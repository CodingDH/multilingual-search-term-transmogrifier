# Analysis

These scripts compare reviewed candidates and rationales without treating agreement as linguistic validation.

| Module | Purpose |
| --- | --- |
| `compare_translations.py` | Shared normalized-string comparison helpers |
| `explore_confidence_within_variant.py` | Agreement among services within a prompt |
| `explore_confidence_across_variants.py` | Prompt sensitivity within services |
| `explore_disagreements.py` | Reviewed translation-comparison records |
| `build_disagreement_explorer_data.py` | Browser disagreement matrix |
| `build_disagreement_patterns.py` | Multidimensional disagreement summaries |
| `rationale_classifier.py` | Rationale service and prompt classifiers |
| `build_language_population_metadata.py` | Population evidence used in later analyses |
| `build_historic_reference_convergence.py` | Historic Digital Humanities comparison |

```bash
python -m scripts.analysis.explore_confidence_within_variant --term "Digital Humanities"
python -m scripts.analysis.explore_confidence_across_variants --term "Digital Humanities"
python -m scripts.analysis.explore_disagreements --term "Digital Humanities"
python -m scripts.analysis.build_disagreement_explorer_data --term "Digital Humanities"
python -m scripts.analysis.build_disagreement_patterns --term "Digital Humanities"
```

## Required Order

The first two confidence stages can run once candidate generation is complete. Run the remaining disagreement stages after candidate review decisions have been saved:

1. `explore_confidence_within_variant.py` writes `confidence_scores.csv` and `confidence_summary.csv`.
2. `explore_confidence_across_variants.py` writes per-service prompt-stability detail and summaries.
3. `explore_disagreements.py` combines reviewed candidates into `disagreement_analysis.csv`.
4. `build_disagreement_explorer_data.py` joins disagreement, confidence, rationale-length, and service data for notebook analysis.
5. `build_disagreement_patterns.py` creates the multidimensional pattern table used by notebook 05 and downstream summaries.

Rerun steps 1-2 when candidate files or pairing rules change. Rerun steps 3-5 when candidate files, exclusions, corrections, or pairing rules change. `compare_translations.py` is a shared helper and should not be run directly.

## Independent And Optional Builders

| Script | Run when | Downstream use |
| --- | --- | --- |
| `build_language_population_metadata.py` | Refreshing CLDR/Wikidata population evidence or rebuilding from cache | Notebooks 01, 02, and 09 |
| `build_historic_reference_convergence.py` | Reconstructing the December 2022 and November 2024 comparisons | Notebook 02 |
| `rationale_classifier.py` | Imported while rerunning the rationale-classification notebook | Notebook 06 |

Population and historic builders do not depend on the disagreement sequence. Rationale classification should follow candidate review so excluded or unpaired responses are handled consistently.

All generated analytical CSVs live under the relevant term's `evaluation/` directory unless a script documents a shared metadata destination.
