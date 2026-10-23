"""Apply reviewed exclusions and translation-rationale integrity rules."""

from __future__ import annotations

import os
from typing import List, Tuple

import pandas as pd

# ── Exclusion tiers ───────────────────────────────────────────────────────────
#
# Two sources feed filter_for_analysis():
#
# 1. automated_review_signals.csv (automated)
#    Produced by notebook 02.  Signals with an unambiguous interpretation are
#    applied automatically — you don't need to Xall every repetition loop.
#
#    likely_error (nulled in 'quality' and 'search_ready'):
#      has_repetition_loop, has_mixed_script, has_placeholder_term,
#      has_unicode_escape, has_extreme_term_length
#
#    likely_search_complication (nulled in 'search_ready' only):
#      has_romanization, has_source_term (non-English), has_short_translation
#
#    NOT auto-excluded (analytical signal, not errors):
#      has_script_disagreement, has_any_mixing, has_missing_rationale
#
# 2. manual_exclusions.csv (human review via review_explorer.html)
#    Supplements and overrides the automated flags for edge cases.
#    Xall  → likely_error               (exclude_translation = True)
#    Xsrch → likely_search_complication (per-variant boolean flags only)
#
# Analysis modes
# --------------
#   'full'         – no filtering  (error rates, coverage stats)
#   'quality'      – null likely_error cells  (model quality comparison)
#   'search_ready' – null both tiers  (building the translation resource)

_SVC_TO_PREFIX = {
    "Claude":           "claude",
    "OpenAI":           "openai",
    "Gemini":           "gemini",
    "DeepSeek":         "deepseek",
    "Llama":            "llama",
    "Gemma":            "gemma",
    "Qwen":             "qwen",
    "Mistral":          "mistral",
    "Google Translate": "gt",
    "EasyNMT":          "enmt",
    "Lingvanex":        "lingvanex",
    "Wikipedia":        "wikipedia",
}

_VARIANT_COL_TO_NAME = {
    "exclude_term_minimal":          "minimal",
    "exclude_term_fluent_speaker":   "fluent_speaker",
    "exclude_term_github_searcher":  "github_searcher",
    "exclude_term_judge":            "judge",
}


def load_exclusion_tiers(term: str, data_dir: str) -> pd.DataFrame:
	"""Return a DataFrame with columns (language_code, service, tier) where
	tier is 'likely_error', 'likely_search_complication', or 'keep'.

	Reads manual_exclusions.csv written by the review tool; returns an empty
	DataFrame if the file does not exist yet.
	"""
	path = os.path.join(
		data_dir, "translated_terms",
		term.lower().replace(" ", "_"),
		"evaluation", "manual_exclusions.csv",
	)
	if not os.path.exists(path):
		return pd.DataFrame(columns=["language_code", "service", "tier"])

	ex = pd.read_csv(path, converters={"language_code": str})
	variant_cols = list(_VARIANT_COL_TO_NAME.keys())

	rows = []
	for _, r in ex.iterrows():
		if r.get("exclude_translation") is True or r.get("exclude_translation") == True:
			tier = "likely_error"
		elif any(r.get(c) for c in variant_cols):
			tier = "likely_search_complication"
		else:
			tier = "keep"
		rows.append({
			"language_code": r["language_code"],
			"service":       r["service"],
			"tier":          tier,
			# preserve per-variant detail for search_ready nulling
			**{_VARIANT_COL_TO_NAME[c]: bool(r.get(c, False)) for c in variant_cols},
		})

	return pd.DataFrame(rows)


def filter_for_analysis(df: pd.DataFrame, term: str, data_dir: str, mode: str) -> pd.DataFrame:
	"""Return a copy of df with excluded cells nulled according to mode.

	Works on wide-format DataFrames (one row per language × prompt_variant)
	as produced by load_all_variants().  Translation columns are nulled in
	place; no rows are dropped, so error-rate denominators stay correct.

	Parameters
	----------
	df       : the wide-format DataFrame from all_dfs[term]
	term     : source term string, e.g. "Digital Humanities"
	data_dir : DATA_DIR from the notebook
	mode     : 'full' | 'quality' | 'search_ready'
	"""
	if mode == "full":
		return df.copy()

	tiers = load_exclusion_tiers(term, data_dir)
	if tiers.empty:
		return df.copy()

	out = df.copy()

	for _, r in tiers.iterrows():
		lc      = r["language_code"]
		prefix  = _SVC_TO_PREFIX.get(r["service"])
		if prefix is None:
			continue
		col = f"{prefix}_translated_term"
		if col not in out.columns:
			continue

		lang_mask = out["language_code"] == lc

		if r["tier"] == "likely_error":
			# null this service for ALL variants of this language
			out.loc[lang_mask, col] = None

		elif r["tier"] == "likely_search_complication" and mode == "search_ready":
			# null only the specific variants flagged by the reviewer
			for variant_name in _VARIANT_COL_TO_NAME.values():
				if r.get(variant_name):
					variant_mask = lang_mask & (out["prompt_variant"] == variant_name)
					out.loc[variant_mask, col] = None

	return out


_PLACEHOLDER_RATIONALE_STEMS = frozenset({
    'no rationale provided',
    'no rationale',
    'n/a',
    'none',
    'not applicable',
    'no explanation provided',
    'no reason provided',
})


def is_placeholder_rationale(text) -> bool:
    """Return True if *text* is a placeholder rather than a real rationale.

    LLMs sometimes return literal strings like 'No rationale provided' instead
    of an actual explanation. These should be treated the same as a missing
    rationale — they carry no keyword signal and cannot validate the translation.
    Non-string values (NaN, None, float) return False so callers don't need to
    pre-filter.
    """
    if not isinstance(text, str):
        return False
    return text.strip().lower().rstrip('.') in _PLACEHOLDER_RATIONALE_STEMS


# LLM service column pairs: (translation_col, rationale_col)
LLM_SERVICE_COL_PAIRS: List[Tuple[str, str]] = [
    ('claude_translated_term',  'claude_translation_rationale'),
    ('openai_translated_term',  'openai_translation_rationale'),
    ('gemini_translated_term',  'gemini_translation_rationale'),
    ('ollama_translated_term',  'ollama_translation_rationale'),
]


def enforce_translation_rationale_pairing(df: pd.DataFrame) -> pd.DataFrame:
    """Null out the unpaired side of any LLM translation ↔ rationale mismatch.

    For each LLM service:
    - Translation present but rationale absent/placeholder → null the translation.
    - Rationale present but translation absent → null the rationale.

    Non-LLM sources — MT baselines (GT, EasyNMT, Lingvanex) and community
    references (Wikipedia) — are skipped because they never produce rationales
    by design.

    Returns a copy with the offending cells set to NaN.
    """
    df = df.copy()
    for trans_col, rat_col in LLM_SERVICE_COL_PAIRS:
        if trans_col not in df.columns or rat_col not in df.columns:
            continue

        has_trans = df[trans_col].notna() & ~df[trans_col].astype(str).str.strip().isin(['', 'nan'])
        rat_raw   = df[rat_col].astype(str)
        has_rat   = df[rat_col].notna() & ~rat_raw.str.strip().isin(['', 'nan']) & ~rat_raw.apply(
            lambda v: is_placeholder_rationale(v)
        )

        # Translation without real rationale → drop translation
        df.loc[has_trans & ~has_rat, trans_col] = None
        # Rationale (or placeholder) without translation → drop rationale
        df.loc[~has_trans, rat_col] = None

    return df


def load_manual_exclusions(
    eval_dir: str,
) -> tuple[set, set, dict]:
    """Load manual_exclusions.csv and return three filtered structures.

    Parameters
    ----------
    eval_dir : str
        Path to the evaluation directory containing manual_exclusions.csv.

    Returns
    -------
    analysis_terms : set[tuple[str, str]]
        ``(language_code, term)`` pairs excluded from analysis. The review
        interface records these decisions at translation-cluster level; they
        must not be promoted to whole-language exclusions.
    search_terms : set[tuple[str, str]]
        (language_code, term) pairs that must not be used as search strings.
    corrections : dict[tuple[str, str], str]
        Mapping (language_code, original_term) → corrected_term.
    """
    path = os.path.join(eval_dir, 'manual_exclusions.csv')
    if not os.path.exists(path):
        return set(), set(), {}

    # keep_default_na=False preserves the valid ISO 639-3 code ``nan``.
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    analysis_rows = df[
        (df['service'] == 'analysis_exclusion') &
        (df['language_code'].str.strip() != '') &
        (df['original_term'].str.strip() != '')
    ]
    analysis_terms: set[tuple[str, str]] = set(
        zip(analysis_rows['language_code'], analysis_rows['original_term'])
    )
    search_terms: set[tuple[str, str]] = set(
        zip(
            df.loc[df['service'] == 'search_exclusion', 'language_code'],
            df.loc[df['service'] == 'search_exclusion', 'original_term'],
        )
    )
    corr_rows = df[
        (df['service'] == 'term_correction') &
        (df['corrected_term'].str.strip() != '')
    ]
    corrections: dict[tuple[str, str], str] = {
        (row['language_code'], row['original_term']): row['corrected_term']
        for _, row in corr_rows.iterrows()
    }

    return analysis_terms, search_terms, corrections


def apply_manual_analysis_exclusions(
    df: pd.DataFrame,
    analysis_terms: set[tuple[str, str]],
    term_columns: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Mask manually excluded translation terms without dropping languages.

    ``analysis_exclusion`` rows exported by the review interface identify a
    translation cluster through ``(language_code, original_term)``. Every
    matching translation cell is set to ``None`` while the language row and
    unrelated translations remain available for analysis.
    """
    if not analysis_terms or 'language_code' not in df.columns:
        return df.copy()

    result = df.copy()
    columns = list(term_columns) if term_columns is not None else [
        col for col in result.columns if col.endswith('_translated_term')
    ]
    exclusions_by_language: dict[str, set[str]] = {}
    for language_code, term in analysis_terms:
        exclusions_by_language.setdefault(str(language_code).strip(), set()).add(str(term).strip())

    for col in columns:
        if col not in result.columns:
            continue
        excluded = result.apply(
            lambda row: (
                str(row['language_code']).strip() in exclusions_by_language
                and isinstance(row[col], str)
                and row[col].strip() in exclusions_by_language[str(row['language_code']).strip()]
            ),
            axis=1,
        )
        result.loc[excluded, col] = None

    return result
