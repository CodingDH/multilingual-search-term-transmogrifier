# Dataset Guide

See [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) for the canonical column-level
schemas used across metadata, translation, evaluation, and search-term files.

This directory contains the source metadata, generated candidate terms, review artifacts, and derived analysis tables used by the Multilingual Search Term Transmogrifier. The files do not all have the same evidentiary status. Some are upstream source snapshots, some are generated model outputs, some record human or assistant review decisions, and others can be regenerated from those files.

## Dataset Layers

| Directory | Role | Canonical status | Documentation |
| --- | --- | --- | --- |
| `metadata_files/` | Language identifiers, scripts, families, service support, and population evidence | Canonical source and reviewed metadata | [`metadata_files/README.md`](metadata_files/README.md) |
| `error_logs/` | Visible service, parsing, refusal, and generation failures | Canonical run evidence; append/update with translation runs | [`error_logs/README.md`](error_logs/README.md) |
| `translated_terms/` | Direct-service and LLM outputs organized by source term | Mixed: completed Digital Humanities corpus plus pilot terms | [`translated_terms/README.md`](translated_terms/README.md) |

## Canonical Digital Humanities Path

The completed article dataset is under `translated_terms/digital_humanities/`:

```text
digital_humanities/
├── direct_services/   # Wikipedia and prompt-invariant MT outputs
├── prompt_services/   # eight LLM services by prompt condition
├── evaluation/        # review, disagreement, classifier, and embedding tables
└── search_terms/      # generated, reviewed, and retrieval-audited query terms
```

See [`translated_terms/digital_humanities/README.md`](translated_terms/digital_humanities/README.md) for the canonical files and execution order.

## Evidence Status

The following labels are used throughout the documentation:

- **Source snapshot**: downloaded or scraped upstream evidence preserved for reproducibility.
- **Raw generated output**: direct service or model response before review.
- **Generated intermediate**: reproducible table built from other committed files.
- **Reviewed artifact**: a generated table with decisions saved through an HTML reviewer or another explicit review process.
- **Frozen result**: a saved analytical result used to prevent stochastic model fitting from changing reported article values.
- **Cache**: replaceable local data used to avoid expensive recomputation.
- **Legacy**: retained only for historical provenance; not read by the current workflow.

## Identifiers and Missing Values

`language_code` is the project row identifier. It is deliberately broader than a single ISO standard and may preserve Wikimedia identifiers or historical source identifiers. Join language-level files to `metadata_files/language_codes_comprehensive_family_reviewed.csv` when reviewed family labels are required.

Read language-code columns as strings. In particular, `nan` is the valid ISO 639-3 code for Min Nan Chinese and must not be interpreted as a missing value. The project loaders use explicit string converters for this reason.

Blank translation fields mean that the source produced no usable parsed output for that row. They do not by themselves distinguish unsupported languages, request failures, refusals, parsing failures, or manual exclusions. Use the error logs and evaluation tables for that distinction.

## Primary, Reviewed, and Derived Data

For article reproduction, preserve these layers:

1. `metadata_files/language_codes_comprehensive.csv` and `language_codes_comprehensive_family_reviewed.csv`.
2. The current direct-service and four current prompt-condition files under `translated_terms/digital_humanities/`.
3. `evaluation/manual_exclusions.csv` and the generated review-signal tables.
4. `search_terms/reviewed_grouped_translated_terms.csv` and the private external retrieval-review decisions.
5. Frozen analytical results explicitly identified in the evaluation README.

Large explorer tables, chart summaries, and embedding metrics are derived and can be rebuilt, but they are committed where they support inspection without rerunning paid APIs or expensive models.

## Provenance and Limitations

- Language metadata combines CLDR, ISO/LOC, Wikimedia, SIL, Glottolog, IANA context supplied through `langcodes`, and reviewed project mappings. The metadata README records the role of each source.
- Direct translation and LLM files record service outputs, not validated linguistic ground truth.
- Rationales are generated texts. They are analyzed as model outputs and do not provide transparent access to model reasoning.
- Automated review signals identify outputs requiring attention; they do not establish correctness.
- GitHub result counts describe retrieval from a particular platform and search workflow. They are not measures of a language community's total digital or scholarly activity.
- Public GitHub records can contain account names and repository metadata. Object-level retrieval samples and review decisions remain in the private external data directory and are not distributed through this repository.

## Regeneration Overview

The repository-level [`README.md`](../README.md) gives the full workflow. In brief:

1. Build language metadata with `scripts/language_metadata/generate_language_codes.py`.
2. Build and complete the family mapping and reconciliation reviews under `scripts/review/`, then run `apply_family_review_metadata.py`.
3. Generate direct and prompt-service outputs with the scripts under `scripts/candidate_generation/`.
4. Run notebook 02, build the candidate-review dataset, and save the browser-review decisions.
5. Build disagreement artifacts under `scripts/analysis/` and rerun the relevant notebooks 03-08.
6. Build and review search terms with `scripts/generate_search_terms.py` and the HTML review tools.
7. Analyze the reviewed GitHub results in notebook 09.

See [`scripts/README.md`](../scripts/README.md) for the full command order and the distinction between required stages and optional metadata maintenance.

API outputs may change as providers update models and services. The committed files are therefore research records, not promises that rerunning a current API will reproduce identical text.
