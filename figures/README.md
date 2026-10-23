# Shared Figures

This directory contains diagrams and visual assets that describe the
multilingual search-term pipeline as a whole. They are kept at the repository
level because they may support multiple analyses and publications.

Paper-specific figures live with the documentation for the paper that uses
them:

- [`Translation to Transmogrification`](../docs/papers/translation-to-transmogrification/figures/)
  contains the analysis exports and numbered publication figures for the
  *Digital Humanities* case study.
- [`Multilingual Translation Embeddings`](../docs/papers/multilingual-translation-embeddings/)
  documents the planned comparative embedding study. Its figures will be
  stored with that paper when the analysis is finalized.

The SVG files in this directory are editable sources. PNG and PDF files are
rendered versions for inspection or reuse. Figures summarize pipeline behavior
and analytical results; they do not establish the linguistic validity of a
candidate term.

## Shared Asset Inventory

| Asset | Purpose |
| --- | --- |
| `translation_pipeline_methods.svg` | Compact translation-generation diagram ending with the judge prompt and preserved evidence. |
| `translation_pipeline_methods_full.svg` | Full pipeline diagram extending beyond candidate generation into review and downstream search. |
| `five_source_language_code_pipeline.svg` | Language-code source and reconciliation diagram. |
| `disagreement_classifier_slim.svg` | Compact translation-disagreement classifier diagram. |
| `disagreement_classifier_slim_with_footnote.svg` | The same compact classifier diagram with explanatory publication text included. |
| `language_pipeline_figure.png` | Raster rendering of the language-metadata pipeline figure. |
| `language_pipeline_figure.pdf` | PDF rendering of the same language-metadata pipeline figure. |

Files ending in `_full` show the broader pipeline, while the corresponding file
without that suffix presents the narrower version intended for contexts where
only the immediate method is relevant. Files ending in `_with_footnote` retain
explanatory text inside the graphic; versions without that suffix leave such
text to the surrounding caption.
