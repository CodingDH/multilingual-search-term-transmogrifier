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

Term-specific data live under `datasets/candidate_terms/{term_slug}/`. A complete term directory can contain:

```text
{term_slug}/
├── direct_services/   # Community and dedicated translation-service outputs
├── prompt_services/   # LLM outputs and rationales by prompt condition
├── evaluation/        # Automated signals, comparisons, and review decisions
└── search_terms/      # Grouped and reviewed terms prepared for retrieval
```

*Digital Humanities* is currently the complete reference corpus. Other disciplinary terms are present at earlier stages of generation and will adopt the same structure as their candidate-generation, review, and retrieval stages are completed. See [Term datasets](datasets/candidate_terms/README.md) for current status.

### Recording Transmogrifications Over Time

In the future, we might rerun existing experiments to capture changes in generated terminology or model behavior over time. Therefore, candidate-term files are append-preserving historical sources. Each row contains a dated observation with a unique `transmogrifier_id` derived from its source term, language code, service, prompt condition, model identifier, observation timestamp, and named service output. Two identical visible responses observed at different times therefore remain separate evidence.

To ensure that we can identify the latest observation for a given source term, language, service, and prompt condition, we provide a helper function
`scripts.candidate_generation.translation_versions.load_translation_versions` with `mode="latest"`; `selected`, `as_of`, and `all_history` support reviewed or longitudinal analysis. The identifier applies to generated candidate
observations, not to the language registry. Language metadata continues to use `language_code` and `project_language_code` as stable entity keys.

## Research Outputs

This shared repository supports multiple publications and analyses. Publication-specific documentation identifies the relevant repository code and datasets.

| Research output | Status | Documentation |
| --- | --- | --- |
| *From Translation to Transmogrification: Exploring Multilingual Metadata and the Limits of AI-Augmented Translation in Digital Humanities* | Forthcoming article | [Translation to Transmogrification](public_docs/papers/translation-to-transmogrification/README.md) |
| Comparative analysis of multilingual translation and rationale embeddings | In development | [Multilingual translation embeddings](public_docs/papers/multilingual-translation-embeddings/README.md) |

## Documentation

| Resource | Contents |
| --- | --- |
| [Project documentation](public_docs/README.md) | Shared methods, publication materials, and documentation boundaries |
| [Datasets](datasets/README.md) | Data layers, canonical files, provenance, missing values, and regeneration boundaries |
| [Language metadata](datasets/metadata_files/README.md) | Language codes, scripts, families, population evidence, and service support |
| [Candidate-term datasets](datasets/candidate_terms/README.md) | Completed and developing source-term corpora |
| [Digital Humanities dataset](datasets/candidate_terms/digital_humanities/README.md) | The first complete direct-service, LLM, evaluation, and search-term corpus |
| [Scripts](scripts/README.md) | Metadata construction, candidate generation, review, analysis, and search preparation |
| [HTML review interfaces](html_files/README.md) | Browser interfaces and the files each one reads and writes |
| [Exclusion strategy](public_docs/exclusion_strategy.md) | Automated signals, manual decisions, and analysis-specific exclusions |

## Repository Structure

```text
multilingual-search-term-transmogrifier/
├── notebooks/          # Analyses of metadata, outputs, disagreement, and retrieval
├── scripts/
│   ├── language_metadata/   # Language inventory construction and curation
│   ├── candidate_generation/# Direct-service and LLM candidate generation
│   ├── review/              # Review queues, signals, and saved decisions
│   ├── analysis/            # Agreement, disagreement, and rationale analysis
│   ├── publication/         # Publication-specific figure builders
│   └── utils.py        # Shared loading, normalization, script, and family helpers
├── datasets/
│   ├── metadata_files/ # Shared language, family, population, and support metadata
│   └── candidate_terms/
│       └── {term_slug}/
│           ├── direct_services/
│           ├── prompt_services/
│           ├── evaluation/
│           └── search_terms/
├── historic_materials/ # Dated precursor datasets for the initial case study
├── html_files/         # Browser-based review interfaces
├── figures/            # Shared and publication-specific figures
└── public_docs/        # Project methods and publication documentation
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

1. Build shared language metadata with `scripts/language_metadata/generate_language_codes.py`.
2. Apply the documented family-label and language-level review process.
3. Generate direct-service and LLM candidates for one or more source terms.
4. Build automated review artifacts with `scripts/review/` and disagreement artifacts with `scripts/analysis/`.
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

Local generation requires Ollama and the model versions documented in [scripts/candidate_generation/README.md](scripts/candidate_generation/README.md).

## GitHub Collection Access and Privacy

The `searching_for_DH` repository and the full GitHub data-collection pipeline are not public. Although the workflow queries publicly accessible GitHub records, releasing a reusable bulk collector and complete raw exports could facilitate additional aggregation, monitoring, or mass surveillance of users and scholarly communities. This repository therefore documents the search methodology and provides non-identifying aggregate artifacts needed to understand the reported analysis without distributing the complete collection infrastructure, raw corpus, or object-level retrieval-review files.

This restriction marks a deliberate limit on end-to-end reproducibility rather than an accidental omission. Researchers interested in responsible reuse, methodological comparison, or collaboration may contact the principal investigator through the contact information associated with this repository. Requests will be considered in relation to research purpose, privacy, data minimization, and GitHub's terms of service.

## Responsible Use

Outputs in this repository are candidate search terms, not verified translations. Coverage, agreement across services, and conformity with an expected script describe properties of the pipeline's outputs, but none independently establishes linguistic accuracy. The same form may recur because systems share training data, reproduce a common borrowing, or respond similarly to prompt framing. Conversely, a form can use the expected script while remaining fabricated, misleading, or inappropriate. Automated review signals identify outputs that warrant inspection, while recorded human decisions document how particular analyses treated them. Neither layer substitutes for linguistic expertise.

Each candidate is distributed with its source term, language identifier, service or model, prompt condition, rationale or error record, and review status. Interpretation and reuse depend on preserving this provenance and identifying the repository release or commit from which the data were drawn. Competing forms and documented disagreements remain part of the evidence and should not be collapsed into settled terminology without additional validation. Claims that a generated term represents established usage, identifies a language community, or is suitable for public-facing metadata require consultation with relevant language experts and communities.

## AI-Assisted Development Disclosure

Generative AI systems, specifically Claude and Codex, assisted with the development of code and documentation in this repository. The PI reviewed and revised all AI-assisted material and takes responsibility for the published contents. Questions about the implementation, documentation, or use of AI in the project's development should be directed to the PI.

## Citing the Repository

Repository-level citation metadata will be added with the first versioned public release. Until then, cite the repository URL together with the commit hash or release tag used for the analysis.

## Ongoing Terminology Migration

Repository terminology is being revised to avoid using *translation* as a blanket description for every generated response. The pipeline requests translations, and some outputs may be established translations, but the stored corpus also contains transliterations, borrowings, paraphrases, disciplinary reinterpretations, source-term repetitions, malformed responses, and unsupported inventions. Unless an output has been independently validated, current documentation therefore favors *candidate term*, *candidate output*, or *transmogrification*.

This migration is intentionally incremental. Renaming every file, column, notebook, and helper at once would make historical analyses difficult to reproduce and could break downstream code. Readers will consequently encounter both legacy and revised terminology while compatibility changes are tested. The following table records the working conventions and proposed implementation names.

| Legacy or expansive usage | Preferred terminology | Repository direction |
| --- | --- | --- |
| translated term | candidate term | Use in prose and new schemas unless linguistic validation establishes translation status. |
| translation output | candidate output or candidate observation | Use for a dated response from a service-model-prompt-language cell. |
| translation rationale | candidate rationale | Use for the generated explanation accompanying a candidate term. |
| translation agreement or disagreement | candidate-form agreement or disagreement | Specify whether comparison uses normalized strings, scripts, embeddings, or another measure. |
| translation error | generation error, unusable response, or automated review signal | Distinguish explicit request failures from suspicious but populated outputs. |
| translation review | candidate review | Reserve *translation validation* for review supported by relevant linguistic expertise. |
| `datasets/translated_terms/` | `datasets/candidate_terms/` | Completed; documentation and active paths now use `candidate_terms`. |
| `*_translated_term` | `*_candidate_term` | Proposed schema migration; legacy columns remain active for compatibility. |
| `*_translation_rationale` | `*_candidate_rationale` | Proposed schema migration; legacy columns remain active for compatibility. |
| `generate_translations.py` | `generate_candidates.py` | Proposed script rename after imports, notebooks, and documentation can be migrated together. |
| `translation_versions.py` | `candidate_versions.py` | Proposed helper rename; `transmogrifier_id` remains the stable observation identifier. |
| `translation_services.py` | `generation_services.py` | Proposed for the mixed service layer; descriptions of actual translation APIs will retain their established category. |
| Notebook 02: translation overview | candidate-output overview | Proposed notebook-title change after publication references are stabilized. |
| Notebook 05: translation projection | candidate-form projection | Proposed notebook-title change; embedding analyses remain valid without presuming linguistic correctness. |

The word *translation* remains appropriate when describing the requested task, dedicated translation services, translation-studies scholarship, independently validated forms, quoted source language, and historical filenames required for reproducibility. Publication titles and archived materials will not be silently rewritten.
