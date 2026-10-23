# Candidate-Generation Error Logs

This directory records failures made visible during candidate generation. There is one CSV per service. A row is a logged request or generation failure, not necessarily one unique language: the same language can fail under multiple prompt variants or during multiple historical runs. Plausible but incorrect outputs are not necessarily logged here and require the separate automated and manual review layers.

The current notebooks deduplicate and aggregate these records explicitly when reporting unique affected languages.

## Files

| Pattern | Service type | Prompt-specific? |
| --- | --- | --- |
| `gt_translation_errors.csv` | Google Translate | No |
| `enmt_translation_errors.csv` | EasyNMT | No |
| `lingvanex_translation_errors.csv` | Lingvanex | No |
| `wikipedia_translation_errors.csv` | Wikipedia lookup | No |
| `{service}_translation_errors.csv` for Claude, OpenAI, Gemini, DeepSeek, Llama, Gemma, Qwen, and Mistral | LLM | Yes; use `variant` |

## Common Columns

| Column | Meaning |
| --- | --- |
| `error_date` | Timestamp written by the pipeline. |
| `error_url` | Endpoint or internal operation associated with the failure. For local models this may name an Ollama operation rather than a web URL. |
| `status_code` | Pipeline status used for retry behavior. It can be an HTTP status or a project-assigned equivalent. |
| `error_message` | Raw or normalized failure message. This can contain provider text and should be treated as generated/service evidence. |
| `term_source` | Source phrase being translated, normally `Digital Humanities` in the completed corpus. |
| `language_code` | Project language identifier. Read as a string so `nan` remains Min Nan Chinese. |
| `variant` | Prompt condition for LLM errors: `minimal`, `fluent_speaker`, `github_searcher`, or `judge`. Blank or absent for prompt-invariant services. |
| `{service}_translated_term` | Partial or rejected output when one was available at failure time. Often blank. |

Column order differs slightly among services because the logs were written by service-specific wrappers. Analysis should select columns by name rather than position.

## Status Semantics

| Status | Pipeline interpretation |
| --- | --- |
| `400` | Deterministic or content-level failure, including unsupported identifiers, refusals, parse failures, and detected repetition loops. |
| `404` | Requested resource or model not found. |
| `408` | Timeout; eligible for retry. |
| `429` | Provider quota or rate limit; normally stops the service pass. |
| `500` | Unexpected API, network, or runtime failure; eligible for retry. |

These categories are operational rather than purely HTTP-semantic. Notebook 02 reclassifies messages into interpretable categories such as knowledge gaps, generic refusals, ancient/extinct-language claims, repetition loops, and API or parsing failures.

## Analytical Cautions

- Error rows measure **visible failure**, not translation inaccuracy.
- A plausible but fabricated translation can pass parsing and leave no error row.
- High raw counts can reflect repeated prompt attempts. Use unique `language_code` counts when comparing affected languages.
- A refusal can be more epistemically responsible than a non-empty fabricated output; error counts should not be treated as a model-quality ranking.
- Prompt-invariant services and LLM services have different opportunity counts. Rate calculations should use the denominators in `evaluation/service_variant_outcomes.csv`.

Files here support the current Digital Humanities analysis.
