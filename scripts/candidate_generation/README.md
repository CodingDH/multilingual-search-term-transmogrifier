# Candidate Generation

This package generates multilingual candidate terms and rationales from direct translation services, Wikipedia, hosted LLMs, and local Ollama models. A populated response is not treated as proof of linguistic validity.

| Module | Purpose |
| --- | --- |
| `generate_translations.py` | Main service orchestrator and output writer |
| `generate_translation_prompts.py` | Run the four prompt conditions |
| `translation_prompts.py` | Prompt templates, service labels, and judge evidence formatting |
| `translation_services.py` | Direct-service and model clients |
| `data_processing.py` | Parse and normalize service responses |
| `log_errors.py` | Record and clean service error logs |

```bash
python -m scripts.candidate_generation.generate_translations
python -m scripts.candidate_generation.generate_translation_prompts
```

The first three prompt conditions generate candidates independently. The judge runs afterward with distinct candidates from those prompts, direct services, and Wikipedia. Outputs are written under `datasets/translated_terms/{term}/`. Regeneration can differ as models, APIs, and upstream services change, so preserve prompt, model, date, and repository-commit provenance.

## Before Running

1. Build or load `datasets/metadata_files/language_codes_comprehensive.csv`.
2. Configure the data directory and credentials described in the repository README.
3. Start Ollama and install the documented local models if local services are enabled.
4. Decide whether the run is a new experiment or an intentional regeneration of an existing term. Existing API outputs should not be overwritten casually because model behavior changes over time.

## Recommended Order

`generate_translations.py` is the reproducible command-line entry point. Supply independent prompts before `judge`:

```bash
python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" \
  --variant minimal fluent_speaker github_searcher judge
```

Large runs can be divided by infrastructure while preserving the same variant order:

```bash
python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" --ollama-only \
  --variant minimal fluent_speaker github_searcher judge

python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" --api-only \
  --variant minimal fluent_speaker github_searcher judge
```

`generate_translation_prompts.py` provides the older interactive interface to the same prompt experiment. Use either that interface or the explicit CLI command above, not both for the same run. The judge requires prior candidate files and must remain last.

## Output Order

Direct-service and Wikipedia files are prompt invariant and live under `direct_services/`. LLM outputs live under `prompt_services/{variant}/`. Error logs are written separately so explicit failures remain distinguishable from populated but questionable candidates.

After generation, run notebook 02 before building the browser review dataset. Notebook 02 creates the automated review signals consumed by `scripts.review.build_review_explorer_data`.
