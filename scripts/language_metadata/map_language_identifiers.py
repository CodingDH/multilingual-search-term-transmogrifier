"""BCP 47 normalization and translation-service identifier mapping."""

import os
import re
from pathlib import Path

import langcodes
import pandas as pd
from rich.console import Console

console = Console()

BCP47_GRANDFATHERED_FALLBACKS = {
    'zh-classical': 'lzh',       # Literary/Classical Chinese
    'be-x-old':     'be-tarask', # Belarusian Taraškievica orthography
    'bat-smg':      'sgs',       # Samogitian
    'fiu-vro':      'vro',       # Võro
    'map-bms':      'jv',        # Banyumasan (no stable ISO 639-3 code in common use)
    'roa-rup':      'rup',       # Aromanian
    'tokipona':     'tok',       # Toki Pona — IANA registered the `tok` subtag in 2022
}

SERVICE_LANGUAGE_CODE_SUPPORT_FILENAME = 'service_language_code_support.csv'

def _canonicalize_bcp47_like_tag(tag: str) -> str:
    """Return a canonical BCP 47 tag, or ''.

    Delegates to ``langcodes.standardize_tag`` (which validates against the
    IANA Language Subtag Registry shipped via ``language_data``: case
    normalization, hyphen/underscore, IANA Preferred-Value rewrites including
    deprecated subtags like ``iw`` → ``he`` and Wikimedia-legacy mappings like
    ``zh-min-nan`` → ``nan``).

    Some grandfathered Wikimedia tags (``bat-smg``, ``be-x-old``, ``tokipona``,
    etc.) are not in the 2021-08-06 IANA snapshot ``language_data`` ships, so
    those fall through to ``BCP47_GRANDFATHERED_FALLBACKS`` below. The literal
    string ``nan`` is the ISO 639-3 code for Min Nan Chinese and is preserved
    here — never treated as a missing-value sentinel.
    """
    if tag is None:
        return ''
    tag = str(tag).strip()
    if not tag or tag.lower() in {'none', 'null'}:
        return ''
    # 'nan' (Min Nan Chinese) is a real language code; check before pandas-NaN handling
    # might tempt anyone to drop it.
    if tag in BCP47_GRANDFATHERED_FALLBACKS:
        return BCP47_GRANDFATHERED_FALLBACKS[tag]
    try:
        return langcodes.standardize_tag(tag)
    except langcodes.LanguageTagError:
        # Tag isn't a well-formed BCP 47 subtag and isn't in our grandfathered
        # fallback list — return the underscore-normalized form so downstream
        # joins still work and the audit script can surface it.
        return tag.replace('_', '-')

def _preferred_bcp47_for_row(row):
    """Choose a preferred BCP 47 tag for a language row.

    Returns (tag, source, note). language_code remains canonical; this tag is
    an interoperability hint for web/HTML/XML/API contexts.
    """
    code = str(row.get('language_code', '')).strip()
    if code in BCP47_GRANDFATHERED_FALLBACKS:
        return (BCP47_GRANDFATHERED_FALLBACKS[code],
                'grandfathered_fallback',
                f'Wikimedia/legacy code {code} not in language_data IANA snapshot; mapped manually')
    # Prefer ISO 639-1 — IANA / BCP 47 uses the shortest primary subtag available.
    # The literal 'nan' here is filtered as a pandas-NaN sentinel, NOT as the
    # Min Nan Chinese code — iso639_1 is the 2-letter slot and Min Nan has no 2-letter code.
    iso1 = str(row.get('iso639_1', '')).strip()
    if iso1 and iso1.lower() not in {'nan', 'none'}:
        return (_canonicalize_bcp47_like_tag(iso1), 'iso639_1', '')
    iso2t = str(row.get('iso639_2_t', '')).strip()
    if iso2t and iso2t.lower() not in {'nan', 'none'}:
        return (_canonicalize_bcp47_like_tag(iso2t), 'iso639_2_t', '')
    return (_canonicalize_bcp47_like_tag(code), 'language_code', '')

def _candidate_codes_for_services(row) -> list:
    """Return likely codes/tags to test against service-specific support lists.

    Adds legacy IANA-deprecated aliases (e.g. ``iw`` for ``he``, ``jw`` for
    ``jv``) so a match against a service that still accepts the deprecated form
    counts as supported. The alias list is sourced from
    ``langcodes.LANGUAGE_REPLACEMENTS`` — the full IANA Preferred-Value map,
    not a hand-curated subset.
    """
    values = [
        row.get('bcp47_tag', ''),
        row.get('language_code', ''),
        row.get('wikimedia_code', ''),
        row.get('iso639_1', ''),
        row.get('iso639_2_t', ''),
        row.get('iso639_2_b', ''),
    ]
    out = []
    for v in values:
        if v is None: continue
        v = str(v).strip()
        if not v or v.lower() in {'none', 'null'}: continue
        canonical = _canonicalize_bcp47_like_tag(v)
        variants = {v, v.replace('_', '-'), canonical}
        for legacy, preferred in langcodes.LANGUAGE_REPLACEMENTS.items():
            if canonical == preferred:
                variants.add(legacy)
        for cand in variants:
            if cand and cand not in out:
                out.append(cand)
    return out

def add_identifier_context(comp_df: pd.DataFrame) -> pd.DataFrame:
    """Add BCP 47 and platform-code context columns without changing row identity.

    `language_code` remains the project-level stable identifier. This function
    adds an interoperability layer alongside it:

    - `project_language_code`: explicit duplicate of the project identifier
    - `wikimedia_code`: exact Wikimedia code where applicable
    - `bcp47_tag`: preferred BCP 47-style web / interchange tag
    - `bcp47_source`: provenance ('iso639_1' / 'iso639_2_t' / 'grandfathered_fallback' / 'language_code')
    - `bcp47_note`: free-text note for overrides
    - `bcp47_is_project_code`: bool — true when bcp47_tag matches the normalized project code
    - `service_code_candidates`: pipe-separated candidate codes for service matching

    Does NOT create new rows for regional/script variants. That expansion would
    change the analytical unit from language/community to locale.
    """
    df = comp_df.copy()
    df['project_language_code'] = df['language_code'].astype(str)

    # Preserve exact Wikimedia project codes separately.
    df['wikimedia_code'] = ''
    if 'in_wikimedia' in df.columns:
        mask = df['in_wikimedia'].astype(bool)
        df.loc[mask, 'wikimedia_code'] = df.loc[mask, 'language_code'].astype(str)

    chosen = df.apply(_preferred_bcp47_for_row, axis=1)
    df['bcp47_tag']    = [x[0] for x in chosen]
    df['bcp47_source'] = [x[1] for x in chosen]
    df['bcp47_note']   = [x[2] for x in chosen]
    # True only when bcp47_tag is a mechanical rewrite of language_code
    # (case/hyphen-normalization). False when IANA Preferred-Value or a
    # grandfathered fallback actually changed the primary subtag — that's the
    # signal downstream users care about: "is the BCP 47 column telling me
    # something different than the project code already says?"
    df['bcp47_is_project_code'] = (
        df['bcp47_tag'].str.lower()
        == df['language_code'].astype(str).str.replace('_', '-', regex=False).str.lower()
    )
    df['service_code_candidates'] = df.apply(
        lambda row: '|'.join(_candidate_codes_for_services(row)), axis=1
    )

    n_diff = int((df['bcp47_tag'] != df['language_code'].astype(str)).sum())
    n_over = int((df['bcp47_source'] == 'grandfathered_fallback').sum())
    console.print(f'  Identifier context: {n_diff} rows have BCP47 tag different from project code; '
                  f'{n_over} grandfathered fallbacks')
    return df

def add_service_language_codes(comp_df: pd.DataFrame, support_csv: str = None) -> pd.DataFrame:
    """Map rows to exact codes required by services/APIs when a support CSV exists.

    The optional CSV must contain at least `service` and `service_code` columns.
    Other columns (language_name, support_level, model, notes) are ignored by
    the matcher but preserved in the source CSV for documentation.

    For each distinct service, adds:
        <service>_code       — exact supported code selected for this row (or '')
        <service>_supported  — boolean

    Matching uses bcp47_tag, language_code, wikimedia_code, ISO fields, and
    legacy aliases. Never modifies language_code itself.
    """
    df = comp_df.copy()
    if support_csv is None:
        # default lookup: metadata_files/service_language_code_support.csv
        from pathlib import Path
        here = Path(__file__).resolve()
        # Language metadata lives three levels below the repository root.
        candidate = here.parent.parent.parent / 'datasets' / 'metadata_files' / SERVICE_LANGUAGE_CODE_SUPPORT_FILENAME
        support_csv = str(candidate) if candidate.exists() else None
    if not support_csv or not os.path.exists(support_csv):
        console.print(f'  Service support CSV not found; skipping service-code columns')
        return df

    support = pd.read_csv(support_csv, dtype=str, na_filter=False)
    required = {'service', 'service_code'}
    if not required.issubset(support.columns):
        console.print(f'  Service support CSV missing required columns {required}: {support_csv}')
        return df

    support['service'] = support['service'].str.strip()
    support['service_code'] = support['service_code'].str.strip()

    for service, sdf in support.groupby('service'):
        if not service: continue
        # Lookup: exact code → exact code, plus underscore→hyphen and canonical variants
        code_lookup = {c: c for c in sdf['service_code'] if c}
        for c in list(code_lookup):
            code_lookup.setdefault(c.replace('_', '-'), c)
            code_lookup.setdefault(_canonicalize_bcp47_like_tag(c), c)
        # Per-row match via candidate codes
        selected = []
        for _, row in df.iterrows():
            match = ''
            for cand in _candidate_codes_for_services(row):
                if cand in code_lookup:
                    match = code_lookup[cand]
                    break
            selected.append(match)

        safe = re.sub(r'[^0-9A-Za-z_]+', '_', service).strip('_').lower()
        df[f'{safe}_code']      = selected
        df[f'{safe}_supported'] = [bool(x) for x in selected]
        console.print(f'  Service codes: {service} matched {sum(bool(x) for x in selected)}/{len(df)} rows')

    return df
