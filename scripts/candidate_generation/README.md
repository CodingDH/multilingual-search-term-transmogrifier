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
