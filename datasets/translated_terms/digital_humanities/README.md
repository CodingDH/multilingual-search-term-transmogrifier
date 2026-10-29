# Digital Humanities Translation Corpus

This is the completed corpus for the source phrase `Digital Humanities`. It contains 881 project language-code rows, direct-service evidence, eight LLM services under four current prompt conditions, review artifacts, and the search terms used for GitHub retrieval.

## Directory Map

| Directory | Row unit | Documentation |
| --- | --- | --- |
| `direct_services/` | Usually one language row per service | [`direct_services/README.md`](direct_services/README.md) |
| `prompt_services/` | One language row per service file and prompt condition | [`prompt_services/README.md`](prompt_services/README.md) |
| `evaluation/` | Varies by artifact; language, service-prompt cell, pair, or summary | [`evaluation/README.md`](evaluation/README.md) |
| `search_terms/` | One normalized query, review row, or overlap edge | [`search_terms/README.md`](search_terms/README.md) |

## Canonical Workflow Files

Use the following files when tracing the current pipeline:

1. Direct evidence: all four files in `direct_services/`.
2. LLM evidence: `{service}_{variant}_translations.csv` for the eight services and the variants `minimal`, `fluent_speaker`, `github_searcher`, and `judge`.
3. Translation review: `evaluation/automated_review_signals.csv`, `evaluation/review_explorer_data.csv`, and `evaluation/manual_exclusions.csv`.
4. Disagreement analysis: `evaluation/disagreement_analysis.csv` and `evaluation/disagreement_patterns.csv`.
5. Search-term review: `search_terms/reviewed_grouped_translated_terms.csv`.
6. Retrieval review: private external `search_terms/digital_humanities/search_result_relevance_reviewed.csv`.

The `expert_persona` prompt files and `evaluation/older_manual_exclusions.csv` are legacy artifacts. They are preserved for provenance but are not part of the current four-condition analysis.

## Missing Outputs

A blank translation means that no usable parsed translation is stored for that service-language-condition cell. Consult `../../error_logs/` for explicit failures and the evaluation tables for manual or automated exclusions. Missing values should not be converted into claims that the service cannot support the language without checking those additional sources.

## Regeneration Cost

The raw translation files are expensive and, for cloud services, potentially billable to regenerate. API and model updates can also change the output. Most reviewers should analyze the committed files rather than rerun translation generation. Derived evaluation and figure tables are safer to rebuild offline.
