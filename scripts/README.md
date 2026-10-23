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

## Recommended Run Order

The full workflow has required stages, review pauses, and optional analytical rebuilds:

| Order | Stage | Run when | Main result |
| --- | --- | --- | --- |
| 1 | `language_metadata.generate_language_codes` | Building or refreshing the shared inventory | Canonical language, script, family, and identifier CSVs |
| 2 | Metadata review scripts | Family sources or assignments changed | Reviewed family metadata layer |
| 3 | Candidate generation | Adding a disciplinary term or deliberately regenerating model outputs | Direct-service and prompt-service candidate files |
| 4 | Notebook 02 | Candidate files changed | Automated review signals and coverage summaries |
| 5 | Candidate review | Automated signals changed or a new term needs review | Saved exclusions and corrections |
| 6 | Analysis scripts and notebooks 03-08 | Reviewed candidates changed | Agreement, disagreement, embedding, and rationale artifacts |
| 7 | `generate_search_terms.py` | Review and disagreement artifacts are complete | Deduplicated, reviewed search strings |
| 8 | Private GitHub retrieval | Search strings changed | Retrieved GitHub objects and overlap tables |
| 9 | Post-search relevance review and notebook 09 | Retrieval finished | Reviewed relevance and visibility findings |

Steps 1-2 are shared across terms. Repeat steps 3-9 for each new source term. Existing committed candidates allow readers to begin at step 4 or later without rerunning paid or nondeterministic services.

## Common Commands

Run commands from the repository root:

```bash
python -m scripts.language_metadata.generate_language_codes
python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" \
  --variant minimal fluent_speaker github_searcher judge
python -m scripts.review.build_review_explorer_data --term "Digital Humanities"
python -m scripts.analysis.explore_confidence_within_variant --term "Digital Humanities"
python -m scripts.analysis.explore_confidence_across_variants --term "Digital Humanities"
python -m scripts.analysis.explore_disagreements --term "Digital Humanities"
python scripts/generate_search_terms.py --term "Digital Humanities"
```

Each package README documents its internal order, inputs, outputs, and optional maintenance tasks.

## Search-Term Export

Run `generate_search_terms.py` after candidate review and disagreement analysis. The exporter applies saved exclusions and corrections, deduplicates normalized forms while preserving provenance, and writes the term-level search artifacts under `datasets/translated_terms/{term_slug}/search_terms/`. Review those terms before passing them to the private GitHub retrieval project.

```bash
python scripts/generate_search_terms.py --term "Digital Humanities"
```

Rebuild the export whenever `manual_exclusions.csv`, disagreement analysis, or term corrections change.
