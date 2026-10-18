# Translated Terms

This directory organizes translation outputs by normalized source-term slug. Each term directory can contain direct-service outputs, prompt-service outputs, evaluation artifacts, and reviewed search terms.

## Corpus Status

| Directory | Status | Use |
| --- | --- | --- |
| `digital_humanities/` | Completed primary corpus | Supports the forthcoming article and the current notebooks. |
| `computational_humanities/`, `computational_social_science/`, `cultural_analytics/`, `digital_cultural_heritage/`, `digital_history/`, `humanities/`, `humanities_data_science/`, `public_history/` | Partial pilot corpora | Early or incomplete outputs retained for future comparative work; do not assume equal service or language coverage. |

The pilot directories predate the completed four-condition, eight-LLM design. Their filenames such as `ollama_translations.csv` or `second_ollama_translations.csv` do not map cleanly onto the current service-specific schema. They should not be combined with the completed corpus without a separate provenance and harmonization pass.

## Standard Term Layout

```text
{term_slug}/
├── direct_services/   # Prompt-invariant community or MT sources
├── prompt_services/   # LLM outputs separated by service and prompt
├── evaluation/        # Generated review and analytical artifacts
└── search_terms/      # Deduplicated, reviewed, and retrieval-audited terms
```

Only `digital_humanities/` currently implements the complete layout. See its [`README.md`](digital_humanities/README.md) for canonical files.

## Shared Row Identity

Most completed translation files contain one row per `language_code` x `term_source` pair. `language_code` is a project identifier whose provenance is documented under `../metadata_files/`. Some services return no translation for a row; the row is retained with a blank service field so coverage failures remain measurable.

Wikipedia is an exception: its direct-service file contains only language rows for which the interlanguage-link lookup produced a label.

## Do Not Treat Outputs as Ground Truth

Values in `*_translated_term` are observed service responses or community labels. They have not been globally validated by speakers of all represented languages. Review decisions and automated signals record analytical judgments about whether outputs should enter later stages, not universal claims about correct translation.
