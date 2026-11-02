# Search-Term Data

This directory records the transition from reviewed translations to GitHub queries and preserves non-identifying aggregate retrieval summaries.

The complete raw GitHub endpoint exports were produced by the private companion `searching_for_DH` collection workflow and are not distributed in this repository. `build_search_relevance_review.py` reads those repository, issue, and account exports, deduplicates their objects, and writes non-identifying overlap summaries here. The object-level review queue and reviewed decisions are written to the configured external search-data directory under `search_terms/digital_humanities/` because their representative samples contain repository and account metadata.

The collector and complete exports are intentionally withheld to avoid releasing reusable infrastructure for further bulk aggregation or surveillance of GitHub users and scholarly communities. This creates a documented limit on end-to-end reproduction. The repository instead preserves reviewed search terms, aggregate overlap summaries, and the analytical code that consumes those artifacts. Researchers interested in responsible methodological comparison or collaboration may contact the principal investigator through the repository's contact information.

## Canonical Sequence

| File | Status | Row unit | Role |
| --- | --- | --- | --- |
| `grouped_translated_terms.csv` | Generated intermediate | One normalized query grouped across language/source rows | Output of `scripts/generate_search_terms.py` before final browser review. |
| `reviewed_grouped_translated_terms.csv` | Reviewed artifact | One reviewed query-language grouping | Canonical query input to GitHub search. |
| `reviewed_candidate_term_provenance.csv` | Provenance bridge | One query-to-candidate-observation link | Joins reviewed queries to candidate history without embedding ID lists in query rows. |
| `reviewed_candidate_term_export_metadata.json` | Export metadata | One reviewed export snapshot | Stores selection mode, export ID, hashes, and provenance coverage counts. |
| `search_result_relevance_review.csv` | Private generated review queue | One productive query | Stored externally with representative retrieval samples and provisional assessments. |
| `search_result_relevance_reviewed.csv` | Private reviewed artifact | One productive query | Stored externally as the canonical downstream relevance decisions. |
| `search_result_term_overlap_edges.csv` | Generated intermediate | One term-to-term overlap edge | Shared GitHub objects and overlap measures. |
| `search_result_overlap_summary.csv` | Generated summary | One corpus-level row | Global retrieval multiplicity totals. |

Files under `older_datasets/` are superseded review snapshots and are not read by the current workflow.

## Grouped Search-Term Columns

| Column | Meaning |
| --- | --- |
| `search_term_id` | Stable identifier for one source concept and normalized GitHub search string. |
| `search_term` | Deduplicated query string. |
| `natural_language` | Semicolon-separated or serialized language-code provenance associated with the term. A term can map to multiple languages. |
| `counts` | Number of contributing candidate records before grouping. |
| `directionality` | Display/search direction selected for the grouped term (`ltr` or `rtl`). |
| `search_term_source` | Services and prompt conditions that supplied the term. |
| `comparison_status` | Upstream candidate-comparison status carried into the grouped record. |
| `keep_term` | Final search-term review decision. Read as a boolean. |
| `directionality_conflict` | Whether contributing language rows disagreed on directionality; present in the generated queue. |
| `ltr_languages`, `rtl_languages` | Language provenance used to resolve directionality conflicts; present in the generated queue. |

The reviewed query CSV retains `search_term_id` and the human-readable query and
review columns. Candidate provenance is normalized into the bridge rather than
stored as comma-separated lists.

| Bridge column | Meaning |
| --- | --- |
| `search_term_id` | Stable reviewed search-string identifier. |
| `transmogrifier_id` | Supporting candidate observation. |

The metadata JSON stores `selection_mode`, optional `selection_as_of`,
generation time, row counts, and SHA-256 hashes for both
tabular artifacts, including the number of reviewed queries linked to source
observations. Run `generate_search_terms.py --enrich-reviewed` after each
browser export to rebuild and validate this normalized provenance package.

The reviewed file can contain more rows than a newly generated queue when a review reconciles or carries forward terms from earlier reviewed snapshots. Treat the reviewed file as the canonical search input and document any future merge rather than assuming row counts must match.

## Private Relevance-Review Columns

The following schema documents the private files used by the analysis; those files are not distributed in this repository.

### Query identity and provenance

| Column | Meaning |
| --- | --- |
| `search_term_key` | Normalized key used to join search results and preserve reviews. |
| `coding_dh_date` | Date of the retrieval-review snapshot. Downstream processing uses the latest completed row for each normalized term key. |
| `search_term` | Display form of the query. |
| `natural_language` | Language rows associated with the query. |
| `language_mapping_rows` | Number of language-to-term mappings represented. |
| `source_translation_count` | Number of translation records contributing the term. |
| `search_term_ids` | Reviewed search-string provenance. Candidate-observation detail remains in the upstream bridge. |
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

`*_samples` columns contain serialized representative GitHub records for phrase repositories, topic repositories, issues, pull requests, users, and organizations. The corresponding `exclusive_*_samples` columns contain up to five examples per group that were retrieved by this term and no other productive query. These fields make sample-based review possible without embedding every retrieved object in the queue.

| Column | Allowed values / meaning |
| --- | --- |
| `term_assessment` | Legacy compatibility field. Current reviews use `not_assessed` rather than deciding whether a term is an authoritative translation. |
| `translation_review` | `no_issue_identified` or `possible_translation_error`; a review signal rather than a definitive linguistic judgment. |
| `exclude_from_translation_analysis` | Whether the generated form should also be omitted from translation-level analysis. This is separate from retrieval handling. |
| `retrieval_assessment` | `mostly_relevant`, `mixed`, or `mostly_irrelevant`. |
| `review_decision` | `retain`, `retain_track`, or `exclude`. |
| `reviewer_notes` | Free-text evidence and rationale. |
| `review_status` | Whether the assessment is `reviewed` or `unreviewed`; reviewer type is not encoded. |

The current file contains a sample-based audit produced through AI-assisted classification and subsequent human confirmation. It is not a manual reading of every retrieved GitHub object. `retain_track` means the term remains in downstream counts while its relevance remains analytically visible.

## Temporal Selection

Candidate generation is append-preserving. Each source observation has a
`transmogrifier_id`, and the provenance bridge records which observations
support each reviewed `search_term_id`. Export metadata identifies the selected
historical view and verifies the reviewed and bridge artifacts with hashes.
Routine exports may use the latest observations; historical exports can use an
`as_of` cutoff or a separately reviewed selection. The private relevance-review
CSV remains the binding decision layer for downstream GitHub expansion and
preserves its own `coding_dh_date` when decisions change.

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
