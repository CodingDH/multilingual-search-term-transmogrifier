# Publication Support

Publication-specific builders live here so analytical modules remain independent of article layout and export requirements.

`build_language_code_pipeline_figure.py` creates the language-metadata pipeline figure from committed metadata and review artifacts. Final numbered exports, captions, and alt text are documented under `docs/papers/translation-to-transmogrification/figures/publication/`.

Run publication builders only after their source notebooks and reviewed datasets are final:

```bash
python -m scripts.publication.build_language_code_pipeline_figure
```

Publication scripts should not be treated as upstream analytical stages. They format existing results for an article and may encode figure-specific dimensions, labels, or export paths.
