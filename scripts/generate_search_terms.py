#!/usr/bin/env python3
"""
generate_search_terms.py
=========================
Read the candidate pipeline's disagreement analysis and produce the grouped
query queue used by the browser reviewer. After review, the same script builds
the normalized query, provenance-bridge, and export-metadata package consumed
by searching_for_DH.

Output is written to:
  datasets/candidate_terms/{term_slug}/search_terms/grouped_translated_terms.csv

Directionality conflicts are embedded in the output CSV as extra columns
(directionality_conflict, ltr_languages, rtl_languages) rather than a
separate file. Open html_files/search_term_reviewer.html to resolve them
interactively before running the search script.

Term-selection logic (by comparison status):
  exact_convergence       → the single agreed-upon term
  near_form_convergence   → terms that appear > 2 times across services,
                            falling back to the most frequent form
  substantive_variation  → all distinct service translations
  insufficient_comparison → every available term

Tier 3 exclusions applied (strictest — search safety):
  • Languages with constructed/undeciphered scripts (zbl, lab, elx, xmr) are dropped.
  • Translation terms marked service='analysis_exclusion' are dropped without
    removing their language rows or unrelated terms.
  • Per-(language, service) pairs flagged by automated term-error review
    signals are removed from service_translations before term selection.
  • Manual exclusions (exclude_translation or any exclude_term_*) are applied.
  • curate_translation() is applied to strip parenthetical romanizations; terms
    reduced to None (placeholder/interleaved noise) are dropped.
  • Source-term leakage is checked and leaking terms are dropped.
  • Terms containing control characters or null bytes are dropped.
  • Terms with no rationale anywhere in the pipeline AND only one cell producing
    them anywhere (i.e., no other cell from any service, variant, or language
    matches the term) are auto-dropped as uncorroborated singletons. Corroboration
    is at the term level — a term that appears in multiple languages, multiple
    services, or both, qualifies even without rationale.

Usage
-----
    python scripts/generate_search_terms.py
    python scripts/generate_search_terms.py --term "Digital Humanities"
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.candidate_generation.translation_versions import load_translation_versions

try:
    from scripts.utils import get_data_directory_path
    from scripts.review.apply_review_filters import load_manual_exclusions
    _DATA_DIR = get_data_directory_path()
except Exception:
    _DATA_DIR = None
    load_manual_exclusions = None

try:
    from scripts.review.translation_classifier import curate_translation, has_source_leakage
    _CLASSIFIER_AVAILABLE = True
except Exception:
    _CLASSIFIER_AVAILABLE = False

# Language codes whose scripts are constructed, undeciphered, or otherwise
# produce unreliable/unsearchable translations (Blissymbols, Linear A,
# Elamite Cuneiform, Meroitic).
CONSTRUCTED_SCRIPT_LANGS = frozenset({"zbl", "lab", "elx", "xmr"})


def _query_id(row: pd.Series) -> str:
    """Return a stable identifier for one reviewed query-language grouping."""
    languages = ", ".join(
        sorted(code.strip() for code in str(row.get("natural_language", "")).split(",") if code.strip())
    )
    payload = "\x1f".join(
        [
            str(row.get("search_term_source", "")),
            str(row.get("search_term", "")),
            languages,
            str(row.get("directionality", "")),
        ]
    )
    return f"cq_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"

# Quality-flag columns that indicate the translated TERM itself is unreliable.
# The paired *_services column lists which service(s) triggered the flag.
_TERM_ERROR_FLAG_COLS: dict[str, str] = {
    "has_mixed_script": "mixed_script_services",
    "has_placeholder_term": "placeholder_term_services",
    "has_repetition_loop": "repetition_loop_services",
    "has_extreme_term_length": "extreme_term_length_services",
    "has_unicode_escape": "unicode_escape_services",
    "has_source_term": "source_term_services",
}

# Characters that would break or poison a GitHub search query.
_UNSAFE_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _load_term_corrections(data_dir: str, term_slug: str) -> dict[tuple[str, str], str]:
    """Return a dict mapping (language_code, original_term) → corrected_term.

    Reads rows from manual_exclusions.csv where service == 'term_correction'.
    """
    me_path = os.path.join(data_dir, "candidate_terms", term_slug, "evaluation", "manual_exclusions.csv")
    corrections: dict[tuple[str, str], str] = {}
    if not os.path.exists(me_path):
        return corrections
    me = pd.read_csv(me_path, converters={'language_code': str})
    if 'corrected_term' not in me.columns or 'original_term' not in me.columns:
        return corrections
    for _, row in me.iterrows():
        if str(row.get('service', '')).strip() != 'term_correction':
            continue
        lang = str(row['language_code']).strip()
        original = str(row.get('original_term', '')).strip()
        corrected = str(row.get('corrected_term', '')).strip()
        if lang and original and corrected and corrected not in ('', 'nan', 'None'):
            corrections[(lang, original)] = corrected
    return corrections


def _build_tier3_drops(data_dir: str, term_slug: str) -> set[tuple[str, str]]:
    """Return a set of (language_code, service_lower) pairs to exclude at Tier 3.

    Sources:
      - automated_review_signals.csv: term-error signals (mixed script,
        placeholder, etc.)
      - manual_exclusions.csv: exclude_translation or any exclude_term_* column
        (rows with service='search_exclusion' are handled separately by
        _build_search_term_drops and are skipped here)
    """
    drops: set[tuple[str, str]] = set()

    qf_path = os.path.join(data_dir, "candidate_terms", term_slug, "evaluation", "automated_review_signals.csv")
    me_path = os.path.join(data_dir, "candidate_terms", term_slug, "evaluation", "manual_exclusions.csv")

    if os.path.exists(qf_path):
        qf = pd.read_csv(qf_path, converters={'language_code': str})
        for _, row in qf.iterrows():
            lang = row["language_code"]
            for flag, svc_col in _TERM_ERROR_FLAG_COLS.items():
                if row.get(flag) and pd.notna(row.get(svc_col, float("nan"))):
                    for svc in str(row[svc_col]).split(";"):
                        svc = svc.strip()
                        if svc:
                            drops.add((lang, svc.lower()))

    if os.path.exists(me_path):
        me = pd.read_csv(me_path, converters={'language_code': str})
        exclude_cols = [
            c for c in me.columns
            if c == "exclude_translation" or c.startswith("exclude_term_")
        ]
        for _, row in me.iterrows():
            if pd.isna(row.get("service")):
                continue
            svc = str(row["service"]).strip().lower()
            if svc in {"search_exclusion", "analysis_exclusion", "term_correction"}:
                continue  # handled by term-level loaders
            lang = str(row["language_code"]).strip()
            if any(row.get(col) is True or row.get(col) == True for col in exclude_cols):
                drops.add((lang, svc))

    return drops


# LLM service / variant inventory for rationale-pairing checks
_LLM_SERVICES_FOR_PAIRING = (
    'claude', 'openai', 'gemini', 'deepseek',
    'llama', 'gemma', 'qwen', 'mistral',
)
_VARIANTS_FOR_PAIRING = ('minimal', 'fluent_speaker', 'github_searcher', 'judge')
_PLACEHOLDER_RATIONALES = frozenset({
    'no rationale provided', 'no rationale', 'n/a', 'none',
    'not applicable', 'no explanation provided', 'no reason provided',
})


def _is_valid_rationale(s) -> bool:
    """A rationale is valid if it's a non-empty string that isn't a placeholder."""
    if not isinstance(s, str) or not s.strip():
        return False
    return s.strip().rstrip('.').lower() not in _PLACEHOLDER_RATIONALES


def _build_corroborated_terms(data_dir: str, term_slug: str) -> set[str]:
    """Return a set of curated term strings (lowercased) that qualify for the
    search corpus by the cross-source corroboration rule:

    A term is kept if EITHER
      (a) at least one cell anywhere in the pipeline produced this term with a
          valid (non-placeholder) rationale — the model explained itself for
          this exact string; OR
      (b) the term was produced by ≥2 distinct cells anywhere (counting any
          combination of LLM-variant cells across any languages and direct
          service cells) — cross-source corroboration.

    Note: corroboration is at the *term level*, not per-(language, term). A term
    that appears in multiple languages or multiple services anywhere in the
    pipeline is considered corroborated, even if each individual (language,
    term) pair on its own is a singleton. This is the more expansive policy:
    the cost asymmetry of dropping a real translation (missing relevant content
    from a language community) is higher than including some questionable terms
    (whose search results can be filtered downstream).

    Terms that fail BOTH conditions are auto-excluded from search.

    Terms are passed through curate_translation() to match what the main loop
    checks after stripping parentheticals, and lowercased (GitHub search is
    case-insensitive).
    """
    cell_count: dict[str, int] = {}
    has_valid_rat: set[str] = set()

    def _key(raw_term) -> str | None:
        if not isinstance(raw_term, str):
            return None
        t = raw_term.strip()
        if not t or t.lower() in ('nan', 'none'):
            return None
        if _CLASSIFIER_AVAILABLE:
            curated, _ = curate_translation(t)
            if curated is None:
                return None
            t = curated
        return t.lower()

    # LLM cells — count occurrences AND track rationale validity
    prompt_dir = os.path.join(data_dir, "candidate_terms", term_slug, "prompt_services")
    for svc in _LLM_SERVICES_FOR_PAIRING:
        for variant in _VARIANTS_FOR_PAIRING:
            path = os.path.join(prompt_dir, f"{svc}_{variant}_translations.csv")
            if not os.path.exists(path):
                continue
            term_col = f"{svc}_translated_term"
            rat_col  = f"{svc}_translation_rationale"
            try:
                df = load_translation_versions(path, mode="latest")
                df = df[['language_code', term_col, rat_col]]
            except (ValueError, KeyError):
                continue
            for _, row in df.iterrows():
                key = _key(row.get(term_col))
                if key is None:
                    continue
                cell_count[key] = cell_count.get(key, 0) + 1
                if _is_valid_rationale(row.get(rat_col)):
                    has_valid_rat.add(key)

    # Direct service cells — count occurrences; no rationales to track
    direct_dir = os.path.join(data_dir, "candidate_terms", term_slug, "direct_services")
    for fname, col in [
        ('gt_translations.csv',        'gt_translated_term'),
        ('enmt_translations.csv',      'enmt_translated_term'),
        ('lingvanex_translations.csv', 'lingvanex_translated_term'),
        ('wikipedia_translations.csv', 'wikipedia_translated_term'),
    ]:
        path = os.path.join(direct_dir, fname)
        if not os.path.exists(path):
            continue
        try:
            df = load_translation_versions(path, mode="latest")
            df = df[['language_code', col]]
        except (ValueError, KeyError):
            continue
        for _, row in df.iterrows():
            key = _key(row.get(col))
            if key is None:
                continue
            cell_count[key] = cell_count.get(key, 0) + 1

    # Corroborated if rationale-paired anywhere OR ≥2 cells anywhere
    return {t for t, n in cell_count.items() if n >= 2 or t in has_valid_rat}


def _build_term_version_ids(
    data_dir: str,
    term_slug: str,
    mode: str = "latest",
) -> dict[tuple[str, str], set[str]]:
    """Map each selected language-term pair to its source observations."""
    version_ids: dict[tuple[str, str], set[str]] = {}
    prompt_dir = os.path.join(data_dir, "candidate_terms", term_slug, "prompt_services")
    direct_dir = os.path.join(data_dir, "candidate_terms", term_slug, "direct_services")
    sources = [
        *(
            (
                os.path.join(prompt_dir, f"{service}_{variant}_translations.csv"),
                f"{service}_translated_term",
            )
            for service in _LLM_SERVICES_FOR_PAIRING
            for variant in _VARIANTS_FOR_PAIRING
        ),
        (os.path.join(direct_dir, "gt_translations.csv"), "gt_translated_term"),
        (os.path.join(direct_dir, "enmt_translations.csv"), "enmt_translated_term"),
        (os.path.join(direct_dir, "lingvanex_translations.csv"), "lingvanex_translated_term"),
        (os.path.join(direct_dir, "wikipedia_translations.csv"), "wikipedia_translated_term"),
    ]
    for path, term_column in sources:
        if not os.path.exists(path):
            continue
        try:
            frame = load_translation_versions(path, mode=mode)
        except (KeyError, ValueError, pd.errors.ParserError):
            continue
        if term_column not in frame.columns:
            continue
        for _, row in frame.iterrows():
            value = row.get(term_column)
            version_id = row.get("transmogrifier_id")
            language_code = str(row.get("language_code", "")).strip()
            if not isinstance(value, str) or not value.strip() or not version_id or not language_code:
                continue
            curated = value.strip()
            if _CLASSIFIER_AVAILABLE:
                curated, _ = curate_translation(curated)
                if curated is None:
                    continue
            key = (language_code, curated.lower())
            version_ids.setdefault(key, set()).add(str(version_id))
    return version_ids


def _build_search_term_drops(data_dir: str, term_slug: str) -> set[tuple[str, str]]:
    """Return a set of (language_code, term_lower) pairs to suppress from search output.

    Reads rows where service == 'search_exclusion' in manual_exclusions.csv.
    These are written by the ✗srch button in review_explorer.html and exclude
    a specific translated term string from grouped_translated_terms.csv without
    removing the (language, service) pair from disagreement analysis.
    """
    drops: set[tuple[str, str]] = set()
    me_path = os.path.join(data_dir, "candidate_terms", term_slug, "evaluation", "manual_exclusions.csv")
    if not os.path.exists(me_path):
        return drops
    me = pd.read_csv(me_path, converters={'language_code': str})
    for _, row in me.iterrows():
        if str(row.get("service", "")).strip().lower() != "search_exclusion":
            continue
        lang = str(row["language_code"]).strip()
        original = str(row.get("original_term", "")).strip().lower()
        if lang and original:
            drops.add((lang, original))
    return drops


def _is_search_unsafe(term: str) -> bool:
    """True if the term contains characters that would corrupt a search query."""
    return bool(_UNSAFE_RE.search(term))


def _select_terms(comparison_status: str, service_translations: dict) -> list[str]:
    """Return the list of search terms to emit for this language row."""
    values = list(service_translations.values())

    if comparison_status == "exact_convergence":
        return [values[0]] if values else []

    if comparison_status == "near_form_convergence":
        counts = Counter(values)
        selected = [term for term, n in counts.items() if n > 2]
        if not selected:
            selected = [counts.most_common(1)[0][0]]
        return selected

    # substantive_variation and insufficient_comparison
    seen: set[str] = set()
    distinct: list[str] = []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            distinct.append(v)
    return distinct


def build_search_terms(
    data_dir: str | None = None,
    term: str = "Digital Humanities",
) -> pd.DataFrame:
    root = data_dir or _DATA_DIR
    if not root:
        sys.exit(
            "Cannot locate pipeline data directory. "
            "Call set_data_directory_path() from scripts/utils.py first."
        )

    term_slug = term.lower().replace(" ", "_")
    disagr_path = os.path.join(root, "candidate_terms", term_slug, "evaluation", "disagreement_analysis.csv")
    lang_path = os.path.join(root, "metadata_files", "language_codes_comprehensive.csv")

    if not os.path.exists(disagr_path):
        sys.exit(f"Missing: {disagr_path}\nRun explore_disagreements.py first.")
    if not os.path.exists(lang_path):
        sys.exit(f"Missing: {lang_path}")

    disagr_df = pd.read_csv(disagr_path, converters={'language_code': str})
    # Drop non-language rows (e.g. Wikipedia navigation artifacts like
    # "see also: test languages at the Wikimedia Incubator")
    disagr_df = disagr_df[~disagr_df["language_code"].str.contains(" ", na=False)]
    # converters preserves 'nan' (Min Nan Chinese, ISO 639-3) as a string
    lang_df = pd.read_csv(lang_path, converters={"language_code": str})[["language_code", "directionality"]]

    # ── Tier 3 exclusion setup ────────────────────────────────────────────────
    tier3_drops = _build_tier3_drops(root, term_slug)
    search_term_drops = _build_search_term_drops(root, term_slug)
    term_corrections = _load_term_corrections(root, term_slug)
    corroborated_terms = _build_corroborated_terms(root, term_slug)

    eval_dir = os.path.join(root, "candidate_terms", term_slug, "evaluation")
    if load_manual_exclusions is not None:
        analysis_terms, _, _ = load_manual_exclusions(eval_dir)
    else:
        analysis_terms = set()

    n_dropped_lang = 0
    n_dropped_analysis = 0
    n_dropped_unpaired = 0
    n_dropped_service = 0
    n_dropped_curate = 0
    n_dropped_leakage = 0
    n_dropped_unsafe = 0
    n_dropped_search_excl = 0

    rows: list[dict] = []
    for _, row in disagr_df.iterrows():
        lang_code = row["language_code"]
        comparison_status = row["comparison_status"]

        # Tier 3: skip constructed/undeciphered script languages entirely
        if lang_code in CONSTRUCTED_SCRIPT_LANGS:
            n_dropped_lang += 1
            continue

        try:
            svc = ast.literal_eval(str(row["service_translations"]))
        except Exception:
            svc = {}

        # Tier 3: remove per-(language, service) pairs with term-error flags
        # or manual exclusions before selecting terms
        filtered_svc: dict[str, str] = {}
        for svc_name, translation in svc.items():
            if (lang_code, svc_name.lower()) in tier3_drops:
                n_dropped_service += 1
                continue
            if isinstance(translation, str) and (lang_code, translation.strip()) in analysis_terms:
                n_dropped_analysis += 1
                continue
            filtered_svc[svc_name] = translation

        # Apply term corrections: replace original translations with user-corrected values
        if term_corrections:
            filtered_svc = {
                svc_name: term_corrections.get((lang_code, t), t)
                for svc_name, t in filtered_svc.items()
            }

        selected = _select_terms(comparison_status, filtered_svc)
        for term_value in selected:
            if not term_value or str(term_value).strip() in ("", "nan", "None"):
                continue
            term_value = str(term_value).strip()

            # Tier 3: apply curate_translation to strip parenthetical
            # romanizations; discard placeholders and interleaved noise
            if _CLASSIFIER_AVAILABLE:
                curated, _ = curate_translation(term_value)
                if curated is None:
                    n_dropped_curate += 1
                    continue
                term_value = curated

            # Tier 3: drop terms that still leak the source term after curation.
            # Skip for English — the English "translation" legitimately IS the source term.
            if _CLASSIFIER_AVAILABLE and lang_code != "en" and has_source_leakage(term_value, term):
                n_dropped_leakage += 1
                continue

            # Tier 3: drop terms with control characters
            if _is_search_unsafe(term_value):
                n_dropped_unsafe += 1
                continue

            # Tier 3: drop terms manually excluded via ✗srch in review_explorer
            if (lang_code, term_value.lower()) in search_term_drops:
                n_dropped_search_excl += 1
                continue

            # Tier 3: drop terms that have neither a rationale nor cross-source
            # corroboration anywhere in the pipeline. A term is kept if EITHER
            # at least one cell anywhere produced it with a valid rationale, OR
            # ≥2 distinct cells anywhere produced it (regardless of language or
            # service). This is the cross-anything corroboration rule — the
            # more expansive policy that preserves cross-language convergence.
            if term_value.lower() not in corroborated_terms:
                n_dropped_unpaired += 1
                continue

            rows.append(
                {
                    "natural_language": lang_code,
                    "search_term": term_value,
                    "search_term_source": term,
                    "comparison_status": comparison_status,
                    "keep_term": True,
                }
            )

    result = pd.DataFrame(rows)

    # ── Case normalisation ────────────────────────────────────────────────────
    # GitHub search is case-insensitive, so "Digital Humanities" and
    # "digital humanities" are identical queries. Lowercase everything so
    # case variants collapse into a single row during deduplication.
    # Non-Latin scripts are unaffected (.lower() is a no-op for them).
    result["search_term"] = result["search_term"].str.lower()

    # Attach directionality
    result = result.merge(lang_df, left_on="natural_language", right_on="language_code", how="left")
    result = result.drop(columns=["language_code"], errors="ignore")
    result["directionality"] = result["directionality"].fillna("ltr")

    # ── Directionality conflict detection ─────────────────────────────────────
    # For each search_term that maps to both LTR and RTL language codes,
    # record which codes are LTR and which are RTL. This is embedded directly
    # in the output CSV so the HTML reviewer can present resolution UI without
    # needing a separate conflicts file.
    dir_per_term = result.groupby("search_term")["directionality"].nunique()
    conflict_terms = set(dir_per_term[dir_per_term > 1].index)

    def _agg_languages(s):
        return ", ".join(sorted(s.unique()))

    def _majority_dir(s):
        return s.mode().iloc[0]

    def _join_categories(s):
        return ", ".join(sorted(s.unique()))

    def _ltr_langs(group):
        return ", ".join(sorted(group.loc[group["directionality"] == "ltr", "natural_language"].unique()))

    def _rtl_langs(group):
        return ", ".join(sorted(group.loc[group["directionality"] == "rtl", "natural_language"].unique()))

    deduped = (
        result
        .groupby("search_term", sort=False)
        .agg(
            natural_language=("natural_language", _agg_languages),
            counts=("natural_language", "nunique"),
            directionality=("directionality", _majority_dir),
            search_term_source=("search_term_source", "first"),
            comparison_status=("comparison_status", _join_categories),
            keep_term=("keep_term", "first"),
        )
        .reset_index()
        .sort_values("counts", ascending=False)
        .reset_index(drop=True)
    )

    # Embed conflict columns
    deduped["directionality_conflict"] = deduped["search_term"].isin(conflict_terms)

    # For conflicted terms, store the per-direction language lists
    if conflict_terms:
        conflict_ltr = (
            result[result["search_term"].isin(conflict_terms)]
            .groupby("search_term")
            .apply(_ltr_langs)
            .rename("ltr_languages")
        )
        conflict_rtl = (
            result[result["search_term"].isin(conflict_terms)]
            .groupby("search_term")
            .apply(_rtl_langs)
            .rename("rtl_languages")
        )
        deduped = deduped.join(conflict_ltr, on="search_term").join(conflict_rtl, on="search_term")
    else:
        deduped["ltr_languages"] = ""
        deduped["rtl_languages"] = ""

    deduped["ltr_languages"] = deduped["ltr_languages"].fillna("")
    deduped["rtl_languages"] = deduped["rtl_languages"].fillna("")
    deduped.insert(0, "query_id", deduped.apply(_query_id, axis=1))

    out_dir = os.path.join(root, "candidate_terms", term_slug, "search_terms")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "grouped_translated_terms.csv")
    deduped.to_csv(out_path, index=False)

    total_langs = result["natural_language"].nunique()
    n_conflicts = len(conflict_terms)
    print(f"Saved {len(deduped)} unique search terms covering {total_langs} languages → {out_path}")
    print(f"  ({len(result)} rows before dedup; {len(result) - len(deduped)} redundant API calls avoided)")
    print(f"\nTier 3 exclusions applied:")
    print(f"  Constructed-script languages dropped : {n_dropped_lang}")
    print(f"  Analysis-excluded translation terms  : {n_dropped_analysis}")
    print(f"  (lang, service) pairs dropped (flags + manual): {n_dropped_service}")
    print(f"  Terms nulled by curate_translation   : {n_dropped_curate}")
    print(f"  Terms dropped for source leakage     : {n_dropped_leakage}")
    print(f"  Terms dropped for unsafe characters  : {n_dropped_unsafe}")
    print(f"  Terms dropped via ✗srch exclusion   : {n_dropped_search_excl}")
    print(f"  Terms dropped as unpaired singletons : {n_dropped_unpaired}")
    if n_conflicts:
        print(f"\n[!] {n_conflicts} term(s) have directionality conflicts — open html_files/search_term_reviewer.html to resolve them.")
    status_counts = result.groupby("comparison_status")["search_term"].count()
    for status, n in status_counts.items():
        print(f"  {status}: {n} terms")

    return deduped


def enrich_reviewed_search_term_provenance(
    data_dir: str | None = None,
    term: str = "Digital Humanities",
) -> pd.DataFrame:
    """Attach candidate-observation provenance to an existing reviewed export."""
    root = data_dir or _DATA_DIR
    if not root:
        raise ValueError("Cannot locate the pipeline datasets directory.")
    term_slug = term.lower().replace(" ", "_")
    path = os.path.join(
        root,
        "candidate_terms",
        term_slug,
        "search_terms",
        "reviewed_grouped_translated_terms.csv",
    )
    reviewed = pd.read_csv(path, converters={"natural_language": str})
    version_ids = _build_term_version_ids(root, term_slug, mode="all_history")

    inline_provenance_columns = {
        "transmogrifier_ids",
        "selection_mode",
        "selection_as_of",
        "candidate_provenance_status",
    }
    reviewed = reviewed.drop(
        columns=[column for column in inline_provenance_columns if column in reviewed],
        errors="ignore",
    )
    if "query_id" not in reviewed.columns:
        reviewed.insert(0, "query_id", reviewed.apply(_query_id, axis=1))
    if reviewed["query_id"].duplicated().any():
        duplicates = reviewed.loc[reviewed["query_id"].duplicated(False), "query_id"].unique()
        raise ValueError(f"Reviewed export contains duplicate query IDs: {duplicates[:5]}")

    links: list[dict[str, str]] = []
    row_statuses: list[str] = []
    for row in reviewed.itertuples(index=False):
        languages = [code.strip() for code in str(row.natural_language).split(",")]
        matched = {
            version_id
            for code in languages
            for version_id in version_ids.get(
                (code, str(row.search_term).strip().lower()), set()
            )
        }
        if matched:
            links.extend(
                {
                    "query_id": row.query_id,
                    "transmogrifier_id": version_id,
                    "provenance_status": "candidate_observation",
                }
                for version_id in sorted(matched)
            )
            row_statuses.append("candidate_observations")
            continue

        payload = "\x1f".join(
            [
                str(row.search_term_source),
                str(row.search_term),
                str(row.natural_language),
                str(row.directionality),
            ]
        )
        legacy_id = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
        links.append(
            {
                "query_id": row.query_id,
                "transmogrifier_id": f"legacy_reviewed_{legacy_id}",
                "provenance_status": "legacy_reviewed_export",
            }
        )
        row_statuses.append("legacy_reviewed_export")

    bridge = pd.DataFrame(links).drop_duplicates().sort_values(
        ["query_id", "transmogrifier_id"]
    )
    bridge_path = os.path.join(os.path.dirname(path), "reviewed_candidate_term_provenance.csv")

    reviewed_bytes = reviewed.to_csv(index=False).encode("utf-8")
    bridge_bytes = bridge.to_csv(index=False).encode("utf-8")
    reviewed_sha256 = hashlib.sha256(reviewed_bytes).hexdigest()
    bridge_sha256 = hashlib.sha256(bridge_bytes).hexdigest()
    export_payload = "\x1f".join(["selected", reviewed_sha256, bridge_sha256])
    term_export_id = f"te_{hashlib.sha256(export_payload.encode('utf-8')).hexdigest()[:24]}"
    metadata = {
        "term_export_id": term_export_id,
        "selection_mode": "selected",
        "selection_as_of": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_query_rows": int(len(reviewed)),
        "provenance_link_rows": int(len(bridge)),
        "candidate_observation_query_rows": row_statuses.count("candidate_observations"),
        "legacy_reviewed_query_rows": row_statuses.count("legacy_reviewed_export"),
        "reviewed_queries_sha256": reviewed_sha256,
        "provenance_bridge_sha256": bridge_sha256,
    }
    metadata_path = os.path.join(
        os.path.dirname(path), "reviewed_candidate_term_export_metadata.json"
    )

    outputs = {
        path: reviewed_bytes,
        bridge_path: bridge_bytes,
        metadata_path: (json.dumps(metadata, indent=2) + "\n").encode("utf-8"),
    }
    for output_path, content in outputs.items():
        temporary_path = f"{output_path}.tmp"
        with open(temporary_path, "wb") as handle:
            handle.write(content)
        os.replace(temporary_path, output_path)
    print(
        f"Enriched {len(reviewed)} reviewed queries: "
        f"{row_statuses.count('candidate_observations')} linked to candidate observations; "
        f"{row_statuses.count('legacy_reviewed_export')} assigned explicit legacy IDs. "
        f"Wrote {len(bridge)} provenance links under export {term_export_id}."
    )
    return reviewed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build grouped_translated_terms.csv from the translation pipeline evaluation outputs."
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Path to the pipeline datasets/ directory (overrides stored apikey)",
    )
    parser.add_argument(
        "--term",
        default="Digital Humanities",
        help="Source term to process (default: 'Digital Humanities')",
    )
    parser.add_argument(
        "--enrich-reviewed",
        action="store_true",
        help="Attach candidate provenance to the existing reviewed search-term export",
    )
    args = parser.parse_args()
    if args.enrich_reviewed:
        enrich_reviewed_search_term_provenance(
            data_dir=args.data_dir, term=args.term
        )
    else:
        build_search_terms(data_dir=args.data_dir, term=args.term)


if __name__ == "__main__":
    main()
