# Multilingual Translation Embeddings: Study Guide

**Status:** In development.

This planned follow-up study uses the Multilingual Search Term Transmogrifier's shared corpus to examine the geometric structure of candidate translations and rationales. It is intentionally separated from the first article's artifact guide so that embedding experiments can evolve without changing that article's evidentiary scope.

## Planned Scope

- multilingual translation and rationale embeddings;
- exact-form agreement compared with semantic proximity;
- normalized means, medoids, and leave-one-service-out sensitivity;
- prompt and model variation within languages;
- neighborhood, family-spread, and hub-assignment stability;
- projection sensitivity and the distinction between analytical distances and visual layouts; and
- comparison across additional disciplinary terms as those corpora become complete.

## Current Repository Starting Points

| Artifact | Role |
| --- | --- |
| `notebooks/05_translation_projection.ipynb` | Translation agreement, dispersion, centroid/medoid sensitivity, and prompt/model comparisons |
| `notebooks/06_rationale_classification.ipynb` | Rationale representations and service/prompt signatures |
| `notebooks/07_definitional_patterns.ipynb` | Exploratory semantic and definitional patterns |
| `notebooks/08_disagreement_patterns.ipynb` | Multidimensional disagreement synthesis and close-reading cases |
| `datasets/translated_terms/` | Completed and pilot term corpora |

## Reproducibility Note

The follow-up paper should receive its own tagged release once its term inventory, model choices, robustness analyses, and publication figures are finalized. Until then, results in these notebooks are development analyses rather than fixed publication claims.
