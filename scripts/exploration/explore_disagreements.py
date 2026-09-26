#!/usr/bin/env python3
"""
explore_disagreements.py
========================
Describe translation convergence without inferring why services agree or
disagree. Each language receives one comparison status:

1. exact_convergence: at least two services remain and all produced the same
   trimmed string, ignoring capitalization.
2. near_form_convergence: outputs differ, but collapse under the documented
   normalization or remain within the edit-distance tolerance.
3. substantive_variation: outputs remain distinct beyond that tolerance.
4. insufficient_comparison: fewer than two usable outputs remain.

Wikipedia presence, source-term retention, script disagreement, rationale
signals, and family metadata remain independent evidence columns. They can be
used to interpret patterns, but they do not decide the comparison status.

Data quality
------------
LLMs occasionally return a translation but omit the rationale, or return a
placeholder string such as "No rationale provided" instead of real reasoning.
Both cases are treated as missing rationales:

  - ``load_variant_df`` (explore_confidence_within_variant.py) nulls out any
    translation whose rationale is absent or a placeholder, and vice versa.
    This pairing is enforced before any notebook or script sees the data.
  - Within this script, the same ``is_placeholder_rationale`` check is applied
    a second time when building the per-language rationale dict from the variant
    DataFrame index.
  - After both dicts are built, any LLM service that still has a translation
    but no rationale in the loaded variant is dropped from the ``translations``
    dict, so its output does not influence the classifier or rationale-similarity
    score.

Input
-----
  - translated_terms/{term}/evaluation/across_variant_detail.csv
    (produced by explore_confidence_across_variants.py)
  - translated_terms/{term}/{direct,prompt}_services/*.csv
    loaded via load_variant_df for a single reference variant's rationales

Output
------
  translated_terms/{term}/evaluation/disagreement_analysis.csv
    One row per (language_code × term_source) with:
      - comparison_status, comparison_basis
      - classifier feature columns (unique counts, edit distance, script info,
        loan words, signal counts)
      - mean_rationale_similarity (surface lexical, not semantic — see docs)
      - first 300 chars of each service's rationale for inspection

Usage
-----
    python explore_disagreements.py

    # Single term, non-default variant
    python explore_disagreements.py --term "Digital Humanities" --variant github_searcher

    # Override source tokens for a different term
    python explore_disagreements.py --source-tokens digital humanities dh
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rich.console import Console
from rich.table import Table

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.utils import (
    get_data_directory_path, read_csv_file,
    detect_script_disagreement,
    is_placeholder_rationale,
    get_language_family,
    load_manual_exclusions,
)
from scripts.exploration.explore_confidence_within_variant import load_variant_df

console = Console()


# ── Constants ──────────────────────────────────────────────────────────────

COMPARISON_STATUSES = {
    'exact_convergence': 'All usable service outputs match after trimming and case-folding',
    'near_form_convergence': 'Differences collapse under normalization or edit-distance tolerance',
    'substantive_variation': 'Differences remain beyond the near-form tolerance',
    'insufficient_comparison': 'Fewer than two usable service outputs remain',
}

# Which prompt variants produce English-language rationales. Keyword matching assumes English; fluent_speaker produces rationales in the target language and keyword rules are skipped for it.
ENGLISH_RATIONALE_VARIANTS = {'minimal', 'github_searcher', 'judge'}
NATIVE_RATIONALE_VARIANTS = {'fluent_speaker'}

RATIONALE_COLS = {
    'Claude':   'claude_translation_rationale',
    'OpenAI':   'openai_translation_rationale',
    'Gemini':   'gemini_translation_rationale',
    'DeepSeek': 'deepseek_translation_rationale',
    'Llama':    'llama_translation_rationale',
    'Gemma':    'gemma_translation_rationale',
    'Qwen':     'qwen_translation_rationale',
    'Mistral':  'mistral_translation_rationale',
}

TRANSLATION_COLS = {
    'Wikipedia':        'wikipedia_translated_term',
    'Google Translate': 'gt_translated_term',
    'EasyNMT':          'enmt_translated_term',
    'Lingvanex':        'lingvanex_translated_term',
    'OpenAI':           'openai_translated_term',
    'Claude':           'claude_translated_term',
    'Gemini':           'gemini_translated_term',
    'DeepSeek':         'deepseek_translated_term',
    'Llama':            'llama_translated_term',
    'Gemma':            'gemma_translated_term',
    'Qwen':             'qwen_translated_term',
    'Mistral':          'mistral_translated_term',
}


# Rationale keywords signaling the model knows no equivalent exists. Literal-word patterns use \b word boundaries so "overborrowed" or "colloquialism" don't accidentally match "borrow" or "anglicism".
ABSENCE_KEYWORDS = [
    'no equivalent', 'no direct', 'no established', 'no widely', 'not adopted',
    'not institutionalized', 'not institutionalised', 'not yet adopted',
    'does not exist', "hasn't been", 'have not been', 'has not been',
    'no community', 'no scholarly', 'not used in', 'concept does not',
    'term does not', 'no translation', 'untranslated', 'no native',
    'no recognized', 'no recognised',
    r'\bborrowed\b', r'\bloanword\b', r'\bloan word\b',
    r'\bborrowing\b', r'\banglicism\b', r'\banglicization\b', r'\banglicised\b',
    r'\btransliterat', r'keep.*english', r'retain.*english',
]

# Rationale keywords suggesting elaborate construction as a transmogrification signal. Currently recorded in the output CSV but not used by any rule in the chain; retained because the signal is potentially useful for downstream analysis.
CONSTRUCTION_KEYWORDS = [
    'etymolog', 'root word', 'compound', 'combining', 'derive from',
    'ancient', 'classical', 'proto-', 'reconstructed', 'neologism',
    'coined', 'coining', 'create.*term', 'construct', 'formation',
    'morpholog', 'word-forming', 'suffix', 'prefix',
]

# Rationale keywords suggesting community debate as a productive disagreement signal. Also recorded but not used by any rule (Wikipedia presence does the work).
DEBATE_KEYWORDS = [
    'some scholars', 'different communities', 'preferred by', 'others use',
    'alternatively', 'debate', 'contested', 'competing', 'variant',
    'both terms', 'either', 'also used', 'sometimes rendered',
]

def derive_source_tokens(term: str) -> List[str]:
    """Derive loanword-detection tokens from the source term itself.

    Three forms, in order:
      1. Full lowercased term          — catches exact phrase borrowing
      2. Individual words              — catches per-word borrowing
      3. Initial-letter acronym        — catches abbreviated forms (e.g. 'dh')

    This replaces manual curation: tokens emerge from the term itself so no
    domain knowledge is required when adding a new source term.
    
    Parameters
    ----------
    term : str
		The source term, e.g. "Digital Humanities". Should be in English or
		Latin script for the tokenization to work well; non-Latin scripts are
		not guaranteed to split into meaningful tokens but will still be
		included as-is in the output list so the loan-word rule can still fire
		on exact matches.
        
    Returns
    -------
    List[str]
		A list of tokens derived from the term, e.g. ["digital humanities", "digital", "humanities", "dh"].
    """
    term_lower = term.lower().strip()
    words = [w for w in re.split(r'\s+', term_lower) if w]
    tokens = [term_lower] + words
    if len(words) > 1:
        tokens.append(''.join(w[0] for w in words))
    seen: set = set()
    out: List[str] = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


# ── String normalization ───────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Lowercase, strip diacritics, remove punctuation, collapse whitespace.

    RTL scripts (Arabic, Hebrew) are handled correctly: Python's \\w is
    Unicode-aware so Arabic/Hebrew letters are preserved by the punctuation
    strip, and NFKD decomposition correctly normalises Arabic compatibility
    forms. The only combining characters removed are vowel-pointing marks
    (harakat, niqqud) which is a loss but necessary to avoid counting diacritic variation as disagreement. Though we do count it as disagreement at the raw level, so the edit-distance-based rules can still detect it as a measurement artefact when the underlying term is the same.
    """
    if not text or not isinstance(text, str):
        return ''
    nfkd = unicodedata.normalize('NFKD', text.lower())
    no_combining = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', no_combining)).strip()


def edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance. Returns 0 for identical strings, 1 for one insertion/deletion/substitution, etc."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = prev if a[i - 1] == b[j - 1] else 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def max_pairwise_edit_distance(strings: List[str]) -> int:
    """Max edit distance among all pairs in a list of strings."""
    if len(strings) <= 1:
        return 0
    return max(
        edit_distance(a, b)
        for i, a in enumerate(strings)
        for b in strings[i + 1:]
    )


def find_loan_words(text: str, source_tokens: List[str]) -> List[str]:
    """Return the subset of source_tokens present as whole words in text.

    Uses whole-word matching (post-normalization) so adapted inflections like 'digitala' (Gothic inflection of 'digital') are not flagged but instead only unadapted borrowings like 'digital' or 'humanities' as standalone words.
    """
    if not text:
        return []
    words = set(normalize(text).split())
    return [tok for tok in source_tokens if tok in words]


# ── Rationale similarity (surface metric) ─────────────────────────────────

def compute_rationale_similarity(
    rationales: Dict[str, Optional[str]],
) -> Optional[float]:
    """Mean pairwise TF-IDF cosine similarity across service rationales.

    Uses character n-grams (3–5) so the metric is script-agnostic. This is a SURFACE metric: it measures how similarly two rationales are *phrased*, not whether they convey the same meaning. High similarity can arise from shared topic vocabulary even when the underlying claims differ. This similarity therefore is lexical convergence, not semantic agreement.

    Returns None when fewer than 2 non-empty rationales are available.
    """
    texts = [
        t for t in rationales.values()
        if t and isinstance(t, str) and t.strip() and t not in ('nan', 'None')
    ]
    if len(texts) < 2:
        return None
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        vec = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=1)
        tfidf = vec.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf)
        n = len(texts)
        upper = [sim_matrix[i, j] for i in range(n) for j in range(i + 1, n)]
        return round(float(np.mean(upper)), 4) if upper else None
    except Exception:
        return None


# ── Rationale keyword matching ─────────────────────────────────────────────

def match_keywords(text: str, keywords: List[str]) -> List[str]:
    """Return which keyword patterns (as regex) match in text."""
    if not text or not isinstance(text, str):
        return []
    text_lower = text.lower()
    return [kw for kw in keywords if re.search(kw, text_lower)]


def extract_rationale_signals(
    rationales: Dict[str, Optional[str]],
) -> Dict[str, List[Tuple[str, str]]]:
    """Scan all service rationales for absence / construction / debate keywords.

    Returns dict with keys 'absence', 'construction', 'debate', each a list
    of (service, keyword) tuples matched.
    """
    signals: Dict[str, List[Tuple[str, str]]] = {
        'absence': [], 'construction': [], 'debate': [],
    }
    for service, text in rationales.items():
        if not text:
            continue
        for kw in match_keywords(text, ABSENCE_KEYWORDS):
            signals['absence'].append((service, kw))
        for kw in match_keywords(text, CONSTRUCTION_KEYWORDS):
            signals['construction'].append((service, kw))
        for kw in match_keywords(text, DEBATE_KEYWORDS):
            signals['debate'].append((service, kw))
    return signals


# ── Features + rules ──────────────────────────────────────────────────────

@dataclass
class ClassifierConfig:
    """Tunable knobs for comparison and evidence extraction."""
    norm_threshold: float = 0.15
    source_tokens: Optional[Tuple[str, ...]] = None  # None = derive from term at runtime


@dataclass
class Features:
    """All features a rule might read, computed once per (language × term).

    This is a plain data record of the rules read fields but it never mutates them. Keeps the rule functions short and makes it easy to add new rules without re-deriving features inside each one.
    
    The features are all derived from the raw translation outputs and rationales, plus Wikipedia presence as external metadata. The rationale-based features are gated on `rationales_are_english` because the keyword matching only works for English rationales; when False, the rationale fields are still populated in the output CSV for inspection but the keyword-rule functions are no-ops.
    """
    translations: Dict[str, str]
    rationales: Dict[str, str]
    has_wikipedia: bool
    rationales_are_english: bool
    n_unique_raw: int
    n_unique_normalized: int
    max_edit_distance: int
    dist_threshold: int
    script_info: Dict
    loan_words_found: List[str]
    source_retention_services: List[str]
    signals: Dict[str, List[Tuple[str, str]]]


def extract_features(
    translations: Dict[str, Optional[str]],
    rationales: Dict[str, Optional[str]],
    has_wikipedia: bool,
    rationales_are_english: bool,
    config: ClassifierConfig,
) -> Features:
    """Compute all classifier features in one pass. See Features for fields."""
    valid = {
        s: t.strip() for s, t in translations.items()
        if t and isinstance(t, str) and t.strip() and t not in ('nan', 'None')
    }
    valid_rationales = {
        s: t.strip() for s, t in rationales.items()
        if t and isinstance(t, str) and t.strip() and t not in ('nan', 'None')
    } if rationales_are_english else {}

    raw_vals = list(valid.values())
    unique_raw = set(v.strip().lower() for v in raw_vals)
    norm_vals = [normalize(v) for v in raw_vals]
    unique_norm = set(v for v in norm_vals if v)
    norm_list = list(unique_norm)
    max_dist = max_pairwise_edit_distance(norm_list)
    mean_len = (
        sum(len(v) for v in norm_list) / len(norm_list) if norm_list else 1
    )
    dist_threshold = max(2, int(config.norm_threshold * mean_len))

    script_info = detect_script_disagreement(valid)

    # Source retention: tokens and services remain independent evidence.
    loan_set: set = set()
    source_retention_services: List[str] = []
    for service, text in valid.items():
        retained = find_loan_words(text, list(config.source_tokens))
        if retained:
            source_retention_services.append(service)
            loan_set.update(retained)
    loan_words_found = sorted(loan_set)

    # Keyword signals — only extract when rationales are English
    if rationales_are_english:
        signals = extract_rationale_signals(valid_rationales)
    else:
        signals = {'absence': [], 'construction': [], 'debate': []}

    return Features(
        translations=valid,
        rationales=valid_rationales,
        has_wikipedia=has_wikipedia,
        rationales_are_english=rationales_are_english,
        n_unique_raw=len(unique_raw),
        n_unique_normalized=len(unique_norm),
        max_edit_distance=max_dist,
        dist_threshold=dist_threshold,
        script_info=script_info,
        loan_words_found=loan_words_found,
        source_retention_services=sorted(source_retention_services),
        signals=signals,
    )


def classify_comparison(features: Features) -> Tuple[str, str]:
    """Return a descriptive status and the string rule supporting it."""
    if len(features.translations) < 2:
        return (
            'insufficient_comparison',
            f'{len(features.translations)} usable service output(s)',
        )
    if features.n_unique_raw == 1:
        return ('exact_convergence', 'All usable outputs match after trim/case-fold')
    if features.n_unique_normalized <= 1:
        return (
            'near_form_convergence',
            'Distinct raw strings collapse under Unicode/diacritic/punctuation normalization',
        )
    if features.max_edit_distance <= features.dist_threshold:
        return (
            'near_form_convergence',
            f'Max normalized edit distance {features.max_edit_distance} <= threshold '
            f'{features.dist_threshold}',
        )
    return (
        'substantive_variation',
        f'Max normalized edit distance {features.max_edit_distance} > threshold '
        f'{features.dist_threshold}',
    )


# ── Main pipeline ──────────────────────────────────────────────────────────

_RATIONALE_VARIANT_KEYS = [
    'rationale_minimal',
    'rationale_fluent_speaker',
    'rationale_github_searcher',
    'rationale_judge',
]

_TERM_VARIANT_KEYS = [
    'term_minimal',
    'term_fluent_speaker',
    'term_github_searcher',
    'term_judge',
]


def load_exclusions(path: str) -> Dict[str, Dict[str, Dict[str, bool]]]:
    """Load manual_exclusions.csv into a nested dict.

    Returns ``{language_code: {service: {term: bool, rationale_minimal: bool, ...}}}``.
    The file is produced by html_files/review_explorer.html.
    Per-variant rationale keys: rationale_minimal, rationale_fluent_speaker,
    rationale_github_searcher, rationale_judge.
    """
    df = pd.read_csv(path, converters={'language_code': str})
    result: Dict[str, Dict[str, Dict[str, bool]]] = {}
    for _, row in df.iterrows():
        code = str(row.get('language_code', '')).strip()
        svc  = str(row.get('service', '')).strip()
        if not code or not svc:
            continue
        if svc in {'analysis_exclusion', 'search_exclusion', 'term_correction'}:
            continue
        if code not in result:
            result[code] = {}
        entry: Dict[str, bool] = {
            'term': str(row.get('exclude_translation', 'False')).strip().lower() == 'true',
        }
        for vkey in _TERM_VARIANT_KEYS:
            col = f'exclude_{vkey}'
            entry[vkey] = str(row.get(col, 'False')).strip().lower() == 'true'
        # Auto-promote: if all per-variant terms are excluded, treat as full exclusion
        if not entry['term'] and all(entry.get(k, False) for k in _TERM_VARIANT_KEYS):
            entry['term'] = True
        for vkey in _RATIONALE_VARIANT_KEYS:
            col = f'exclude_{vkey}'
            entry[vkey] = str(row.get(col, 'False')).strip().lower() == 'true'
        result[code][svc] = entry
    n_langs = len(result)
    n_entries = sum(len(v) for v in result.values())
    console.print(
        f"  Loaded {n_entries} exclusion entries across {n_langs} languages from {path}",
        style="dim cyan",
    )
    return result


def load_term_corrections(path: str) -> Dict[str, Dict[str, str]]:
    """Load term corrections from manual_exclusions.csv.

    Returns ``{language_code: {original_term: corrected_term}}`` for rows
    where ``service == 'term_correction'``.
    """
    df = pd.read_csv(path, converters={'language_code': str})
    result: Dict[str, Dict[str, str]] = {}
    if 'corrected_term' not in df.columns or 'original_term' not in df.columns:
        return result
    for _, row in df.iterrows():
        if str(row.get('service', '')).strip() != 'term_correction':
            continue
        code = str(row.get('language_code', '')).strip()
        original = str(row.get('original_term', '')).strip()
        corrected = str(row.get('corrected_term', '')).strip()
        if code and original and corrected and corrected not in ('', 'nan', 'None'):
            if code not in result:
                result[code] = {}
            result[code][original] = corrected
    n_corrections = sum(len(v) for v in result.values())
    if n_corrections:
        console.print(
            f"  Loaded {n_corrections} term correction(s) across {len(result)} language(s) from {path}",
            style="dim cyan",
        )
    return result


def run_disagreement_analysis(
    data_directory_path: str,
    target_terms: List[str],
    rationale_variant: str = 'minimal',
    config: Optional[ClassifierConfig] = None,
    output_dir: Optional[str] = None,
    exclusions: Optional[Dict[str, Dict[str, Dict[str, bool]]]] = None,
    analysis_terms: Optional[set[tuple[str, str]]] = None,
    corrections: Optional[Dict[str, Dict[str, str]]] = None,
) -> pd.DataFrame:
    """Describe convergence for every (language × term) comparison.

    Parameters
    ----------
    data_directory_path : str
        Root data directory.
    target_terms : list of str
        Each term needs an across_variant_detail.csv from
        explore_confidence_across_variants.py.
    rationale_variant : str
        Which prompt variant to source rationales from. 'minimal' is the
        canonical choice. Rationale signals are retained as evidence and never
        determine comparison status.
    config : ClassifierConfig, optional
        Comparison knobs (edit-distance threshold and source tokens).
    corrections : dict, optional
        Term corrections from load_term_corrections(). Maps
        {language_code: {original_term: corrected_term}}. Applied after
        exclusions, replacing matched translation strings before classification.
    analysis_terms : set of (language_code, term), optional
        Translation clusters manually excluded from analysis. Matching strings
        are removed without dropping other translations for the language.
    output_dir : str, optional
        Defaults to translated_terms/{first_term}/evaluation/.

    Returns
    -------
    pd.DataFrame with one row per (language_code × term_source).
    """
    cfg = config or ClassifierConfig()

    if rationale_variant in NATIVE_RATIONALE_VARIANTS:
        console.print(
            "Running with fluent_speaker rationales. English keyword evidence "
            "will be empty; comparison status remains string-based.",
            style="dim cyan",
        )
        rationales_are_english = False
    elif rationale_variant in ENGLISH_RATIONALE_VARIANTS:
        if rationale_variant == 'judge':
            console.print(
                "⚠ Using 'judge' variant: its rationales are synthesis text "
                "across other variants, not independent model reasoning. "
                "Keyword evidence may conflate meta-level and object-level "
                "claims. Consider 'minimal' for the canonical evidence layer.",
                style="bold yellow",
            )
        rationales_are_english = True
    else:
        raise ValueError(
            f"Unknown rationale_variant: {rationale_variant!r}. "
            f"Expected one of {ENGLISH_RATIONALE_VARIANTS | NATIVE_RATIONALE_VARIANTS}."
        )

    console.print(f"\n[bold]Comparison configuration[/bold]")
    console.print(f"  rationale_variant        = {rationale_variant}")
    console.print(f"  rationales_are_english   = {rationales_are_english}")
    console.print(f"  norm_threshold           = {cfg.norm_threshold}")
    console.print(f"  source_tokens            = {'(derived from term)' if cfg.source_tokens is None else list(cfg.source_tokens)}")

    all_rows: List[Dict] = []

    for term in target_terms:
        term_slug = term.lower().replace(' ', '_')
        console.print(f"\n[bold cyan]Analyzing disagreements: {term}[/bold cyan]")
        term_tokens = cfg.source_tokens if cfg.source_tokens is not None else tuple(derive_source_tokens(term))
        cfg_term = replace(cfg, source_tokens=term_tokens)
        console.print(f"  source_tokens: {list(term_tokens)}")

        eval_dir = os.path.join(
            data_directory_path, 'translated_terms', term_slug, 'evaluation',
        )
        detail_path = os.path.join(eval_dir, 'across_variant_detail.csv')
        if not os.path.exists(detail_path):
            console.print(
                f"  ⚠ {detail_path} not found — run "
                "explore_confidence_across_variants.py first",
                style="bold yellow",
            )
            continue

        detail_df = read_csv_file(detail_path)
        detail_df = detail_df[detail_df['term_source'] == term]

        variant_df = load_variant_df(data_directory_path, term_slug, rationale_variant)
        if variant_df is None:
            console.print(
                f"  ⚠ Could not load '{rationale_variant}' variant data; "
                "rationales will be empty",
                style="bold yellow",
            )
            variant_df = pd.DataFrame()

        console.print(
            f"  detail rows: {len(detail_df)} | variant rows: {len(variant_df)}",
        )
        if not variant_df.empty:
            variant_df = variant_df.set_index(['language_code', 'term_source'])

        for (lang_code, term_source), grp in detail_df.groupby(
            ['language_code', 'term_source'],
            dropna=False,
        ):
            lang_name = grp['language_name'].iloc[0]
            lang_family = get_language_family(str(lang_code))

            translations: Dict[str, Optional[str]] = {}
            for _, srow in grp.iterrows():
                candidate = srow.get('best_candidate')
                translations[srow['service']] = (
                    str(candidate) if pd.notna(candidate) else None
                )

            if analysis_terms:
                translations = {
                    service: candidate
                    for service, candidate in translations.items()
                    if not (
                        isinstance(candidate, str)
                        and (str(lang_code), candidate.strip()) in analysis_terms
                    )
                }

            # Apply manual exclusions from html_files/review_explorer.html
            if exclusions:
                lang_excl = exclusions.get(lang_code, {})
                translations = {
                    s: t for s, t in translations.items()
                    if not lang_excl.get(s, {}).get('term', False)
                }

            # Apply term corrections: replace original translation strings with
            # user-corrected values before classification
            if corrections:
                lang_corr = corrections.get(lang_code, {})
                if lang_corr:
                    translations = {
                        s: (lang_corr[t] if t and t in lang_corr else t)
                        for s, t in translations.items()
                    }

            has_wikipedia = bool(translations.get('Wikipedia'))

            rationales: Dict[str, Optional[str]] = {}
            if not variant_df.empty:
                key = (lang_code, term_source)
                if key in variant_df.index:
                    vrow = variant_df.loc[key]
                    if isinstance(vrow, pd.DataFrame):
                        vrow = vrow.iloc[0]
                    for service, col in RATIONALE_COLS.items():
                        val = vrow.get(col) if col in vrow.index else None
                        if pd.notna(val) and not is_placeholder_rationale(str(val)):
                            rationales[service] = str(val)
                        else:
                            rationales[service] = None

            if exclusions:
                lang_excl = exclusions.get(lang_code, {})
                variant_key = f'rationale_{rationale_variant}'
                rationales = {
                    s: r for s, r in rationales.items()
                    if not lang_excl.get(s, {}).get(variant_key, False)
                }

            # Drop LLM translations that have no rationale in this variant.
            # Arises when across_variant_detail pulled a translation from a
            # different variant file than the one loaded for rationales.
            _LLM_SVCS = set(RATIONALE_COLS)
            translations = {
                s: t for s, t in translations.items()
                if s not in _LLM_SVCS or rationales.get(s) is not None
            }

            features = extract_features(
                translations=translations,
                rationales=rationales,
                has_wikipedia=has_wikipedia,
                rationales_are_english=rationales_are_english,
                config=cfg_term,
            )
            comparison_status, comparison_basis = classify_comparison(features)
            similarity = compute_rationale_similarity(rationales)

            row: Dict = {
                'language_code': lang_code,
                'language_name': lang_name,
                'language_family': lang_family,
                'term_source': term_source,
                'comparison_status': comparison_status,
                'comparison_basis': comparison_basis,
                'has_wikipedia': has_wikipedia,
                'rationales_are_english': rationales_are_english,
                'n_services_with_translation': len(features.translations),
                'n_services_with_rationale': len(features.rationales),
                'n_unique_raw': features.n_unique_raw,
                'n_unique_normalized': features.n_unique_normalized,
                'max_edit_distance': features.max_edit_distance,
                'distance_threshold': features.dist_threshold,
                'source_retention_service_count': len(features.source_retention_services),
                'source_retention_services': '; '.join(features.source_retention_services),
                'source_retention_tokens': '; '.join(features.loan_words_found),
                'has_script_disagreement': features.script_info.get(
                    'has_script_disagreement', False,
                ),
                'scripts_found': '; '.join(features.script_info.get('scripts_found', [])),
                'absence_signals': '; '.join(
                    f"{s}:{kw}" for s, kw in features.signals['absence']
                ),
                'construction_signals': '; '.join(
                    f"{s}:{kw}" for s, kw in features.signals['construction']
                ),
                'debate_signals': '; '.join(
                    f"{s}:{kw}" for s, kw in features.signals['debate']
                ),
                'mean_rationale_similarity': similarity,
            }
            for service in ('Claude', 'OpenAI', 'Gemini', 'Ollama'):
                text = features.rationales.get(service, '')
                row[f'{service.lower()}_rationale_snippet'] = text[:300] if text else ''

            row['service_translations'] = str(features.translations)
            all_rows.append(row)

    if not all_rows:
        console.print("⚠ No rows to classify.", style="bold red")
        return pd.DataFrame()

    result_df = pd.DataFrame(all_rows)
    _print_summary(result_df)

    _dir = output_dir or os.path.join(
        data_directory_path, 'translated_terms',
        target_terms[0].lower().replace(' ', '_'), 'evaluation',
    )
    os.makedirs(_dir, exist_ok=True)

    out_path = os.path.join(_dir, 'disagreement_analysis.csv')
    result_df.to_csv(out_path, index=False)
    console.print(f"\n[bold green]✓ Wrote {len(result_df)} rows → {out_path}[/bold green]")

    return result_df


def _print_summary(df: pd.DataFrame) -> None:
    """Print comparison-status counts and family breakdown."""
    status_counts = df['comparison_status'].value_counts()
    total = len(df)

    status_table = Table(title="Translation Comparison Summary", show_header=True)
    status_table.add_column("Status", style="cyan")
    status_table.add_column("Count", style="white")
    status_table.add_column("Pct", style="white")
    status_table.add_column("Description", style="dim")
    for status, count in status_counts.items():
        status_table.add_row(
            status, str(count), f"{count / total * 100:.1f}%",
            COMPARISON_STATUSES.get(status, ''),
        )
    console.print(status_table)

    family_counts = (
        df.groupby(['language_family', 'comparison_status'])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    if not family_counts.empty:
        console.print("\n[bold]Comparison status × Language Family[/bold]")
        console.print(family_counts.to_string(index=False))


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Measure exact, near-form, and substantive translation variation.",
    )
    parser.add_argument(
        '--term', nargs='+', default=['Digital Humanities'],
    )
    parser.add_argument(
        '--variant', default='minimal',
        choices=sorted(ENGLISH_RATIONALE_VARIANTS | NATIVE_RATIONALE_VARIANTS),
        help=(
            "Prompt variant for rationale extraction. 'minimal' is canonical; "
            "'fluent_speaker' has non-English rationale evidence; 'judge' warns."
        ),
    )
    parser.add_argument(
        '--threshold', type=float, default=0.15,
        help='Edit-distance tolerance as fraction of mean length (default 0.15)',
    )
    parser.add_argument(
        '--source-tokens', nargs='+', default=None,
        help=(
            'Override source-language loanword tokens. Defaults to the Digital '
            'Humanities curated list.'
        ),
    )
    parser.add_argument('--output-dir', default=None)
    parser.add_argument(
        '--exclusions', default=None, metavar='PATH',
        help=(
            'Path to manual_exclusions.csv produced by html_files/review_explorer.html. '
            'Rows specify per-language, per-service translations and/or rationales to remove '
            'before the classifier runs — use this to fix bad translations (e.g. "To be '
            'determined") without editing source data.'
        ),
    )
    args = parser.parse_args()

    source_tokens = (
        tuple(args.source_tokens) if args.source_tokens is not None
        else None  # derive from term at runtime
    )
    cfg = ClassifierConfig(
        norm_threshold=args.threshold,
        source_tokens=source_tokens,
    )

    excl = load_exclusions(args.exclusions) if args.exclusions else None
    corr = load_term_corrections(args.exclusions) if args.exclusions else None
    analysis_terms = (
        load_manual_exclusions(os.path.dirname(args.exclusions))[0]
        if args.exclusions else None
    )

    data_dir = get_data_directory_path()
    run_disagreement_analysis(
        data_directory_path=data_dir,
        target_terms=args.term,
        rationale_variant=args.variant,
        config=cfg,
        output_dir=args.output_dir,
        exclusions=excl,
        analysis_terms=analysis_terms,
        corrections=corr,
    )


if __name__ == '__main__':
    main()
