#!/usr/bin/env python3
"""Build a term-level queue for reviewing GitHub search relevance. The review separates two judgments that should not be collapsed:

1. whether the proposed search term is a credible name for Digital Humanities;
2. whether GitHub's returned results are mostly relevant to Digital Humanities.

Run this only after ``searching_for_DH/generate_search_data.py`` has finished. The generated CSV is loaded into ``html_files/search_relevance_reviewer.html``.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scripts.utils import get_data_directory_path, get_search_data_directory_path


REVIEW_COLUMNS = {
    'term_assessment': 'not_assessed',
    'translation_review': 'no_issue_identified',
    'exclude_from_translation_analysis': False,
    'retrieval_assessment': 'unreviewed',
    'decision_override': 'auto',
    'review_decision': 'unreviewed',
    'reviewer_notes': '',
    'review_status': 'unreviewed',
}

# Starting assessments for the Digital Humanities retrievals. These values are
# review suggestions, not completed reviews. A saved reviewed CSV overrides the
# defaults. Translation flags are limited to suspected errors rather than
# classifying every term's disciplinary status.
MOSTLY_RELEVANT_TERMS = {
    'digital humanities', 'humanidades digitales', 'humanités numériques',
    'humanités numeriques', 'informatica umanistica', 'humanidades digitais',
    '數字人文', '數位人文', '数字人文', 'digihumanitaaria', 'digital humaniora',
    'digitale geisteswissenschaften', 'umanistica digitale', '디지털 인문학',
    'デジタル・ヒューマニティーズ', 'digitalna humanistika',
    'digitális bölcsészet', 'dijital beşeri bilimler',
    'digitaaliset ihmistieteet', 'dijital insani bilimler',
    'humanidades dixitais', 'humanitats digitals',
}

SUSPECT_TERMS = {
    'digitäl humäns', 'buku digital', '电子文学', '人工智能文学',
    'ŋɔɔŋ ŋɔɔŋ ŋɔɔŋ ŋɔɔŋ', 'ŋaŋaŋa ŋaŋaŋaŋ', 'artes digitales',
    '數字文學', 'digitale kunst', 'humano digitais', 'budaya digital',
    'ngôn ngữ học số', 'văn học điện tử', 'digital kultur', 'dijital kultur',
    'sastra digital', 'kultural digital', 'seni budaya digital',
    'dijital insanlar', 'teknologi digital manusia', 'teknologi manusia digital',
    'teknologi sosial digital', 'teknologi digital budaya',
    'komputer sastra', 'komputer budaya digital', 'pengajian digital',
    'dijital sanatlar', 'no exact translation available', 'digital a humanities',
    'digital a humanidades', 'digitaal ŋaam', '大利石化', '数宇人文',
    'dì jì zhī shù', 'yi zhī xì shù', 'дигитални умения',
    'neh jiyaj', 'pana seme', 'kulupu suli pilin', 'sona pi jan sewi',
    'sona pi ilo', 'sona pi ilo nanpa', 'sona ilo pi toki nanpa',
    '𐓷𐓘𐓻𐓘𐓻𐓟 𐓷𐓘𐓻𐓘𐓻𐓟',
}

MOSTLY_IRRELEVANT_TERMS = SUSPECT_TERMS | {
    'nhân văn số', 'digital a humanities', 'humanities me digital',
    'im humanities digital', 'humanitas digital', 'humanitá digital',
    'humanitás digital', 'digital humanitá', 'digital humanitás',
    'digitál humanitá', 'ciencias digitales', 'insani dijital',
    'kəlmə dijital', 'kilalang digital', 'kebudayaan digital',
    'ngữ hóa kỹ thuật số', 'nhân văn kỹ thuật số', 'ubunifu wa kidijitali',
}


def _seed_reviewed_assessments(review: pd.DataFrame) -> pd.DataFrame:
    """Populate suggested Digital Humanities retrieval assessments."""
    if review.empty:
        return review
    review = review.copy()
    for index, row in review.iterrows():
        key = str(row['search_term_key']).strip().lower()
        translation_review = (
            'possible_translation_error'
            if key in SUSPECT_TERMS
            else 'no_issue_identified'
        )

        if key in MOSTLY_RELEVANT_TERMS:
            retrieval_assessment = 'mostly_relevant'
        elif key in MOSTLY_IRRELEVANT_TERMS:
            retrieval_assessment = 'mostly_irrelevant'
        else:
            retrieval_assessment = 'mixed'

        if retrieval_assessment == 'mostly_relevant':
            decision = 'retain'
            sample_finding = 'Stored samples are predominantly related to digital humanities.'
        elif retrieval_assessment == 'mostly_irrelevant':
            decision = 'exclude'
            sample_finding = 'Stored samples are predominantly unrelated to digital humanities.'
        else:
            decision = 'retain_track'
            sample_finding = 'Stored samples mix potentially relevant, ambiguous, and unrelated material.'

        audited = int(pd.to_numeric(row.get('audited_unique_result_count', 0), errors='coerce') or 0)
        coverage = float(pd.to_numeric(row.get('match_evidence_coverage_pct', 0), errors='coerce') or 0)
        observable = round(audited * coverage)
        documented = int(pd.to_numeric(row.get('documented_field_match_count', 0), errors='coerce') or 0)
        surface = int(pd.to_numeric(row.get('visible_surface_match_count', 0), errors='coerce') or 0)
        token_only = int(pd.to_numeric(row.get('token_only_match_count', 0), errors='coerce') or 0)
        unresolved = int(pd.to_numeric(row.get('unresolved_platform_match_count', 0), errors='coerce') or 0)
        if bool(row.get('match_evidence_available', False)):
            unresolved_label = 'match remained' if unresolved == 1 else 'matches remained'
            audit_finding = (
                f'The match audit found observable evidence for {observable:,} of '
                f'{audited:,} retrieved objects ({coverage:.1%}); overlapping indicators '
                f'included {documented:,} documented-field reproductions, {surface:,} '
                f'visible phrase matches, and {token_only:,} token-only matches. '
                f'{unresolved:,} {unresolved_label} unresolved.'
            )
            if bool(row.get('match_evidence_any_route_truncated', False)):
                audit_finding += ' At least one qualified route reached GitHub\'s retrieval ceiling.'
        else:
            audit_finding = 'Field-qualified match evidence was not available for this initial assessment.'
        translation_finding = (
            ' The proposed term is also flagged as a possible translation error.'
            if translation_review == 'possible_translation_error'
            else ''
        )
        action = {
            'retain': 'Initial suggestion: retain.',
            'retain_track': 'Initial suggestion: retain while tracking relevance.',
            'exclude': 'Initial suggestion: exclude these retrieved results.',
        }[decision]
        reason = ' '.join(
            [sample_finding, audit_finding, action]
        ) + translation_finding

        review.at[index, 'term_assessment'] = 'not_assessed'
        review.at[index, 'translation_review'] = translation_review
        review.at[index, 'exclude_from_translation_analysis'] = False
        review.at[index, 'retrieval_assessment'] = retrieval_assessment
        review.at[index, 'decision_override'] = 'auto'
        review.at[index, 'review_decision'] = decision
        review.at[index, 'reviewer_notes'] = reason
        review.at[index, 'review_status'] = 'unreviewed'
    return review


def _text(value, limit: int = 600) -> str:
    if pd.isna(value):
        return ''
    value = ' '.join(str(value).split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + '…'


def _read_result_files(pattern: str, result_type: str) -> pd.DataFrame:
    frames = []
    for filename in sorted(glob.glob(pattern)):
        try:
            frame = pd.read_csv(filename, low_memory=False)
        except (pd.errors.EmptyDataError, UnicodeDecodeError):
            continue
        if frame.empty or 'search_term' not in frame.columns or 'id' not in frame.columns:
            continue
        frame = frame.copy()
        frame['result_type'] = result_type
        if result_type == 'repository':
            frame['search_channel'] = (
                'topic' if Path(filename).name.startswith('repos_tagged_') else 'phrase'
            )
        else:
            frame['search_channel'] = 'phrase'
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _sample_records(frame: pd.DataFrame, result_type: str, sample_size: int) -> str:
    if frame.empty:
        return '[]'
    frame = frame.drop_duplicates('id').copy()
    if result_type == 'repository' and 'stargazers_count' in frame.columns:
        frame['_sample_order'] = pd.to_numeric(frame['stargazers_count'], errors='coerce').fillna(0)
        frame = frame.sort_values(['_sample_order', 'id'], ascending=[False, True])
    else:
        frame = frame.sort_values('id')

    records = []
    for _, row in frame.head(sample_size).iterrows():
        if result_type == 'repository':
            title = row.get('full_name', row.get('name', ''))
            description = row.get('description', '')
            stars = pd.to_numeric(row.get('stargazers_count', 0), errors='coerce')
            extra = {
                'stars': int(stars) if pd.notna(stars) else 0,
                'programming_language': _text(row.get('language', ''), 80),
                'channel': _text(row.get('search_channel', ''), 30),
            }
        elif result_type in {'issue', 'pull_request'}:
            title = row.get('title', '')
            description = row.get('body', '')
            extra = {'channel': 'phrase'}
        else:
            title = row.get('login', row.get('name', ''))
            description = row.get('bio', '')
            extra = {'channel': 'phrase'}
        records.append({
            'id': str(row.get('id', '')),
            'title': _text(title, 180),
            'description': _text(description),
            'url': _text(row.get('html_url', ''), 500),
            **extra,
        })
    return json.dumps(records, ensure_ascii=False)


def _filter_exclusive_records(
    frame: pd.DataFrame,
    result_type: str,
    exclusive_items: set[str],
) -> pd.DataFrame:
    """Return rows whose endpoint-qualified IDs occur for only one term."""
    if frame.empty:
        return frame
    qualified_ids = result_type + ':' + frame['id'].astype(str)
    return frame[qualified_ids.isin(exclusive_items)].copy()


def _join_unique(series: pd.Series) -> str:
    values = []
    for value in series.dropna().astype(str):
        for part in value.split(','):
            part = part.strip()
            if part and part.lower() != 'nan' and part not in values:
                values.append(part)
    return ', '.join(values)


def _load_match_evidence(search_dir: str, term_slug: str) -> pd.DataFrame:
    """Summarize the optional field-qualified audit for relevance review."""
    path = (
        Path(search_dir) / 'search_match_evidence' / term_slug / 'derived'
        / 'broad_search_match_evidence.csv'
    )
    columns = [
        'search_term_key', 'match_evidence_available',
        'audited_unique_result_count', 'documented_field_match_count',
        'visible_surface_match_count', 'token_only_match_count',
        'unresolved_platform_match_count', 'match_evidence_coverage_pct',
        'match_evidence_any_route_truncated',
    ]
    if not path.is_file():
        return pd.DataFrame(columns=columns)
    evidence = pd.read_csv(path, low_memory=False)
    required = {'search_term_key', 'result_key', 'match_evidence_class', 'visible_match_class'}
    if evidence.empty or not required.issubset(evidence.columns):
        return pd.DataFrame(columns=columns)

    # One object may occur through multiple broad routes. Collapse those rows
    # before counting evidence so repository topic and phrase retrieval do not
    # inflate the term-level totals.
    evidence['_documented_field'] = (
        evidence['qualified_routes'].fillna('').astype(str).ne('')
        | evidence['broad_search_route'].eq('repository_topic')
    )
    evidence['_visible_surface'] = evidence['visible_match_class'].isin(
        ['normalized_surface', 'folded_surface']
    )
    evidence['_token_match'] = evidence['visible_match_class'].isin(
        ['all_tokens', 'partial_tokens']
    )
    evidence['_unresolved'] = evidence['match_evidence_class'].eq(
        'unresolved_platform_match'
    )
    collapsed = evidence.groupby(
        ['search_term_key', 'result_key'], as_index=False
    ).agg(
        documented_field=('_documented_field', 'max'),
        visible_surface=('_visible_surface', 'max'),
        token_match=('_token_match', 'max'),
        unresolved=('_unresolved', 'min'),
        route_truncated=('any_route_truncated', 'max'),
    )
    summary = collapsed.groupby('search_term_key', as_index=False).agg(
        audited_unique_result_count=('result_key', 'nunique'),
        documented_field_match_count=('documented_field', 'sum'),
        visible_surface_match_count=('visible_surface', 'sum'),
        token_only_match_count=('token_match', 'sum'),
        unresolved_platform_match_count=('unresolved', 'sum'),
        match_evidence_any_route_truncated=('route_truncated', 'max'),
    )
    explained = (
        collapsed['documented_field']
        | collapsed['visible_surface']
        | collapsed['token_match']
    )
    coverage = (
        collapsed.assign(_explained=explained)
        .groupby('search_term_key')['_explained'].mean()
        .rename('match_evidence_coverage_pct')
        .reset_index()
    )
    summary = summary.merge(coverage, on='search_term_key', how='left')
    summary['match_evidence_available'] = True
    return summary[columns]


def build_review(
    data_dir: str,
    search_dir: str,
    term: str = 'Digital Humanities',
    sample_size: int = 5,
) -> pd.DataFrame:
    term_slug = term.lower().replace(' ', '_')
    search_terms_dir = Path(data_dir) / 'translated_terms' / term_slug / 'search_terms'
    terms_path = search_terms_dir / 'reviewed_grouped_translated_terms.csv'
    output_path = search_terms_dir / 'search_result_relevance_review.csv'
    overlap_path = search_terms_dir / 'search_result_term_overlap_edges.csv'
    overlap_summary_path = search_terms_dir / 'search_result_overlap_summary.csv'
    reviewed_path = search_terms_dir / 'search_result_relevance_reviewed.csv'

    terms = pd.read_csv(terms_path, keep_default_na=False)
    if 'keep_term' in terms.columns:
        terms = terms[terms['keep_term'].astype(str).str.lower().eq('true')].copy()
    terms['search_term_key'] = terms['search_term'].astype(str).str.lower().str.strip()
    term_summary = terms.groupby('search_term_key', as_index=False).agg(
        search_term=('search_term', 'first'),
        natural_language=('natural_language', _join_unique),
        language_mapping_rows=('natural_language', 'size'),
        source_translation_count=('counts', 'sum'),
        directionality=('directionality', _join_unique),
        comparison_status=('comparison_status', _join_unique),
    )

    root = Path(search_dir)
    patterns = {
        'repository': str(root / 'searched_repo_data' / term_slug / '*.csv'),
        'issue': str(root / 'searched_issue_data' / term_slug / '*.csv'),
        'user': str(root / 'searched_user_data' / term_slug / '*.csv'),
    }
    results = {kind: _read_result_files(pattern, kind) for kind, pattern in patterns.items()}
    kept_keys = set(term_summary['search_term_key'])
    for kind, frame in results.items():
        if frame.empty:
            continue
        frame['search_term_key'] = frame['search_term'].astype(str).str.lower().str.strip()
        results[kind] = frame[frame['search_term_key'].isin(kept_keys)].copy()

    # Use endpoint-qualified IDs so numeric IDs from different GitHub object
    # types cannot collide. Repositories reached by both phrase and topic search
    # intentionally collapse to the same material item.
    term_item_sets = {key: set() for key in kept_keys}
    for kind, frame in results.items():
        if frame.empty:
            continue
        for key, group in frame.groupby('search_term_key'):
            term_item_sets.setdefault(key, set()).update(
                f'{kind}:{item_id}' for item_id in group['id'].dropna().astype(str)
            )
    item_frequency = Counter(
        item for items in term_item_sets.values() for item in items
    )
    english_items = term_item_sets.get('digital humanities', set())

    overlap_rows = []
    nonempty_keys = [key for key, items in term_item_sets.items() if items]
    for left, right in combinations(sorted(nonempty_keys), 2):
        left_items, right_items = term_item_sets[left], term_item_sets[right]
        shared = left_items & right_items
        if not shared:
            continue
        union = left_items | right_items
        overlap_rows.append({
            'source_term_key': left,
            'target_term_key': right,
            'shared_result_count': len(shared),
            'jaccard_overlap': len(shared) / len(union),
            'source_coverage': len(shared) / len(left_items),
            'target_coverage': len(shared) / len(right_items),
        })
    overlap_edges = pd.DataFrame(overlap_rows)
    if not overlap_edges.empty:
        overlap_edges = overlap_edges.sort_values(
            ['shared_result_count', 'jaccard_overlap'], ascending=False
        )
    overlap_edges.to_csv(overlap_path, index=False)
    overlap_summary = pd.DataFrame([{
        'productive_term_count': len(nonempty_keys),
        'unique_result_count': len(item_frequency),
        'english_result_count': len(english_items),
        'result_count_beyond_english': len(set(item_frequency) - english_items),
        'exclusive_to_one_term_count': sum(value == 1 for value in item_frequency.values()),
        'shared_by_two_or_more_terms_count': sum(value >= 2 for value in item_frequency.values()),
        'shared_by_three_or_more_terms_count': sum(value >= 3 for value in item_frequency.values()),
        'shared_by_five_or_more_terms_count': sum(value >= 5 for value in item_frequency.values()),
        'maximum_term_multiplicity': max(item_frequency.values(), default=0),
        'term_result_link_count': sum(len(items) for items in term_item_sets.values()),
    }])
    overlap_summary.to_csv(overlap_summary_path, index=False)

    rows = []
    for _, metadata in term_summary.iterrows():
        key = metadata['search_term_key']
        subsets = {
            kind: frame[frame['search_term_key'].eq(key)].copy() if not frame.empty else frame
            for kind, frame in results.items()
        }
        repo = subsets['repository']
        repo_phrase = repo[repo['search_channel'].eq('phrase')] if not repo.empty else repo
        repo_topic = repo[repo['search_channel'].eq('topic')] if not repo.empty else repo
        issue_results = subsets['issue']
        if not issue_results.empty:
            pull_request_mask = (
                issue_results['pull_request.url'].notna()
                if 'pull_request.url' in issue_results.columns
                else issue_results.get('html_url', pd.Series('', index=issue_results.index))
                    .astype(str).str.contains('/pull/')
            )
            pull_requests = issue_results[pull_request_mask].copy()
            issues = issue_results[~pull_request_mask].copy()
        else:
            pull_requests = issue_results
            issues = issue_results
        account_results = subsets['user']
        if not account_results.empty and 'type' in account_results.columns:
            organization_mask = account_results['type'].astype(str).str.lower().eq('organization')
            organizations = account_results[organization_mask].copy()
            users = account_results[~organization_mask].copy()
        else:
            organizations = account_results.iloc[0:0].copy()
            users = account_results
        counts = {
            'repository_count': int(repo['id'].nunique()) if not repo.empty else 0,
            'repository_phrase_count': int(repo_phrase['id'].nunique()) if not repo_phrase.empty else 0,
            'repository_topic_count': int(repo_topic['id'].nunique()) if not repo_topic.empty else 0,
            'issue_count': int(issues['id'].nunique()) if not issues.empty else 0,
            'pull_request_count': int(pull_requests['id'].nunique()) if not pull_requests.empty else 0,
            'user_count': int(users['id'].nunique()) if not users.empty else 0,
            'organization_count': int(organizations['id'].nunique()) if not organizations.empty else 0,
        }
        total = sum(counts[key] for key in (
            'repository_count', 'issue_count', 'pull_request_count',
            'user_count', 'organization_count',
        ))
        if total == 0:
            continue
        items = term_item_sets.get(key, set())
        exclusive_items = {item for item in items if item_frequency[item] == 1}
        exclusive_repo_phrase = _filter_exclusive_records(
            repo_phrase, 'repository', exclusive_items
        )
        exclusive_repo_topic = _filter_exclusive_records(
            repo_topic, 'repository', exclusive_items
        )
        exclusive_issues = _filter_exclusive_records(
            issues, 'issue', exclusive_items
        )
        exclusive_pull_requests = _filter_exclusive_records(
            pull_requests, 'issue', exclusive_items
        )
        exclusive_users = _filter_exclusive_records(
            users, 'user', exclusive_items
        )
        exclusive_organizations = _filter_exclusive_records(
            organizations, 'user', exclusive_items
        )
        alternatives = []
        for other_key, other_items in term_item_sets.items():
            if other_key == key or not other_items:
                continue
            shared = items & other_items
            if not shared:
                continue
            alternatives.append({
                'term': other_key,
                'shared_count': len(shared),
                'current_term_coverage': len(shared) / len(items),
                'jaccard_overlap': len(shared) / len(items | other_items),
                'other_total_results': len(other_items),
            })
        alternatives.sort(
            key=lambda value: (
                value['shared_count'], value['current_term_coverage'], value['jaccard_overlap']
            ),
            reverse=True,
        )
        covered_by_english = items & english_items
        rows.append({
            **metadata.to_dict(),
            **counts,
            'total_unique_results': total,
            'exclusive_result_count': len(exclusive_items),
            'shared_with_other_terms_count': len(items) - len(exclusive_items),
            'shared_with_other_terms_pct': (
                (len(items) - len(exclusive_items)) / len(items) if items else 0
            ),
            'covered_by_english_count': len(covered_by_english),
            'new_beyond_english_count': len(items - english_items),
            'top_overlapping_terms': json.dumps(alternatives[:10], ensure_ascii=False),
            'repository_phrase_samples': _sample_records(repo_phrase, 'repository', sample_size),
            'repository_topic_samples': _sample_records(repo_topic, 'repository', sample_size),
            'issue_samples': _sample_records(issues, 'issue', sample_size),
            'pull_request_samples': _sample_records(pull_requests, 'pull_request', sample_size),
            'user_samples': _sample_records(users, 'user', sample_size),
            'organization_samples': _sample_records(organizations, 'user', sample_size),
            'exclusive_repository_phrase_samples': _sample_records(
                exclusive_repo_phrase, 'repository', sample_size
            ),
            'exclusive_repository_topic_samples': _sample_records(
                exclusive_repo_topic, 'repository', sample_size
            ),
            'exclusive_issue_samples': _sample_records(
                exclusive_issues, 'issue', sample_size
            ),
            'exclusive_pull_request_samples': _sample_records(
                exclusive_pull_requests, 'pull_request', sample_size
            ),
            'exclusive_user_samples': _sample_records(
                exclusive_users, 'user', sample_size
            ),
            'exclusive_organization_samples': _sample_records(
                exclusive_organizations, 'user', sample_size
            ),
            **REVIEW_COLUMNS,
        })

    review = pd.DataFrame(rows).sort_values(
        ['total_unique_results', 'search_term'], ascending=[False, True]
    )
    evidence_summary = _load_match_evidence(search_dir, term_slug)
    if not evidence_summary.empty:
        review = review.merge(evidence_summary, on='search_term_key', how='left')
    evidence_defaults = {
        'match_evidence_available': False,
        'audited_unique_result_count': 0,
        'documented_field_match_count': 0,
        'visible_surface_match_count': 0,
        'token_only_match_count': 0,
        'unresolved_platform_match_count': 0,
        'match_evidence_coverage_pct': 0.0,
        'match_evidence_any_route_truncated': False,
    }
    for column, default in evidence_defaults.items():
        if column not in review.columns:
            review[column] = default
        review[column] = review[column].fillna(default)
    review = _seed_reviewed_assessments(review)
    if reviewed_path.exists() and not review.empty:
        prior = pd.read_csv(reviewed_path, keep_default_na=False)
        if 'search_term_key' in prior.columns:
            available_review_columns = [column for column in REVIEW_COLUMNS if column in prior.columns]
            decisions = prior[['search_term_key', *available_review_columns]].drop_duplicates('search_term_key')
            review = review.merge(
                decisions, on='search_term_key', how='left', suffixes=('', '_prior')
            )
            prior_status = review.get(
                'review_status_prior', pd.Series('', index=review.index)
            ).eq('reviewed')
            for column in available_review_columns:
                prior_column = f'{column}_prior'
                if prior_column in review.columns:
                    review.loc[prior_status, column] = review.loc[prior_status, prior_column]
                    review = review.drop(columns=prior_column)
            for column, default in REVIEW_COLUMNS.items():
                if column not in review.columns:
                    review[column] = default
                review[column] = review[column].fillna(default).replace('', default if column != 'reviewer_notes' else '')
            review['review_decision'] = review['review_decision'].replace({
                'keep': 'retain',
                'inspect': 'retain_track',
            })
            legacy_suspect = review['term_assessment'].eq('suspect_translation')
            no_translation_review = review['translation_review'].eq('no_issue_identified')
            review.loc[
                legacy_suspect & no_translation_review, 'translation_review'
            ] = 'possible_translation_error'
            review['term_assessment'] = 'not_assessed'
            review['exclude_from_translation_analysis'] = (
                review['translation_review'].eq('exclude_from_translation_analysis')
            )
            automatic = review['decision_override'].eq('auto')
            review.loc[automatic, 'review_decision'] = review.loc[
                automatic, 'retrieval_assessment'
            ].map({
                'mostly_relevant': 'retain',
                'mixed': 'retain_track',
                'mostly_irrelevant': 'exclude',
                'unreviewed': 'retain_track',
            }).fillna('retain_track')

    search_terms_dir.mkdir(parents=True, exist_ok=True)
    review.to_csv(output_path, index=False)
    print(f'Saved {len(review):,} productive search terms -> {output_path}')
    print(f'Saved {len(overlap_edges):,} term-overlap edges -> {overlap_path}')
    print(f'Saved overlap summary -> {overlap_summary_path}')
    print(f'Load this file in html_files/search_relevance_reviewer.html')
    return review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--term', default='Digital Humanities')
    parser.add_argument('--data-dir', default=get_data_directory_path())
    parser.add_argument('--search-dir', default=None)
    parser.add_argument('--sample-size', type=int, default=5)
    args = parser.parse_args()
    search_dir = args.search_dir or get_search_data_directory_path()
    build_review(args.data_dir, search_dir, args.term, args.sample_size)


if __name__ == '__main__':
    main()
