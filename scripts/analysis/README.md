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
