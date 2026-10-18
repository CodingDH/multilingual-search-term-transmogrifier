# Documentation

The Multilingual Search Term Transmogrifier is a shared research project and pipeline. Its documentation is divided between project-wide methods and publication-specific artifact guides so that the repository can support more than one paper without making the main README reproduce each article's argument.

## Shared Project Documentation

| Guide | Scope |
| --- | --- |
| [Dataset index](../datasets/README.md) | Dataset layers, evidentiary status, canonical files, and regeneration boundaries |
| [Language metadata](../datasets/metadata_files/README.md) | Language-code, script, family, population, and service-support fields |
| [Translation corpus](../datasets/translated_terms/digital_humanities/README.md) | Direct-service, prompt-service, evaluation, and search-term data |
| [Script guide](../scripts/README.md) | Generation and analytical scripts |
| [HTML review tools](../html_files/README.md) | Browser interfaces and their input/output files |
| [Exclusion strategy](exclusion_strategy.md) | Automated signals, manual review, and analysis-specific exclusions |
| [Historic materials](../historic_materials/README.md) | Dated precursor datasets from 2022 and 2024 |

## Publication Guides

Publication guides map a paper's claims to the relevant notebooks, datasets, figures, and reviewed artifacts. They do not duplicate article prose.

- [Translation to Transmogrification](papers/translation-to-transmogrification/README.md) documents the artifact subset used by the forthcoming article.
- [Multilingual translation embeddings](papers/multilingual-translation-embeddings/README.md) records the planned scope of the follow-up comparative study.

Each published paper should refer to a tagged release. This keeps the repository's shared infrastructure current while preserving the exact snapshot used for reported numbers and figures.

## Documentation Boundary

Public documentation explains how the pipeline was built, which artifacts are canonical, and how analyses can be reproduced. Article drafts, literature notes, exploratory outlines, and writing-stage findings remain local and are excluded through `.gitignore`.
