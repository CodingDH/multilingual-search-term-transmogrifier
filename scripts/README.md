# Transmogrifier Scripts

The scripts are organized by pipeline responsibility. Historical filenames and data columns retain the word `translation`, but generated outputs remain candidate terms until reviewed.

## Structure

| Directory | Responsibility |
| --- | --- |
| [`language_metadata/`](language_metadata/README.md) | Build, reconcile, load, and maintain the shared language inventory |
| [`candidate_generation/`](candidate_generation/README.md) | Query direct services and LLM prompt conditions to generate candidate terms and rationales |
| [`review/`](review/README.md) | Build automated and browser-based review artifacts and apply saved decisions |
| [`analysis/`](analysis/README.md) | Compare candidates, measure disagreement, classify rationales, and build analytical datasets |
| [`publication/`](publication/README.md) | Generate publication-specific figures from committed results |
| `generate_search_terms.py` | Export reviewed and deduplicated terms for downstream retrieval |
| `utils.py` | Shared paths, CSV loading, family lookup, and chart export helpers |

## Pipeline Sequence

```text
language_metadata
  -> candidate_generation
  -> notebook 02 automated signals
  -> review
  -> analysis
  -> generate_search_terms.py
  -> private GitHub retrieval
  -> post-search relevance review
```

Candidate generation can require credentials, paid APIs, local Ollama models, and network access. The committed datasets support review and analysis without regenerating candidates. The separate GitHub collector is intentionally private because distributing bulk collection infrastructure and complete raw exports could facilitate additional surveillance.

## Common Commands

Run commands from the repository root:

```bash
python -m scripts.language_metadata.generate_language_codes
python -m scripts.candidate_generation.generate_translations
python -m scripts.candidate_generation.generate_translation_prompts
python -m scripts.review.build_review_explorer_data --term "Digital Humanities"
python -m scripts.analysis.explore_disagreements --term "Digital Humanities"
python scripts/generate_search_terms.py --term "Digital Humanities"
```

Each package README documents its internal order, inputs, outputs, and optional maintenance tasks.
