# Prompt-Service Outputs

This directory preserves raw and parsed LLM outputs for eight services across the project's prompt conditions.

## Current Design

Services:

- API-hosted: Claude, DeepSeek, Gemini, and OpenAI.
- Local through Ollama: Gemma, Llama, Mistral, and Qwen.

Current prompt conditions:

| Variant | Role |
| --- | --- |
| `minimal` | Independent candidate generation with no system persona. |
| `fluent_speaker` | Independent candidate generation with a multilingual-scholar framing and rationale requested in the target language. |
| `github_searcher` | Independent candidate generation framed as constructing multilingual GitHub queries. |
| `judge` | Dependent synthesis condition shown candidates from prior prompts, direct services, and Wikipedia. |

Files follow `{service}_{variant}_translations.csv`. Each current file normally contains 881 language rows. The filename preserves the requested translation task, but the stored rows are treated as candidate outputs. The judge is not an independent generation trial; it receives evidence generated earlier in the pipeline.

Future reruns append observations rather than replacing prior rows, so file
length is no longer a stable coverage measure. Use the version loader's default
`latest` view for the current 881-language grid, or request `selected`, `as_of`,
or `all_history` explicitly. `transmogrifier_id` identifies one historical
service-prompt-language observation.

## Legacy Files

`{service}_expert_persona_translations.csv` belongs to a superseded prompt scheme. These files are retained for provenance but are excluded from the current four-condition analysis. Do not combine them with `fluent_speaker` without an explicit historical comparison.

## Column Families

Each file is a service-local observation log. It contains common observation
keys and fields belonging to the service named in the filename. The generation
pipeline may use a cumulative in-memory frame, but foreign-service and baseline
columns are not copied into the persisted source file. Select fields by name.

| Column pattern | Meaning |
| --- | --- |
| `language_code`, `language_name`, `term_source` | Row identity and requested source phrase. |
| `transmogrifier_id` | Deterministic identifier for one dated term-language-service-prompt observation. Identical content observed later receives a different ID. |
| `service`, `prompt_variant`, `model_identifier` | Explicit context used for historical selection and comparison. |
| `coding_dh_date` | UTC time at which Coding DH observed and saved the response. |
| `{service}_translated_term` | Parsed candidate term used by downstream loaders. The stable column name does not imply validation. |
| `{service}_translation_rationale` | Parsed rationale. Generated explanation, not verified reasoning. |
| `{service}_translation` | Raw or less-normalized candidate payload retained by the service wrapper. |
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
| `generation_temperature`, `generation_top_p`, `generation_max_output_tokens`, `generation_settings_source` | Request settings and their provenance where recorded. |

Prompt-invariant candidates remain in `../direct_services/`; current family
metadata remains in the reviewed metadata tables; and manual decisions remain
in `../evaluation/manual_exclusions.csv`. The judge's supplied evidence is
preserved in its service-specific user prompt rather than copied as foreign
candidate columns.

Not every service exposes every metadata field. Blank timing or token fields are expected for providers that do not return them or for incomplete requests.

Load these files through
`scripts.candidate_generation.translation_versions.load_translation_versions`.
Its `latest`, `selected`, `as_of`, and `all_history` modes prevent preserved
historical rows from being mistaken for simultaneous service outputs.

## Candidate/Rationale Pairing

Raw files preserve what the service returned. Downstream loading uses `enforce_translation_rationale_pairing()` so candidate-only and rationale-only cells can be excluded consistently from analyses requiring both. The function retains its established technical name. The raw values remain here for audit. Notebook 02 reports pairing failures separately.

## Interpretation

- A nonblank parsed term is evidence that the response passed the parser, not evidence of linguistic validity.
- Prompts, models, and provider-level deployment can all shape outputs.
- Model names and hosted implementations are versioned evidence. A current API rerun may not reproduce the saved response.
- Judge outputs must not be counted as independent votes because their prompt contains prior candidates.
