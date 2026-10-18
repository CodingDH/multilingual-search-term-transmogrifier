# Multilingual Search Term Transmogrifier

The Multilingual Search Term Transmogrifier is part of [*Coding DH*](https://github.com/CodingDH), a research project developing data-driven social histories of scholarly coding communities at scale. *Coding DH* uses platform data to study where these communities form, how their practices and relationships change over time, and how scholarly coding becomes visible or remains difficult to identify across disciplinary and linguistic contexts.

This repository provides the project's multilingual term-discovery pipeline, which generates, compares, reviews, and prepares candidate search terms for scholarly concepts so that *Coding DH* can identify relevant activity beyond English-language terminology. The resulting datasets preserve language metadata, source provenance, competing forms, model rationales, review decisions, and retrieval evidence rather than allowing multilingual discovery to depend on a single translation service or language standard.

The pipeline grew from an effort to identify communities associated with *Digital Humanities* across languages on GitHub. That term remains the first completed case study and the source of the historic materials in this repository, but more terms will be added in the future.

## Why "Transmogrifier"?

The generated terms are not treated as authoritative translations. Depending on the language, source, model, and prompt, an output may be a translation, transliteration, borrowing, paraphrase, disciplinary reinterpretation, repetition of the source phrase, or fabricated form. *Transmogrification* names this broader process without treating model fluency or agreement among services as linguistic validation.

The pipeline therefore preserves alternatives and their provenance rather than collapsing them into a single ground-truth vocabulary. Its outputs are research artifacts and possible search terms that require critical review.

## Pipeline

For each source term, the pipeline:

1. Builds on a shared multilingual metadata layer while retaining disagreements among registries and community sources.
2. Collects prompt-invariant terminology from Wikipedia and dedicated translation services.
3. Generates candidate terms and rationales with local and API-hosted language models.
4. Compares independent prompting conditions with a later judge condition that receives prior candidates as evidence.
5. Surfaces suspicious outputs through automated signals and browser-based review interfaces.
6. Analyzes coverage, failures, exact agreement, scripts, rationales, embeddings, and disagreement structure.
7. Produces reviewed search-term datasets and evaluate what those terms retrieve from platforms such as GitHub.

The current implementation uses Wikipedia, Google Translate, EasyNMT, Lingvanex, eight LLM services, and four prompt conditions. These are documented as components of a dated experiment rather than assumed to be a permanent or exhaustive service set.

## Terms and Data

Term-specific data live under `datasets/translated_terms/{term_slug}/`. A complete term directory can contain:

```text
{term_slug}/
├── direct_services/   # Community and dedicated translation-service outputs
├── prompt_services/   # LLM outputs and rationales by prompt condition
├── evaluation/        # Automated signals, comparisons, and review decisions
└── search_terms/      # Grouped and reviewed terms prepared for retrieval
```

*Digital Humanities* is currently the complete reference corpus. Other disciplinary terms are present at earlier stages of generation and will adopt the same structure as their translation, review, and retrieval stages are completed. See [Term datasets](datasets/translated_terms/README.md) for current status.

## Research Outputs

This shared repository supports multiple publications and analyses. Publication-specific documentation identifies the relevant repository code and datasets.

| Research output | Status | Documentation |
| --- | --- | --- |
| *From Translation to Transmogrification: Exploring Multilingual Metadata and the Limits of AI-Augmented Translation in Digital Humanities* | Forthcoming article | [Translation to Transmogrification](docs/papers/translation-to-transmogrification/README.md) |
| Comparative analysis of multilingual translation and rationale embeddings | In development | [Multilingual translation embeddings](docs/papers/multilingual-translation-embeddings/README.md) |

## Documentation

| Resource | Contents |
| --- | --- |
| [Project documentation](docs/README.md) | Shared methods, publication materials, and documentation boundaries |
| [Datasets](datasets/README.md) | Data layers, canonical files, provenance, missing values, and regeneration boundaries |
| [Language metadata](datasets/metadata_files/README.md) | Language codes, scripts, families, population evidence, and service support |
| [Term datasets](datasets/translated_terms/README.md) | Completed and developing source-term corpora |
| [Digital Humanities dataset](datasets/translated_terms/digital_humanities/README.md) | The first complete direct-service, LLM, evaluation, and search-term corpus |
| [Scripts](scripts/README.md) | Metadata construction, candidate generation, review, analysis, and search preparation |
| [HTML review interfaces](html_files/README.md) | Browser interfaces and the files each one reads and writes |
| [Exclusion strategy](docs/exclusion_strategy.md) | Automated signals, manual decisions, and analysis-specific exclusions |

## Repository Structure

```text
multilingual-search-term-transmogrifier/
├── notebooks/          # Analyses of metadata, outputs, disagreement, and retrieval
├── scripts/
│   ├── experiment/     # Metadata and candidate-term generation
│   ├── exploration/    # Review datasets and analytical artifacts
│   └── utils.py        # Shared loading, normalization, script, and family helpers
├── datasets/
│   ├── metadata_files/ # Shared language, family, population, and support metadata
│   └── translated_terms/
│       └── {term_slug}/
│           ├── direct_services/
│           ├── prompt_services/
│           ├── evaluation/
│           └── search_terms/
├── historic_materials/ # Dated precursor datasets for the initial case study
├── html_files/         # Browser-based review interfaces
├── figures/            # Shared and publication-specific figures
└── docs/               # Project methods and publication documentation
```

## Installation

The repository was tested with Python 3.13.3. Dependencies can be installed with `pip` in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The language-metadata build requires Node.js/npm when downloading pinned CLDR packages for the first time. Candidate generation additionally requires provider credentials and, for local models, [Ollama](https://ollama.com/).

## Regenerating Pipeline Artifacts

The principal stages are:

1. Build shared language metadata with `scripts/experiment/generate_language_codes.py`.
2. Apply the documented family-label and language-level review process.
3. Generate direct-service and LLM candidates for one or more source terms.
4. Build automated review and disagreement artifacts with `scripts/exploration/`.
5. Review outputs through the interfaces documented in [html_files/README.md](html_files/README.md).
6. Generate reviewed search terms with `scripts/generate_search_terms.py`.
7. Evaluate retrieval results for the relevant term or comparative study.

See [Scripts](scripts/README.md) for commands and dependencies. Rebuilding generated stages can change results because APIs, hosted models, service support, web resources, and local model versions change over time. Tagged releases preserve the data used for reported analyses.

## Credentials

Generation scripts retrieve credentials through the `apikey` package. Required keys depend on the enabled services:

```bash
python -c "import apikey; apikey.save('CODING_DH_GOOGLE_TRANSLATE_CREDENTIALS', 'path/to/credentials.json')"
python -c "import apikey; apikey.save('CODING_DH_OPENAI_KEY', 'your-key')"
python -c "import apikey; apikey.save('CODING_DH_OPENAI_PROJECT_ID', 'your-project-id')"
python -c "import apikey; apikey.save('CODING_DH_OPENAI_ORGANIZATION_ID', 'your-organization-id')"
python -c "import apikey; apikey.save('CODING_DH_CLAUDE_KEY', 'your-key')"
python -c "import apikey; apikey.save('CODING_DH_GEMINI_KEY', 'your-key')"
python -c "import apikey; apikey.save('CODING_DH_DEEPSEEK_KEY', 'your-key')"
```

Set a descriptive Wikimedia User-Agent before rebuilding language metadata:

```bash
export WIKIMEDIA_USER_AGENT="multilingual-language-metadata-research/1.0 (contact: your-email@example.org)"
```

Store the path to this repository's `datasets/` directory under the repository-specific key:

```bash
python -c "import apikey; apikey.save('MULTILINGUAL_SEARCH_TERM_TRANSMOGRIFIER_DATA_DIRECTORY', '/absolute/path/to/datasets')"
```

Notebook 09 also reads the GitHub retrieval datasets produced by `searching_for_DH`. Store that external directory separately:

```bash
python -c "import apikey; apikey.save('SEARCHING_FOR_DH_DATA_DIRECTORY', '/absolute/path/to/search/datasets')"
```

Local generation requires Ollama and the model versions documented in [scripts/experiment/README.md](scripts/experiment/README.md).

## Responsible Use

The pipeline produces candidate terms rather than verified translations. A populated response does not demonstrate linguistic accuracy, and agreement among models or services may reflect shared training data, prompt framing, borrowing, or repetition rather than independent confirmation. Expected script use provides another useful review signal, but a term written in the anticipated script can still be fabricated, misleading, or inappropriate for the relevant language community. Automated signals should therefore be understood as ways to prioritize inspection, not as substitutes for linguistic judgment. Human review decisions should remain distinguishable from those automated assessments.

Responsible reuse also requires preserving the provenance attached to each candidate. Publications and derived datasets should identify the source term, language identifier, service or model, prompt condition, review status, and repository snapshot associated with the result. Researchers should retain competing forms and documented disagreements when those differences matter to the analysis rather than presenting the pipeline's preferred candidate as settled terminology. Consultation with language experts and relevant communities remains necessary before generated terms are described as established usage, used to characterize a community, or incorporated into public-facing multilingual metadata.

## Citing the Repository

Repository-level citation metadata will be added with the first versioned public release. Until then, cite the repository URL together with the commit hash or release tag used for the analysis.
