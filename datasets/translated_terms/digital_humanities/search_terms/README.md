# Search-Term Data

This directory records the transition from reviewed translations to GitHub queries and then to term-level retrieval assessment.

The complete raw GitHub endpoint exports were produced by the private companion `searching_for_DH` collection workflow and are not distributed in this repository. `build_search_relevance_review.py` reads those repository, issue, and account exports, deduplicates their objects, and writes the compact review and overlap files documented here. The `*_samples` columns are representative records for review; they are not the complete raw result corpus.

The collector and complete exports are intentionally withheld to avoid releasing reusable infrastructure for further bulk aggregation or surveillance of GitHub users and scholarly communities. This creates a documented limit on end-to-end reproduction. The repository instead preserves reviewed search terms, derived counts, overlap summaries, representative samples, and the analytical code that consumes those artifacts. Researchers interested in responsible methodological comparison or collaboration may contact the principal investigator through the repository's contact information.

## Canonical Sequence

| File | Status | Row unit | Role |
| --- | --- | --- | --- |
| `grouped_translated_terms.csv` | Generated intermediate | One normalized query grouped across language/source rows | Output of `scripts/generate_search_terms.py` before final browser review. |
| `reviewed_grouped_translated_terms.csv` | Reviewed artifact | One retained query and its provenance | Canonical input to GitHub search. |
| `search_result_relevance_review.csv` | Generated review queue | One productive query | Representative retrieval samples and provisional assessments. |
| `search_result_relevance_reviewed.csv` | Reviewed artifact | One productive query | Canonical downstream relevance decisions. |
| `search_result_term_overlap_edges.csv` | Generated intermediate | One term-to-term overlap edge | Shared GitHub objects and overlap measures. |
| `search_result_overlap_summary.csv` | Generated summary | One corpus-level row | Global retrieval multiplicity totals. |

Files under `older_datasets/` are superseded review snapshots and are not read by the current workflow.

## Grouped Search-Term Columns

| Column | Meaning |
| --- | --- |
| `search_term` | Deduplicated query string. |
| `natural_language` | Semicolon-separated or serialized language-code provenance associated with the term. A term can map to multiple languages. |
| `counts` | Number of contributing translation records before grouping. |
| `directionality` | Display/search direction selected for the grouped term (`ltr` or `rtl`). |
| `search_term_source` | Services and prompt conditions that supplied the term. |
| `comparison_status` | Upstream translation-comparison status carried into the grouped record. |
| `keep_term` | Final search-term review decision. Read as a boolean. |
| `directionality_conflict` | Whether contributing language rows disagreed on directionality; present in the generated queue. |
| `ltr_languages`, `rtl_languages` | Language provenance used to resolve directionality conflicts; present in the generated queue. |

The reviewed file can contain more rows than a newly generated queue when a review reconciles or carries forward terms from earlier reviewed snapshots. Treat the reviewed file as the canonical search input and document any future merge rather than assuming row counts must match.

## Relevance-Review Columns

### Query identity and provenance

| Column | Meaning |
| --- | --- |
| `search_term_key` | Normalized key used to join search results and preserve reviews. |
| `search_term` | Display form of the query. |
| `natural_language` | Language rows associated with the query. |
| `language_mapping_rows` | Number of language-to-term mappings represented. |
| `source_translation_count` | Number of translation records contributing the term. |
| `directionality`, `comparison_status` | Upstream metadata retained for interpretation. |

### Retrieval counts

| Column | Meaning |
| --- | --- |
| `repository_count` | Unique repositories after combining phrase and topic channels. |
| `repository_phrase_count` | Repositories returned directly by phrase search. |
| `repository_topic_count` | Repositories reached through matching GitHub topics. |
| `issue_count`, `pull_request_count` | Unique issue-search objects separated by GitHub object type. |
| `user_count`, `organization_count` | Account-search results separated by account type. |
| `total_unique_results` | Unique objects across the six displayed groups for this term. |
| `exclusive_result_count` | Objects retrieved by this term and no other reviewed term. |
| `shared_with_other_terms_count`, `shared_with_other_terms_pct` | Retrieval overlap with other terms. |
| `covered_by_english_count` | Objects also reached by the English query. |
| `new_beyond_english_count` | Objects not reached by the English query. This is novelty, not relevance. |
| `top_overlapping_terms` | Highest-overlap alternative queries. |

### Samples and review

`*_samples` columns contain serialized representative GitHub records for phrase repositories, topic repositories, issues, pull requests, users, and organizations. They make sample-based review possible without embedding every retrieved object in the queue.

| Column | Allowed values / meaning |
| --- | --- |
| `term_assessment` | `credible_dh_term`, `ambiguous_or_broad`, or `suspect_translation`. |
| `retrieval_assessment` | `mostly_relevant`, `mixed`, or `mostly_irrelevant`. |
| `review_decision` | `retain`, `retain_track`, or `exclude`. |
| `reviewer_notes` | Free-text evidence and rationale. |
| `review_status` | Whether the assessment is `reviewed` or `unreviewed`; reviewer type is not encoded. |

The current file contains a sample-based audit produced through AI-assisted classification and subsequent human confirmation. It is not a manual reading of every retrieved GitHub object. `retain_track` means the term remains in downstream counts while its relevance remains analytically visible.

## Overlap Edge Columns

| Column | Meaning |
| --- | --- |
| `source_term_key`, `target_term_key` | Normalized query pair. |
| `shared_result_count` | Number of GitHub objects retrieved by both terms. |
| `jaccard_overlap` | Intersection divided by union of both result sets. |
| `source_coverage`, `target_coverage` | Directional share of each term's result set covered by the other term. |

Overlap does not establish semantic equivalence. GitHub tokenization, broad phrases, shared repositories, and topic expansion can all produce overlap.

## Search Limitations

- GitHub endpoints do not all apply identical matching behavior.
- Phrase-search and topic expansion are analytically distinct retrieval paths.
- A productive term can be linguistically incorrect but retrieve many objects.
- A credible low-resource term can return nothing because the scholarship is absent from GitHub, indexed under another term, or hosted elsewhere.
- Language provenance belongs to the query; it does not guarantee that every retrieved object is written in that language.
