#!/usr/bin/env python3
"""Build a multidimensional, non-exclusive disagreement-pattern table.

The comparison status in ``disagreement_analysis.csv`` measures only degree of
string convergence. This script adds descriptive pattern dimensions without
inferring correctness or a single cause: cluster shape, service-group topology,
prompt sensitivity, Wikipedia relationship, source retention, script evidence,
and rationale/definitional signals.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scripts.utils import get_data_directory_path, read_csv_file
from scripts.exploration.explore_disagreements import normalize


SERVICE_GROUPS = {
    'Wikipedia': 'community',
    'Google Translate': 'mt',
    'EasyNMT': 'mt',
    'Lingvanex': 'mt',
    'Claude': 'api_llm',
    'OpenAI': 'api_llm',
    'Gemini': 'api_llm',
    'DeepSeek': 'api_llm',
    'Llama': 'local_llm',
    'Gemma': 'local_llm',
    'Qwen': 'local_llm',
    'Mistral': 'local_llm',
}

LLM_KEYS = ('claude', 'openai', 'gemini', 'deepseek', 'llama', 'gemma', 'qwen', 'mistral')
VARIANTS = ('minimal', 'fluent_speaker', 'github_searcher', 'judge')
SOURCE_TOKENS = ('digital humanities', 'digital', 'humanities', 'dh')

REGISTER_PATTERNS = {
    'compositional_literal': [
        r'\bcombines?\b.*\bdigital\b',
        r'\bdigital\b.*\b(?:and|with|plus)\b.*\bhumanities\b',
    ],
    'scholarly_methodological': [
        r'\binterdisciplinary\b', r'\bcomputational\s+method',
        r'\bdigital\s+(?:methods?|tools?)\s+(?:to|in|for)\s+(?:study|stud|research|analy)',
        r'\bdigital\b.*\bscholarship\b', r'\bacademic\s+(?:field|discipline)',
    ],
    'human_centered': [
        r'\bhuman\s+(?:culture|society|experience|values?|beings?)\b',
        r'\bpeople\b.*\bdigital\b', r'\bdigital\b.*\bpeople\b',
    ],
    'knowledge_generic': [
        r'\bknowledge\b', r'\blearning\b', r'\beducation\b', r'\bstudies\b',
    ],
}

STANCE_PATTERNS = {
    'claims_established_equivalent': [r'\bestablished\b', r'\bstandard term\b', r'\bwidely used\b'],
    'claims_borrowing': [r'\bborrow', r'\bloan ?word\b', r'\bretain.*english\b', r'\banglic'],
    'claims_coinage': [r'\bcoin(?:ed|age|ing)?\b', r'\bneolog', r'\bconstruct(?:ed|ion)?\b'],
    'admits_uncertainty': [r'\bno (?:direct|established|widely accepted)\b', r'\buncertain\b', r'\bmay be\b', r'\bcould be\b'],
}


def _valid(value) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {
        'nan', 'none'
    }


def _valid_rationale(value) -> bool:
    if not isinstance(value, str) or len(value.strip()) <= 20:
        return False
    return value.strip().rstrip('.').lower() not in {
        'nan', 'none', 'no rationale provided', 'no rationale', 'n/a',
        'not applicable', 'no explanation provided', 'no reason provided',
        '[rationale truncated — max_tokens]',
    }


def _contains_source(value: str) -> bool:
    words = set(normalize(value).split())
    return any(token in words for token in SOURCE_TOKENS)


def _cluster_services(translations: dict[str, str]) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = defaultdict(list)
    for service, term in translations.items():
        if _valid(term):
            key = normalize(term)
            if key:
                clusters[key].append(service)
    return dict(clusters)


def _dominance(values: dict[str, str], services: list[str]) -> tuple[float, str]:
    normalized = [normalize(values[s]) for s in services if s in values and _valid(values[s])]
    normalized = [v for v in normalized if v]
    if not normalized:
        return 0.0, ''
    term, count = Counter(normalized).most_common(1)[0]
    return count / len(normalized), term


def _shape(clusters: dict[str, list[str]], n_services: int) -> str:
    sizes = sorted((len(v) for v in clusters.values()), reverse=True)
    if n_services < 2:
        return 'insufficient_comparison'
    if len(sizes) == 1:
        return 'unanimous'
    if sizes[0] >= n_services - 1:
        return 'near_unanimous_with_outlier'
    if len(sizes) == 2 and abs(sizes[0] - sizes[1]) <= max(1, n_services * 0.25):
        return 'two_cluster_split'
    if sizes[0] / n_services >= 0.5:
        return 'dominant_form_with_alternatives'
    return 'fragmented_disagreement'


def _load_rationale_signal_detail(data_dir: str, term_slug: str) -> pd.DataFrame:
    eval_dir = os.path.join(data_dir, 'translated_terms', term_slug, 'evaluation')
    explorer = read_csv_file(os.path.join(eval_dir, 'disagreement_explorer_data.csv'))
    exclusions_path = os.path.join(eval_dir, 'manual_exclusions.csv')
    exclusion_lookup = {}
    if os.path.exists(exclusions_path):
        exclusions = read_csv_file(exclusions_path)
        for _, row in exclusions.iterrows():
            code = str(row.get('language_code', '')).strip()
            service = str(row.get('service', '')).strip().lower()
            if not code or not service or service == 'nan':
                continue
            exclusion_lookup[(code, service)] = {
                'translation': str(row.get('exclude_translation', 'False')).strip().lower() == 'true',
                **{
                    f'rationale_{variant}': str(
                        row.get(f'exclude_rationale_{variant}', 'False')
                    ).strip().lower() == 'true'
                    for variant in ('minimal', 'fluent_speaker', 'github_searcher', 'judge')
                },
            }

    rows = []
    for service in LLM_KEYS:
        for variant in ('minimal', 'github_searcher', 'judge'):
            rationale_col = f'{service}_rationale_{variant}'
            if rationale_col not in explorer.columns:
                continue
            for _, row in explorer[['language_code', rationale_col]].iterrows():
                code = str(row['language_code']).strip()
                rationale = row[rationale_col]
                decisions = exclusion_lookup.get((code, service), {})
                if (decisions.get('translation', False)
                        or decisions.get(f'rationale_{variant}', False)
                        or not _valid_rationale(rationale)):
                    continue
                text = str(rationale).lower()
                record = {
                    'language_code': code,
                    'service': service,
                    'variant': variant,
                }
                for label, patterns in REGISTER_PATTERNS.items():
                    record[f'register_{label}'] = any(re.search(pattern, text) for pattern in patterns)
                for label, patterns in STANCE_PATTERNS.items():
                    record[label] = any(re.search(pattern, text) for pattern in patterns)
                rows.append(record)
    return pd.DataFrame(rows)


def _load_rationale_signals(data_dir: str, term_slug: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail = _load_rationale_signal_detail(data_dir, term_slug)
    if detail.empty:
        return pd.DataFrame(columns=['language_code']), detail
    id_cols = {'language_code', 'service', 'variant'}
    signal_cols = [column for column in detail.columns if column not in id_cols]
    aggregate = detail.groupby('language_code')[signal_cols].mean().reset_index()
    return aggregate, detail


def build_patterns(data_dir: str, term: str = 'Digital Humanities') -> pd.DataFrame:
    term_slug = term.lower().replace(' ', '_')
    eval_dir = os.path.join(data_dir, 'translated_terms', term_slug, 'evaluation')
    analysis = read_csv_file(os.path.join(eval_dir, 'disagreement_analysis.csv'))
    explorer = read_csv_file(os.path.join(eval_dir, 'disagreement_explorer_data.csv'))

    prompt_cols = {
        (service, variant): f'{service}_term_{variant}'
        for service in LLM_KEYS for variant in VARIANTS
        if f'{service}_term_{variant}' in explorer.columns
    }
    explorer_by_code = explorer.drop_duplicates('language_code').set_index('language_code')
    rows = []

    for _, base in analysis.iterrows():
        code = str(base['language_code'])
        try:
            translations = ast.literal_eval(str(base['service_translations']))
        except (ValueError, SyntaxError):
            translations = {}
        translations = {str(k): str(v) for k, v in translations.items() if _valid(v)}
        clusters = _cluster_services(translations)
        sizes = sorted((len(v) for v in clusters.values()), reverse=True)
        n_services = len(translations)
        dominant_key = max(clusters, key=lambda key: len(clusters[key])) if clusters else ''
        dominant_services = sorted(clusters.get(dominant_key, []))
        dominant_share = (sizes[0] / n_services) if sizes and n_services else 0
        outliers = (
            sorted(service for services in clusters.values() if len(services) == 1 for service in services)
            if dominant_share >= 0.5 else []
        )

        api_dom, api_term = _dominance(translations, [s for s, g in SERVICE_GROUPS.items() if g == 'api_llm'])
        local_dom, local_term = _dominance(translations, [s for s, g in SERVICE_GROUPS.items() if g == 'local_llm'])
        mt_dom, mt_term = _dominance(translations, [s for s, g in SERVICE_GROUPS.items() if g == 'mt'])
        llm_dom, llm_term = _dominance(translations, [s for s, g in SERVICE_GROUPS.items() if g.endswith('llm')])
        if api_dom >= .75 and local_dom < .5:
            service_pattern = 'api_aligned_local_fragmented'
        elif local_dom >= .75 and api_dom < .5:
            service_pattern = 'local_aligned_api_fragmented'
        elif api_dom >= .75 and local_dom >= .75:
            service_pattern = 'api_and_local_aligned'
        elif api_dom < .5 and local_dom < .5:
            service_pattern = 'api_and_local_fragmented'
        else:
            service_pattern = 'mixed_group_alignment'

        mt_llm_split = bool(mt_term and llm_term and mt_dom >= .5 and llm_dom >= .5 and mt_term != llm_term)
        wiki_term = normalize(translations.get('Wikipedia', ''))
        if not wiki_term:
            wikipedia_relationship = 'no_wikipedia_term'
        elif wiki_term == dominant_key:
            wikipedia_relationship = 'matches_dominant_form'
        elif wiki_term in clusters and len(clusters[wiki_term]) > 1:
            wikipedia_relationship = 'matches_alternative_cluster'
        elif wiki_term in clusters:
            wikipedia_relationship = 'wikipedia_isolated'
        else:
            wikipedia_relationship = 'wikipedia_not_in_comparison'

        stable_services = []
        sensitive_services = []
        github_echo_services = []
        variant_unique_counts = {}
        if code in explorer_by_code.index:
            erow = explorer_by_code.loc[code]
            for service in LLM_KEYS:
                values = {
                    variant: erow.get(prompt_cols.get((service, variant), ''), '')
                    for variant in VARIANTS
                }
                normalized = [normalize(v) for v in values.values() if _valid(v)]
                if len(normalized) >= 2:
                    (stable_services if len(set(normalized)) == 1 else sensitive_services).append(service)
                if (_valid(values.get('github_searcher')) and _contains_source(values['github_searcher'])
                        and not (_valid(values.get('minimal')) and _contains_source(values['minimal']))):
                    github_echo_services.append(service)
            for variant in VARIANTS:
                vals = [
                    normalize(erow.get(prompt_cols.get((service, variant), ''), ''))
                    for service in LLM_KEYS
                    if _valid(erow.get(prompt_cols.get((service, variant), ''), ''))
                ]
                variant_unique_counts[variant] = len(set(vals))

        minimal_unique = variant_unique_counts.get('minimal', 0)
        judge_unique = variant_unique_counts.get('judge', 0)
        if minimal_unique and judge_unique <= minimal_unique * .75:
            judge_effect = 'judge_induced_convergence'
        elif minimal_unique and judge_unique > minimal_unique:
            judge_effect = 'judge_increased_variation'
        else:
            judge_effect = 'limited_judge_change'

        rows.append({
            **base.to_dict(),
            'disagreement_shape': _shape(clusters, n_services),
            'n_exact_form_clusters': len(clusters),
            'largest_cluster_size': sizes[0] if sizes else 0,
            'dominant_form_share': dominant_share,
            'dominant_cluster_services': '; '.join(dominant_services),
            'singleton_outlier_service_count': len(outliers),
            'singleton_outlier_services': '; '.join(outliers),
            'api_group_dominance': api_dom,
            'local_group_dominance': local_dom,
            'mt_group_dominance': mt_dom,
            'llm_group_dominance': llm_dom,
            'service_group_pattern': service_pattern,
            'has_mt_llm_split': mt_llm_split,
            'wikipedia_relationship': wikipedia_relationship,
            'prompt_stable_service_count': len(stable_services),
            'prompt_stable_services': '; '.join(stable_services),
            'prompt_sensitive_service_count': len(sensitive_services),
            'prompt_sensitive_services': '; '.join(sensitive_services),
            'github_source_echo_service_count': len(github_echo_services),
            'github_source_echo_services': '; '.join(github_echo_services),
            'minimal_unique_llm_forms': minimal_unique,
            'judge_unique_llm_forms': judge_unique,
            'judge_effect': judge_effect,
        })

    result = pd.DataFrame(rows)
    projection_path = os.path.join(eval_dir, 'translation_projection_language_metrics.csv')
    if os.path.exists(projection_path):
        projection = read_csv_file(projection_path)[[
            'language_code', 'mean_pairwise_distance', 'max_pairwise_distance'
        ]].rename(columns={
            'mean_pairwise_distance': 'mean_embedding_distance',
            'max_pairwise_distance': 'max_embedding_distance',
        })
        result = result.merge(projection, on='language_code', how='left')
    rationale, rationale_detail = _load_rationale_signals(data_dir, term_slug)
    if not rationale.empty:
        result = result.merge(rationale, on='language_code', how='left')
    signal_cols = [c for c in result.columns if c.startswith('register_') or c in STANCE_PATTERNS]
    result[signal_cols] = result[signal_cols].fillna(0)

    out_path = os.path.join(eval_dir, 'disagreement_patterns.csv')
    result.to_csv(out_path, index=False)
    rationale_detail_path = os.path.join(eval_dir, 'rationale_signal_detail.csv')
    rationale_detail.to_csv(rationale_detail_path, index=False)
    print(f'Saved {len(result)} rows x {len(result.columns)} columns -> {out_path}')
    print(f'Saved {len(rationale_detail)} rationale rows -> {rationale_detail_path}')
    print(result['disagreement_shape'].value_counts().to_string())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--term', default='Digital Humanities')
    args = parser.parse_args()
    build_patterns(get_data_directory_path(), args.term)


if __name__ == '__main__':
    main()
