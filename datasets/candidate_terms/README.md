# Translated Terms

This directory organizes candidate outputs by normalized source-term slug. Each term directory can contain direct-service outputs, prompt-service outputs, evaluation artifacts, and reviewed search terms.

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

## Historical Row Identity

The initial completed corpus contains one row per `language_code` x `term_source`
pair in most candidate-output files. Future reruns append observations instead of
replacing those rows. Each observation receives a `transmogrifier_id` derived
from its term, language, service, prompt, model, timestamp, and generated
output. `language_code` is a project identifier whose provenance is documented
under `../metadata_files/`. Some services return no candidate for a row; the
row is retained with a blank service field so coverage failures remain
measurable.

New candidate observations store their project timestamp as
`coding_dh_generated_at_utc`. This field records when Coding DH received the
candidate, not when a provider created a model or when a linguistic form first
entered use. The historical `coding_dh_date` column remains a supported legacy
alias and is normalized by the candidate-version loader.

The original Wikipedia artifact is sparse because it contains only language rows for which the initial interlanguage-link lookup produced a label. Future Wikipedia refreshes append complete dated language snapshots, including blank candidates where no label is present. This makes additions, edits, and removals observable without rewriting the original sparse observations.

Routine analysis uses the latest observation for each term-language-service-
prompt identity. Historical analysis can instead request an `as_of` cutoff,
all observations, or a reviewed selection of `transmogrifier_id` values. Search
term exports record the IDs of the selected observations so downstream GitHub
retrieval remains tied to a specific candidate snapshot.

Code that consumes service outputs should use
`scripts.candidate_generation.translation_versions.load_translation_versions`
rather than reading these CSVs directly with `pandas.read_csv`. A direct read
returns every preserved observation after a refresh, while routine analysis
normally requires `mode="latest"`.

Errors remain in separate log files and are never inserted into successful
model-output CSVs. `error_observation_id` identifies one dated failure event;
the repository does not store a `latest_error_observation_id` or treat an
earlier failure as a permanent current status.

## Do Not Treat Outputs as Ground Truth

Values in `*_translated_term` are observed service responses or community labels. They have not been globally validated by speakers of all represented languages. Review decisions and automated signals record analytical judgments about whether outputs should enter later stages, not universal claims about linguistic correctness.
