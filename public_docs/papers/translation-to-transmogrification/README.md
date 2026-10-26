# Translation to Transmogrification: Artifact Guide

This guide identifies the repository artifacts supporting the forthcoming article, *From Translation to Transmogrification: Exploring Multilingual Metadata and the Limits of AI-Augmented Translation in Digital Humanities*.

## Article Scope

The article treats multilingual candidate generation as an interpretive and infrastructural problem rather than a benchmark translation task. The article details the following:

- the historical construction of the 881-row language inventory;
- differences between community, standards, localization, and service infrastructures;
- visible failures and plausible but suspicious LLM outputs;
- prompt- and model-dependent variation;
- exact-form disagreement and judge synthesis;
- rationales as model- and prompt-specific rhetorical artifacts; and
- the opportunities and limits of using reviewed terms to search GitHub.

Embedding analyses remain available in the repository but are not required to reproduce the article's central argument. They are reserved primarily for the follow-up comparative study.

## Primary Notebooks

| Notebook | Use in the article |
| --- | --- |
| `01_language_exploration.ipynb` | Language-source history, identifier conflicts, family review, and population evidence |
| `02_translation_overview.ipynb` | Historic convergence, coverage, errors, scripts, automated review signals, and visibility categories |
| `03_baseline_services.ipynb` | Prompt-invariant sources and search-ready coverage |
| `04_prompt_services.ipynb` | Prompt variation, LLM coverage, candidate proliferation, and exact agreement |
| `05_translation_projection.ipynb` | Exact disagreement categories and judge effects used in the article; embedding sections are supplementary |
| `06_rationale_classification.ipynb` | Rationale pairing, service/prompt classifiers, distinctive vocabulary, and collocations |
| `09_search_results.ipynb` | Reviewed GitHub retrieval, vocabulary-source ablation, relevance, and counterfactual visibility |

Notebooks 07 and 08 preserve additional interpretive and disagreement experiments but are not necessary for the article's core reported results.

## Canonical Data

- `datasets/metadata_files/language_codes_comprehensive_family_reviewed.csv`
- `datasets/translated_terms/digital_humanities/direct_services/`
- `datasets/translated_terms/digital_humanities/prompt_services/`
- `datasets/translated_terms/digital_humanities/evaluation/`
- `datasets/translated_terms/digital_humanities/search_terms/reviewed_grouped_translated_terms.csv`
- reviewed retrieval artifacts documented by `datasets/translated_terms/digital_humanities/search_terms/README.md`

The article's numerical claims should be checked against these committed reviewed artifacts rather than regenerated API responses.

## Methods Appendix

The [LLM prompts and generation settings appendix](appendix_llm_prompts_and_settings.md) records the exact prompt templates, model identifiers, temperature and sampling settings, output limits, and provider-specific configuration used for candidate generation.

## Figures

Article-specific visual materials are stored with this guide:

- [`figures/analysis/`](figures/analysis/) contains notebook-generated source
  figures, exploratory charts, and titleless derivatives used to assemble the
  article figures.
- [`figures/publication/`](figures/publication/) contains the numbered figures
  and tables selected for the article. Its
  [manifest](figures/publication/README.md) records captions, alt text, source
  notebooks, and production notes.

Shared pipeline diagrams that may support more than one publication remain in
the repository-level [`figures/`](../../../figures/) directory.

