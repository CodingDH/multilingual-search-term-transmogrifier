# Data Dictionary

This dictionary identifies the canonical CSVs used across the pipeline. More
detailed provenance and file inventories remain in the README for each data
directory.

## Shared Conventions

| Field | Meaning |
| --- | --- |
| `language_code` | Stable project identifier. Always read as a string because `nan` is the valid ISO 639-3 code for Min Nan Chinese. |
| `language_name` | English display name associated with the project identifier. |
| `term_source` | Source phrase submitted for translation. |
| blank translation | No stored usable response. A blank is not evidence that a service lacks support unless the corresponding error or support metadata confirms that interpretation. |
| boolean fields | Stored as `True`/`False` in generated CSVs and sometimes as lowercase strings after browser review. Parse explicitly rather than relying on truthiness. |
| pipe-separated fields | Multiple registry or script values in one cell, such as `sources`, `scripts`, and `script_codes`. |
| semicolon-separated fields | Multiple service, language, or review values in one cell. |

Raw generated outputs are preserved separately from reviewed corrections and
exclusions. A populated translation is a generated candidate, not a validated
equivalent.

## Language Metadata

### Canonical files

- `metadata_files/language_codes_comprehensive.csv`: generated registry layer,
  one row per project language code.
- `metadata_files/language_codes_comprehensive_family_reviewed.csv`: the same
  rows with reviewed family fields appended. Use this file for downstream
  family analysis.

### Identity, standards, and scripts

| Column | Meaning |
| --- | --- |
| `language_code` | Stable project code and primary join key. |
| `language_name`, `local_name` | English display name and CLDR autonym where available. |
| `iso639_1`, `iso639_2_t`, `iso639_2_b` | ISO 639-1 and ISO 639-2 terminological/bibliographic equivalents where available. |
| `in_iso639_1`, `in_iso639_2`, `is_group_iso639_2` | Membership flags for the relevant ISO inventories. |
| `in_wikimedia`, `wikimedia_code` | Wikimedia project evidence and source-specific identifier. |
| `scripts`, `script_codes` | Pipe-separated writing-system names and ISO 15924 codes. |
| `primary_script`, `primary_script_code` | Primary writing system used by downstream checks. |
| `directionality`, `directionality_wikimedia` | Derived primary-script direction and separately preserved Wikimedia direction. |
| `n_scripts` | Number of scripts listed for the row. |
| `modern_language`, `is_official` | CLDR modern-use and official-language evidence. |

### Provenance, families, and interoperability

| Column | Meaning |
| --- | --- |
| `sources`, `cldr_version` | Registries contributing the row and its CLDR provenance. |
| `coding_dh_date_added`, `coding_dh_date_last_seen` | Project-level first and most recent source-attestation dates. |
| `iso639_5_direct`, `iso639_5_family` | Direct and top-level ISO 639-5 group codes. |
| `family_name`, `subfamily_name` | Initial family and direct subgroup labels. |
| `family_name_reconciled` | Pre-review ISO/Glottolog reconciliation result. |
| `project_language_code` | Explicit copy of the stable project identifier. |
| `bcp47_tag`, `bcp47_source`, `bcp47_note`, `bcp47_is_project_code` | BCP 47 normalization and provenance without overwriting the project code. |
| `service_code_candidates` | Candidate service identifiers derived from the available standards. |
| `google_nmt_code`, `google_nmt_supported` | Google Cloud Translation code and support snapshot. |
| `google_translation_llm_code`, `google_translation_llm_supported` | Google Translation LLM code and support snapshot. |

The reviewed family file adds:

| Column | Meaning |
| --- | --- |
| `family_name_reconciled_pre_review` | Reconciled value before manual review. |
| `family_name_reconciled_reviewed` | Reviewed language-to-family decision. |
| `family_review_source`, `family_review_notes` | Decision provenance and notes. |
| `family_name_analysis` | Final controlled label used for aggregate analysis. |
| `family_name_analysis_source` | Provenance for the analysis-level label. |

See [`metadata_files/README.md`](metadata_files/README.md) for upstream sources,
population tables, service-support manifests, and full field provenance.

## Translation Outputs

### Direct services

Files under `translated_terms/{term_slug}/direct_services/` preserve one named
source's output. Google Translate, EasyNMT, and Lingvanex files retain the full
language inventory; Wikipedia stores productive interlanguage labels.

| Column or pattern | Meaning |
| --- | --- |
| `language_code`, `language_name`, `term_source` | Row identity and requested phrase. |
| `{service}_translated_term` | Parsed candidate from the named source. |
| `wikipedia_translated_term` | Community-edited interlanguage label where available. |
| `term` | Pipeline-selected term in cumulative historical schemas, not an independent source. |
| `coding_dh_date` | Collection or write date. |
| `family_name` | Family label available during generation; join reviewed metadata for current analysis. |
| `exclude_*` | Historical generation flags. Current review decisions live in `evaluation/manual_exclusions.csv`. |

### Prompt services

Files under `prompt_services/` follow
`{service}_{prompt_variant}_translations.csv`. The filename supplies the service
and condition; columns are cumulative and can contain evidence from earlier
services.

| Column pattern | Meaning |
| --- | --- |
| `{service}_translated_term` | Parsed translation candidate used downstream. |
| `{service}_translation_rationale` | Parsed generated explanation. Not a record of internal reasoning or independent validation. |
| `{service}_translation`, `{service}_content` | Less-normalized or raw response payload. |
| `{service}_system_prompt`, `{service}_user_prompt` | Prompt text sent for the row. |
| `{service}_model` | Recorded provider or local model identifier. |
| `{service}_created`, `{service}_created_at` | Provider or local timestamp. |
| `{service}_finish_reason`, `{service}_stop_reason`, `{service}_done_reason` | Completion state. |
| `{service}_prompt_tokens`, `{service}_input_tokens` | Input-token usage where available. |
| `{service}_completion_tokens`, `{service}_output_tokens`, `{service}_total_tokens` | Output and total-token usage where available. |
| `{service}_*_duration`, `{service}_*_count` | Ollama timing and evaluation metrics. |
| `{service}_extracted_dictionaries` | JSON-like objects parsed from local-model output. |

The `judge` condition is dependent: its prompts contain candidates from earlier
prompts and direct sources. Do not count judge outputs as independent votes.

See the [direct-service](translated_terms/digital_humanities/direct_services/README.md)
and [prompt-service](translated_terms/digital_humanities/prompt_services/README.md)
documentation for coverage and interpretation details.

## Evaluation and Review

### `automated_review_signals.csv`

One row per language. Each `has_{signal}` boolean is paired with a
`{signal}_services` field identifying affected service-prompt outputs.

| Column group | Meaning |
| --- | --- |
| `has_missing_rationale` | Translation exists without its expected rationale. |
| `has_mixed_script`, `has_script_disagreement`, `has_any_mixing` | Within-output or cross-output script anomalies. |
| `has_romanization`, `has_transliteration_rationale` | Romanization or claimed transliteration evidence. |
| `has_source_term`, `has_language_name_term`, `has_placeholder_term` | Source retention, language-name substitution, or placeholder-like output. |
| `has_repetition_loop`, `has_unicode_escape` | Mechanical generation or serialization failures. |
| `has_extreme_term_length`, `has_short_translation` | Length-based review signals. |
| `has_refusal_rationale`, `has_placeholder_rationale` | Refusal or non-explanatory rationale language. |
| `has_unexpected_rationale_language` | Rationale language differs from the condition's expectation. |
| `automated_review_signals`, `quality_flags` | Serialized summaries of triggered checks. |
| `flag_count` | Number of triggered signal types for the language. |

Signals identify review candidates; they do not determine linguistic accuracy.

### `manual_exclusions.csv`

| Column | Meaning |
| --- | --- |
| `language_code`, `language_name` | Reviewed language. |
| `service` | Named service or decision scope such as `analysis_exclusion`, `search_exclusion`, or `term_correction`. |
| `exclude_translation` | Remove matching output from quality-filtered analysis when true. |
| `exclude_term_{variant}` | Remove the service-condition candidate from search-term generation. |
| `original_term`, `corrected_term` | Preserved output and reviewed replacement. |
| `notes` | Human review rationale. |

### `disagreement_patterns.csv`

| Column group | Meaning |
| --- | --- |
| `comparison_status`, `comparison_basis` | Exact-form comparison result and evidence basis. |
| `n_services_with_translation`, `n_services_with_rationale` | Available evidence counts. |
| `n_unique_raw`, `n_unique_normalized`, `max_edit_distance` | Conservative string-comparison measures. |
| `disagreement_shape`, `n_exact_form_clusters`, `dominant_form_share` | Cross-service exact-form structure. |
| `service_group_pattern`, `has_mt_llm_split` | Alignment among MT, API, local, and LLM source groups. |
| `wikipedia_relationship` | Wikipedia's relationship to dominant and alternative forms. |
| `prompt_stable_*`, `prompt_sensitive_*` | Within-service behavior across prompt conditions. |
| `minimal_unique_llm_forms`, `judge_unique_llm_forms`, `judge_effect` | Judge-condition change relative to independent generation. |
| `mean_embedding_distance`, `max_embedding_distance` | Supplementary representational distance, not correctness. |
| `register_*`, `claims_*`, `admits_uncertainty` | Overlapping rationale-text signals. |

See [`evaluation/README.md`](translated_terms/digital_humanities/evaluation/README.md)
for the complete evaluation inventory and normalization assumptions.

## Search Terms and Retrieval Review

### `reviewed_grouped_translated_terms.csv`

| Column | Meaning |
| --- | --- |
| `search_term` | Deduplicated reviewed query string. |
| `natural_language` | Language-code provenance associated with the query. |
| `counts` | Contributing translation records before grouping. |
| `directionality` | Display/search direction. |
| `search_term_source` | Services and prompt conditions that supplied the term. |
| `comparison_status` | Upstream translation-comparison category. |
| `keep_term` | Reviewed inclusion decision. |

### `search_result_relevance_reviewed.csv`

| Column group | Meaning |
| --- | --- |
| `search_term_key`, `search_term` | Normalized join key and display query. |
| `natural_language`, `language_mapping_rows`, `source_translation_count` | Query provenance and contributing-record counts. |
| `*_count`, `total_unique_results` | Unique GitHub objects by result type and in total. |
| `exclusive_result_count`, `shared_with_other_terms_*` | Retrieval overlap among queries. |
| `covered_by_english_count`, `new_beyond_english_count` | Novelty relative to the English query, not relevance. |
| `*_samples` | Serialized representative records for browser review. |
| `term_assessment` | Credibility of the proposed DH term. |
| `retrieval_assessment` | Relevance of sampled GitHub results. |
| `review_decision` | `retain`, `retain_track`, or `exclude`. |
| `reviewer_notes`, `review_status` | Decision rationale and review provenance. |

See [`search_terms/README.md`](translated_terms/digital_humanities/search_terms/README.md)
for overlap-edge fields, allowed review values, and GitHub search limitations.
