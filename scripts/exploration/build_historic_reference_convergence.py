#!/usr/bin/env python3
"""
Build historic reference convergence tables for notebook 02.

This script keeps two historic artifacts separate:

1. ``historic_materials/translated_dh_terms.csv`` (November 2022)
   The flattened early translation artifact. For ``Digital Humanities``, the
   ``term`` column contains pre-existing/Wikipedia-derived terms where available
   and ``translated_term`` contains the historic Google Translate output.

2. ``historic_materials/initial_translated_terms.csv`` (November 2024)
   The initial prompt-reference artifact. It stores Wikipedia, Google
   Translate, EasyNMT, and OpenAI outputs side by side for the same
   ``Digital Humanities`` term.

Outputs are written to:
    datasets/translated_terms/digital_humanities/evaluation/

Usage:
    python scripts/exploration/build_historic_reference_convergence.py
    python scripts/exploration/build_historic_reference_convergence.py --term "Digital Humanities"
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from rich.console import Console
from rich.table import Table

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scripts.utils import analyze_differences, get_data_directory_path

console = Console()


@dataclass(frozen=True)
class HistoricArtifactConfig:
    prefix: str
    label: str
    relative_path: str
    language_col: str
    service_columns: dict[str, str]
    context_columns: dict[str, str]
    role: str


HISTORIC_ARTIFACTS = [
    HistoricArtifactConfig(
        prefix='historic_2022',
        label='November 2022 flattened historic translation artifact',
        relative_path='historic_materials/translated_dh_terms.csv',
        language_col='language',
        service_columns={
            'Wikipedia/pre-existing term': 'term',
            'Historic Google Translate output': 'translated_term',
        },
        context_columns={},
        role=(
            'November 2022 flattened output; compares pre-existing/Wikipedia-derived '
            'Digital Humanities terms with historic Google Translate outputs'
        ),
    ),
    HistoricArtifactConfig(
        prefix='historic_2024',
        label='November 2024 initial prompt-reference artifact',
        relative_path='historic_materials/initial_translated_terms.csv',
        language_col='language_code',
        service_columns={
            'Wikipedia': 'wikipedia_translated_term',
            'Google Translate': 'gt_translated_term',
            'EasyNMT': 'enmt_translated_term',
            'OpenAI': 'openai_translated_term',
        },
        context_columns={
            'wikipedia_or_preexisting_term': 'term',
            'ollama_historic_output': 'ollama_translated_term',
        },
        role=(
            'November 2024 initial prompt-reference output; compares Wikipedia, '
            'Google Translate, EasyNMT, and OpenAI outputs'
        ),
    ),
]

DETAIL_OUTPUT_COLUMNS = {
    'term': 'wikipedia_or_preexisting_term',
    'translated_term': 'google_translate_historic_output',
    'gt_translated_term': 'google_translate_historic_output',
    'enmt_translated_term': 'easynmt_historic_output',
    'openai_translated_term': 'openai_historic_output',
}


def has_text(value) -> bool:
    value = '' if value is None else str(value).strip()
    return bool(value) and value.lower() not in {'nan', 'none', 'null'}


def normalize_translation(value) -> str:
    """Conservative exact-agreement normalization."""
    if not has_text(value):
        return ''
    text = unicodedata.normalize('NFKC', str(value)).casefold()
    text = re.sub(r'\s+', ' ', text).strip()
    return text.strip(' "\'“”‘’.,;:!¡?¿()[]{}')


def _filter_term(df: pd.DataFrame, term: str, path: Path) -> pd.DataFrame:
    if 'term_source' not in df.columns:
        raise ValueError(f'Missing term_source column in {path}')
    filtered = df[df['term_source'].astype(str).str.strip() == term].copy()
    if filtered.empty:
        available = sorted(df['term_source'].dropna().astype(str).unique().tolist())
        raise ValueError(
            f'No rows for term_source={term!r} in {path}. '
            f'Available term_source values: {available}'
        )
    return filtered


def _load_directionality(data_dir: Path) -> dict[str, str]:
    meta_path = data_dir / 'metadata_files' / 'language_codes_comprehensive.csv'
    if not meta_path.exists():
        return {}
    meta = pd.read_csv(meta_path, dtype=str, keep_default_na=False)
    if not {'language_code', 'directionality'}.issubset(meta.columns):
        return {}
    return dict(zip(meta['language_code'], meta['directionality']))


def _check_columns(frame: pd.DataFrame, config: HistoricArtifactConfig, path: Path) -> None:
    required = {'term_source', config.language_col, 'language_name'}
    required.update(config.service_columns.values())
    missing = sorted(col for col in required if col not in frame.columns)
    if missing:
        raise ValueError(f'{path} is missing required column(s): {missing}')


def _build_artifact_outputs(
    *,
    frame: pd.DataFrame,
    config: HistoricArtifactConfig,
    path: Path,
    term: str,
    directionality: dict[str, str],
) -> dict[str, pd.DataFrame]:
    service_cols = list(config.service_columns.values())
    source_presence = frame[service_cols].map(has_text)

    artifact_scope = pd.DataFrame([
        {
            'artifact': config.relative_path,
            'artifact_label': config.label,
            'term_source': term,
            'rows': len(frame),
            'languages': frame[config.language_col].nunique(),
            'terms': frame['term_source'].nunique(),
            'nonblank_translation_rows': int(source_presence.any(axis=1).sum()),
            'role_in_this_section': config.role,
        },
    ])

    service_presence = []
    for service, col in config.service_columns.items():
        present = frame[col].map(has_text)
        service_presence.append({
            'source': service,
            'translation_column': col,
            'rows_with_translation': int(present.sum()),
            'total_rows': len(frame),
            'coverage_rate': present.sum() / len(frame) if len(frame) else 0,
        })
    service_presence = pd.DataFrame(service_presence)

    convergence_records = []
    for _, row in frame.iterrows():
        language_code = row.get(config.language_col, '')
        row_directionality = directionality.get(language_code, 'ltr') or 'ltr'

        all_values = []
        service_values = {}
        for service, col in config.service_columns.items():
            raw = row.get(col, '')
            norm = normalize_translation(raw)
            service_values[service] = raw if has_text(raw) else None
            if norm:
                all_values.append((service, raw, norm))

        all_unique = len({norm for _, _, norm in all_values})
        if not all_values:
            convergence_label = 'no outputs'
        elif len(all_values) == 1:
            convergence_label = 'one output only'
        elif all_unique == 1:
            convergence_label = 'all available outputs agree'
        else:
            convergence_label = 'outputs diverge'

        differences = analyze_differences(service_values, row_directionality)

        record = {
            'language_code': language_code,
            'language_name': row.get('language_name', ''),
            'term_source': term,
            'directionality': row_directionality,
            'all_available_sources': '; '.join(service for service, _, _ in all_values),
            'n_sources_present': len(all_values),
            'n_distinct_translations': all_unique,
            'sources_agree': len(all_values) > 1 and all_unique == 1,
            'all_source_convergence': convergence_label,
            'difference_summary': differences.get('summary', 'unknown'),
            'difference_details': str(differences),
        }
        for output_col, input_col in config.context_columns.items():
            record[output_col] = row.get(input_col, '')
        for service, input_col in config.service_columns.items():
            output_col = DETAIL_OUTPUT_COLUMNS.get(input_col)
            if output_col is None:
                output_col = (
                    service
                    .lower()
                    .replace('/', '_')
                    .replace('-', '_')
                    .replace(' ', '_')
                    .replace('__', '_')
                    + '_historic_output'
                )
            record[output_col] = row.get(input_col, '')
        convergence_records.append(record)
    convergence_detail = pd.DataFrame(convergence_records)

    pairwise_records = []
    services = list(config.service_columns.items())
    for i, (service_a, col_a) in enumerate(services):
        for service_b, col_b in services[i + 1:]:
            overlap_mask = frame[col_a].map(has_text) & frame[col_b].map(has_text)
            overlap = frame[overlap_mask].copy()
            if overlap.empty:
                agreement_mask = pd.Series(dtype=bool)
            else:
                agreement_mask = overlap.apply(
                    lambda r: normalize_translation(r[col_a]) == normalize_translation(r[col_b]),
                    axis=1,
                )
            pairwise_records.append({
                'comparison': f'{service_a} vs {service_b}',
                'source_a': service_a,
                'source_b': service_b,
                'term_source': term,
                'overlap': len(overlap),
                'exact_normalized_agreements': int(agreement_mask.sum()),
                'agreement_rate': agreement_mask.mean() if len(overlap) else 0,
            })
    pairwise_agreement = pd.DataFrame(pairwise_records)

    ref_count_summary = (
        convergence_detail
        .groupby('n_sources_present', as_index=False)
        .agg(
            rows=('language_code', 'size'),
            sources_agree=('sources_agree', 'sum'),
            outputs_all_agree=('sources_agree', 'sum'),
        )
    )
    ref_count_summary['term_source'] = term
    ref_count_summary['agreement_rate'] = (
        ref_count_summary['sources_agree'] / ref_count_summary['rows']
    )

    all_source_summary = (
        convergence_detail['all_source_convergence']
        .value_counts()
        .rename_axis('convergence_category')
        .reset_index(name='rows')
    )
    all_source_summary['term_source'] = term
    all_source_summary['share'] = all_source_summary['rows'] / len(convergence_detail)

    return {
        'reference_artifacts': artifact_scope,
        'reference_service_presence': service_presence,
        'pairwise_reference_agreement': pairwise_agreement,
        'reference_count_summary': ref_count_summary,
        'all_source_convergence_summary': all_source_summary,
        'reference_convergence_detail': convergence_detail,
    }


def build_historic_reference_convergence(
    data_dir: str | Path,
    term: str = 'Digital Humanities',
    source_slug: str = 'digital_humanities',
    output_dir: Optional[str | Path] = None,
) -> dict[str, dict[str, pd.DataFrame]]:
    data_dir = Path(data_dir)
    project_root = data_dir.parent
    source_dir = data_dir / 'translated_terms' / source_slug
    eval_dir = Path(output_dir) if output_dir else source_dir / 'evaluation'
    eval_dir.mkdir(parents=True, exist_ok=True)
    directionality = _load_directionality(data_dir)

    all_outputs = {}
    for config in HISTORIC_ARTIFACTS:
        path = project_root / config.relative_path
        if not path.exists():
            raise FileNotFoundError(path)

        frame_all = pd.read_csv(path, dtype=str, keep_default_na=False)
        _check_columns(frame_all, config, path)
        frame = _filter_term(frame_all, term, path)
        outputs = _build_artifact_outputs(
            frame=frame,
            config=config,
            path=path,
            term=term,
            directionality=directionality,
        )

        for name, df in outputs.items():
            df.to_csv(eval_dir / f'{config.prefix}_{name}.csv', index=False)
        all_outputs[config.prefix] = outputs

    return all_outputs


def print_summary(outputs: dict[str, dict[str, pd.DataFrame]], output_dir: Path) -> None:
    for prefix, artifact_outputs in outputs.items():
        artifact = artifact_outputs['reference_artifacts'].iloc[0]
        table = Table(title=f"{prefix}: {artifact['artifact_label']}")
        table.add_column('Comparison')
        table.add_column('Overlap', justify='right')
        table.add_column('Agreements', justify='right')
        table.add_column('Agreement rate', justify='right')

        pairwise = artifact_outputs['pairwise_reference_agreement']
        for _, row in pairwise.iterrows():
            table.add_row(
                row['comparison'],
                f"{int(row['overlap']):,}",
                f"{int(row['exact_normalized_agreements']):,}",
                f"{row['agreement_rate']:.1%}",
            )
        console.print(table)
    console.print(f'[green]Wrote outputs to:[/green] {output_dir}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--term', default='Digital Humanities')
    parser.add_argument('--data-dir', default=None)
    parser.add_argument('--source-slug', default='digital_humanities')
    parser.add_argument('--output-dir', default=None)
    args = parser.parse_args()

    data_dir = Path(args.data_dir or get_data_directory_path())
    source_dir = data_dir / 'translated_terms' / args.source_slug
    output_dir = Path(args.output_dir) if args.output_dir else source_dir / 'evaluation'

    outputs = build_historic_reference_convergence(
        data_dir=data_dir,
        term=args.term,
        source_slug=args.source_slug,
        output_dir=output_dir,
    )
    print_summary(outputs, output_dir)


if __name__ == '__main__':
    main()
