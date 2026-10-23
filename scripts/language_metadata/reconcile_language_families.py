"""Language-family assignment and Glottolog reconciliation."""

import os
from pathlib import Path

import pandas as pd
from rich.console import Console

from scripts.language_metadata.language_metadata_overrides import MANUAL_LANG_TO_SET5
from scripts.language_metadata.parse_cldr_json import _ISO639_5_NAMES

console = Console()

def add_family_info(comp_df: pd.DataFrame, set5_df: pd.DataFrame,
                    fallback_json: str = None) -> pd.DataFrame:
    """
    Join ISO 639-5 family information onto the comprehensive DataFrame.

    Uses MANUAL_LANG_TO_SET5 as the primary lookup, then falls back to
    language_family_assignments.json for codes that MANUAL does not cover.
    The JSON file also corrects known errors in legacy reference data (e.g.
    Limburgish misclassified as Romance, Zhuang as Sino-Tibetan).

    Parameters
    ----------
    comp_df : DataFrame from build_comprehensive.
    set5_df : DataFrame containing ISO 639-5 family/group codes and hierarchy.
    fallback_json : path to language_family_assignments.json; defaults to the
        file sitting alongside this script.

    Returns
    -------
    comp_df enriched with iso639_5_direct, iso639_5_family, family_name,
    and subfamily_name columns.
    """
    import json as _json
    from scripts.language_metadata.parse_cldr_json import _ISO639_5_NAMES

    code_to_parent = dict(zip(set5_df['iso639_5'], set5_df['parent_code']))
    code_to_name   = dict(zip(set5_df['iso639_5'], set5_df['family_name']))
    code_to_depth  = dict(zip(set5_df['iso639_5'], set5_df['depth']))

    # Supplement with names for ISO 639-5 codes used in MANUAL_LANG_TO_SET5 that
    # are not in CLDR's languageGroups (e.g. hyx=Armenian, sqj=Albanian, grk=Greek).
    # These appear as iso639_5_direct values but have no entry in set5_df, so
    # top_family() returns the code itself and we need a name for it.
    code_to_name.update({k: v for k, v in _ISO639_5_NAMES.items()
                         if k not in code_to_name or not code_to_name[k]})

    # Load JSON fallback (codes not covered by MANUAL_LANG_TO_SET5)
    if fallback_json is None:
        fallback_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     '..', '..', 'datasets', 'metadata_files',
                                     'language_family_assignments.json')
    json_fallback: dict = {}
    if os.path.exists(fallback_json):
        with open(fallback_json, encoding='utf-8') as f:
            json_fallback = {e['language_code']: e for e in _json.load(f)}

    def top_family(code):
        if not code or code == 'isolate':
            return code
        visited, current = set(), code
        while current and current not in visited:
            if code_to_depth.get(current, 99) == 0:
                return current
            visited.add(current)
            current = code_to_parent.get(current, '')
        return code

    rows_out = []
    for _, row in comp_df.iterrows():
        lang = str(row['language_code']).strip()
        iso2 = str(row.get('iso639_2_t', '')).strip()
        direct = (MANUAL_LANG_TO_SET5.get(lang) or
                  MANUAL_LANG_TO_SET5.get(iso2) or '')

        # JSON fallback for codes not in MANUAL
        fb = json_fallback.get(lang, {})
        if not direct and fb.get('iso639_5'):
            direct = fb['iso639_5']

        if not direct and lang in code_to_name:
            direct = lang

        top    = top_family(direct) if direct else ''
        fname  = ('Language isolate' if top == 'isolate'
                  else code_to_name.get(top, ''))
        sfname = code_to_name.get(direct, fname)

        # Final fallback: use family_name string from JSON when ISO 639-5 gives nothing
        if not fname and fb.get('family_name'):
            fname  = fb['family_name']
            sfname = fb.get('family_name', fname)

        rows_out.append((direct, top, fname, sfname))

    comp_df = comp_df.copy()
    comp_df['iso639_5_direct'] = [r[0] for r in rows_out]
    comp_df['iso639_5_family'] = [r[1] for r in rows_out]
    comp_df['family_name']     = [r[2] for r in rows_out]
    comp_df['subfamily_name']  = [r[3] for r in rows_out]

    covered = (comp_df['iso639_5_family'] != '').sum()
    console.print(f"  Family assigned: {covered}/{len(comp_df)} "
        f"({covered/len(comp_df)*100:.0f}%)")
    json_covered = sum(1 for e in rows_out if e[2])
    console.print(f"  JSON fallback used: {sum(1 for lang in comp_df['language_code'] if lang in json_fallback and not MANUAL_LANG_TO_SET5.get(lang))} codes")
    return comp_df

def _norm_family_name(s) -> str:
    """Strip trailing 'languages'/'language' suffix and lowercase for comparison."""
    if not isinstance(s, str): return ''
    s = s.strip().lower()
    for suffix in (' languages', ' language'):
        if s.endswith(suffix):
            s = s[:-len(suffix)]
            break
    return s

def add_family_reconciliation(comp_df: pd.DataFrame, metadata_dir: str = None) -> pd.DataFrame:
    """Add `family_name_reconciled` by cross-checking against Glottolog 5.3.

    Glottolog wins where (a) ISO 639-5 uses geographic rather than genealogical
    groupings ('Caucasian', 'North American Indian'), (b) macrofamilies are
    abandoned ('Niger-Kordofanian') or contested ('Altaic'). ISO 639-5 wins
    where Glottolog's category is a metadata tag ('Bookkeeping', 'Unclassifiable')
    or where the disagreement is sociolinguistic ('Creoles and pidgins').
    Per-pair decisions live in `family_reconciliation.csv`.
    """
    df = comp_df.copy()

    if metadata_dir is None:
        from pathlib import Path
        here = Path(__file__).resolve()
        metadata_dir = str(here.parent.parent.parent / 'datasets' / 'metadata_files')

    glot_path  = os.path.join(metadata_dir, 'glottolog-cache', 'languoid.csv')
    recon_path = os.path.join(metadata_dir, 'family_reconciliation.csv')

    if not (os.path.exists(glot_path) and os.path.exists(recon_path)):
        console.print(
            f'  Glottolog cache or reconciliation CSV missing; family_name_reconciled = family_name'
        )
        df['family_name_reconciled'] = df['family_name']
        return df

    glot = pd.read_csv(glot_path, low_memory=False)
    _id_to_name = glot.set_index('id')['name'].to_dict()
    glot['glottolog_family'] = glot['family_id'].map(_id_to_name)
    glot_lang = glot[(glot['level'] == 'language') & glot['iso639P3code'].notna()].copy()

    def _iso639_3(row):
        for col in ('language_code', 'iso639_2_t'):
            v = row.get(col)
            if isinstance(v, str) and len(v) == 3:
                return v
        return None

    df['_iso639_3'] = df.apply(_iso639_3, axis=1)
    df = df.merge(
        glot_lang[['iso639P3code', 'glottolog_family']],
        left_on='_iso639_3', right_on='iso639P3code', how='left',
    )
    df = df.drop(columns=['_iso639_3', 'iso639P3code'], errors='ignore')

    recon = pd.read_csv(recon_path)
    recon_lookup = {
        (r['family_name_iso'], r['family_name_glottolog']): r['chosen_family_name']
        for _, r in recon.iterrows()
    }

    def _reconcile(row):
        our  = row.get('family_name')
        glot = row.get('glottolog_family')
        if not isinstance(our, str):  return our
        if not isinstance(glot, str): return our  # no Glottolog match — keep ours
        if _norm_family_name(our) == _norm_family_name(glot): return our  # agreement
        return recon_lookup.get((our, glot), our)  # disagreement — apply or fall back

    df['family_name_reconciled'] = df.apply(_reconcile, axis=1)

    # Identify disagreement pairs the reconciliation CSV doesn't cover.
    # These are pairs where ISO 639-5 and Glottolog disagree but no per-pair
    # decision exists yet — so the row silently falls back to family_name and
    # the methodological choice is implicit rather than recorded. Surface them
    # so the author can open the reviewer and add explicit decisions.
    has_both = df['family_name'].astype(str).str.len().gt(0) & df['glottolog_family'].notna()
    valid = df[has_both]
    pairs_seen = {
        (our, glot)
        for our, glot in zip(valid['family_name'], valid['glottolog_family'])
        if _norm_family_name(our) != _norm_family_name(glot)
    }
    uncovered_pairs = pairs_seen - set(recon_lookup.keys())

    df = df.drop(columns=['glottolog_family'], errors='ignore')

    n_total      = len(df)
    n_matched    = df['family_name_reconciled'].notna().sum()
    n_changed    = (df['family_name_reconciled'] != df['family_name']).sum()
    n_unchanged  = n_matched - n_changed
    console.print(
        f'  Family reconciliation: {n_changed} reclassified vs ISO 639-5 family_name, '
        f'{n_unchanged} unchanged, {n_total - n_matched} with no Glottolog match'
    )
    if uncovered_pairs:
        console.print(
            f'\n  [yellow]⚠ {len(uncovered_pairs)} disagreement pair(s) NOT in family_reconciliation.csv '
            f'(silently kept as ISO 639-5):[/yellow]'
        )
        for our, glot in sorted(uncovered_pairs)[:5]:
            n_affected = sum(
                1 for o, g in zip(valid['family_name'], valid['glottolog_family'])
                if o == our and g == glot
            )
            console.print(f'      ISO: {our!r}  vs  Glottolog: {glot!r}   ({n_affected} languages)')
        if len(uncovered_pairs) > 5:
            console.print(f'      ... and {len(uncovered_pairs) - 5} more')
        console.print(
            '  [yellow]→ Open html_files/family_reconciliation_reviewer.html to add explicit decisions,[/yellow]\n'
            '  [yellow]  then re-run generate_language_codes.py to apply.[/yellow]'
        )
    return df
