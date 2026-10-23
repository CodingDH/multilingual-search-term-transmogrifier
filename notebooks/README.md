# Analysis Notebooks

The numbered notebooks document the analytical sequence used to inspect the language metadata, generated candidate terms, review decisions, model rationales, and GitHub retrieval results. They analyze committed artifacts; they are not the entry point for generating new translations or issuing new GitHub searches.

For the article-specific subset, figures, and reported claims, see the [*Translation to Transmogrification* artifact guide](../docs/papers/translation-to-transmogrification/README.md).

## Notebook Sequence

| Notebook | Purpose | Principal inputs |
| --- | --- | --- |
| [`01_language_exploration.ipynb`](01_language_exploration.ipynb) | Reconstructs the language-code inventory, identifier reconciliation, family metadata, source provenance, and population evidence. | Metadata files and reviewed language-code tables |
| [`02_translation_overview.ipynb`](02_translation_overview.ipynb) | Describes pipeline coverage, error logs, scripts, automated review signals, manual exclusions, and language-level error recurrence. | Reviewed language metadata, direct-service outputs, LLM outputs, and evaluation tables |
| [`03_baseline_services.ipynb`](03_baseline_services.ipynb) | Compares prompt-invariant sources, including Wikipedia and dedicated translation services, with attention to coverage, overlap, and search-ready terms. | Direct-service and community-source outputs |
| [`04_prompt_services.ipynb`](04_prompt_services.ipynb) | Examines coverage, output shape, exact agreement, source retention, and stability across LLM services and prompt conditions. | Prompt-service translation outputs and reviewed exclusions |
| [`05_translation_projection.ipynb`](05_translation_projection.ipynb) | Models exact-form disagreement and judge effects, then records supplementary embedding, input-selection, and robustness analyses. | Reviewed translations, disagreement tables, and cached embeddings |
| [`06_rationale_classification.ipynb`](06_rationale_classification.ipynb) | Analyzes rationale availability, length, lexical density, service and prompt classification, distinctive vocabulary, collocations, and translation-rationale alignment. | Paired English-language rationales and cached classifier artifacts |
| [`07_definitional_patterns.ipynb`](07_definitional_patterns.ipynb) | Preserves exploratory topic models and overlapping rules for studying how rationales define and authorize *Digital Humanities*. | Rationale corpus and Notebook 06 analytical artifacts |
| [`08_disagreement_patterns.ipynb`](08_disagreement_patterns.ipynb) | Synthesizes rationale claims, disagreement evidence, and cases selected for close reading. | Disagreement analysis and rationale-derived signals |
| [`09_search_results.ipynb`](09_search_results.ipynb) | Evaluates reviewed search terms, GitHub retrieval, overlap, relevance, vocabulary-source ablation, and counterfactual visibility. | Reviewed search vocabulary and committed GitHub search-result tables |

## Analytical Dependencies

The numeric prefixes give the recommended reading order, but the notebooks do not form a single script that must always be executed end to end. Notebooks 01 through 04 establish the reviewed metadata and translation evidence used by Notebooks 05 through 08. Notebook 09 depends on the reviewed search vocabulary and search-result artifacts produced outside the notebooks.

Notebooks 01–06 and 09 contain the principal analyses used in the forthcoming article. Notebook 05 also retains embedding experiments intended primarily for comparative follow-up work. Notebooks 07 and 08 preserve exploratory analyses that are useful for further research but are not required to reproduce the article's central claims.

## Running the Notebooks

Install the repository dependencies from `requirements.txt` and use a Python kernel associated with that environment. The notebooks resolve the project root without relying on an absolute local path, so they can be opened from the repository or from the `notebooks/` directory.

Most cells read committed CSV, JSON, cache, and model-output artifacts. They do not need API credentials unless a cell explicitly invokes a generation or retrieval script. New candidate generation and GitHub collection belong to the scripts documented in [`scripts/`](../scripts/README.md), where environment variables and external-service requirements are described.

Executed notebooks can be large because they retain tables and interactive chart specifications. When a notebook renderer cannot display one of these files, the source remains available here and its article-facing visual outputs can be inspected in the paper's [`figures/publication/`](../docs/papers/translation-to-transmogrification/figures/publication/) directory.


