# Prompt-Service Outputs

This directory preserves raw and parsed LLM outputs for eight services across the project's prompt conditions.

## Current Design

Services:

- API-hosted: Claude, DeepSeek, Gemini, and OpenAI.
- Local through Ollama: Gemma, Llama, Mistral, and Qwen.

Current prompt conditions:

| Variant | Role |
| --- | --- |
| `minimal` | Independent translation with no system persona. |
| `fluent_speaker` | Independent translation with a multilingual-scholar framing and rationale requested in the target language. |
| `github_searcher` | Independent translation framed as constructing multilingual GitHub queries. |
| `judge` | Dependent synthesis condition shown candidates from prior prompts, direct services, and Wikipedia. |

Files follow `{service}_{variant}_translations.csv`. Each current file normally contains 881 language rows. The judge is not an independent translation trial; it receives evidence generated earlier in the pipeline.

## Legacy Files

`{service}_expert_persona_translations.csv` belongs to a superseded prompt scheme. These files are retained for provenance but are excluded from the current four-condition analysis. Do not combine them with `fluent_speaker` without an explicit historical comparison.

## Column Families

The files are cumulative pipeline records and therefore contain columns for more than the service named in the filename. Column order varies with collection history. Select fields by name.

| Column pattern | Meaning |
| --- | --- |
| `language_code`, `language_name`, `term_source` | Row identity and requested source phrase. |
| `{service}_translated_term` | Parsed translation used by downstream loaders. |
| `{service}_translation_rationale` | Parsed rationale. Generated explanation, not verified reasoning. |
| `{service}_translation` | Raw or less-normalized translation payload retained by the service wrapper. |
| `{service}_system_prompt`, `{service}_user_prompt` | Exact prompt text sent for that service-condition row. |
| `{service}_model` | Provider model identifier recorded by the response or configured client. |
| `{service}_created`, `{service}_created_at` | Provider or local runtime timestamp. |
| `{service}_finish_reason`, `{service}_stop_reason`, `{service}_done_reason` | Provider completion state. |
| `{service}_prompt_tokens`, `{service}_input_tokens` | Input-token count where supplied. |
| `{service}_completion_tokens`, `{service}_output_tokens` | Output-token count where supplied. |
| `{service}_total_tokens` | Provider total-token count where supplied. |
| Ollama duration/count fields | Local timing and token-evaluation metadata, generally stored in nanoseconds/counts as returned by Ollama. |
| `{service}_content` | Raw local-model response text. |
| `{service}_extracted_dictionaries` | Candidate JSON-like objects parsed from local output. |
| `wikipedia_translated_term`, `gt_translated_term`, `enmt_translated_term`, `lingvanex_translated_term` | Prompt-invariant context merged into the row. |
| `family_name` | Family label at generation time; prefer reviewed metadata for aggregate analysis. |
| `exclude_*` | Historical generation flags, not the canonical manual-review decisions. |

Not every service exposes every metadata field. Blank timing or token fields are expected for providers that do not return them or for incomplete requests.

## Translation/Rationale Pairing

Raw files preserve what the service returned. Downstream loading uses `enforce_translation_rationale_pairing()` so translation-only and rationale-only cells can be excluded consistently from analyses requiring both. The raw values remain here for audit. Notebook 02 reports pairing failures separately.

## Interpretation

- A nonblank parsed term is evidence that the response passed the parser, not evidence of linguistic validity.
- Prompts, models, and provider-level deployment can all shape outputs.
- Model names and hosted implementations are versioned evidence. A current API rerun may not reproduce the saved response.
- Judge outputs must not be counted as independent votes because their prompt contains prior candidates.
