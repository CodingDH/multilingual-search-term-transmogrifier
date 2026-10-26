# Appendix: LLM Prompts and Generation Settings

This appendix documents the large language models, inference settings, and prompt templates used to generate the *Digital Humanities* candidate translations analyzed in the forthcoming article. The configuration is reconstructed from the generation code and checked against model identifiers saved with the committed response files. Direct machine-translation services and Wikipedia are not included because they did not receive these prompts.

## Models and Inference Settings

| Service | Execution | Requested model | Model recorded in responses | Temperature | Top-p | Maximum output | Additional settings |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| OpenAI | Provider API | `gpt-4o` | `gpt-4o-2024-08-06` | 0 | 1 | 2,048 tokens | OpenAI Chat Completions API |
| Claude | Provider API | `claude-sonnet-4-5` | `claude-sonnet-4-5-20250929` | 0 | Provider default | 2,048 tokens | Anthropic Messages API |
| Gemini | Provider API | `gemini-2.5-flash` | `gemini-2.5-flash` | 0 | 1 | 2,048 tokens | Thinking budget 0; request timeout 60 seconds |
| DeepSeek | Provider API | `deepseek-chat` | `deepseek-v4-flash` | 0 | 1 | 2,048 tokens | OpenAI-compatible DeepSeek endpoint |
| Llama | Local via Ollama | `llama3.1:latest` | `llama3.1:latest` | 0 | 1 | 2,048 predicted tokens | Request timeout 240 seconds; 2-second delay between requests |
| Gemma | Local via Ollama | `gemma3:12b` | `gemma3:12b` | 0 | 1 | 2,048 predicted tokens | Request timeout 240 seconds; 2-second delay between requests |
| Qwen | Local via Ollama | `qwen2.5:7b` | `qwen2.5:7b` | 0 | 1 | 2,048 predicted tokens | Request timeout 240 seconds; 2-second delay between requests |
| Mistral | Local via Ollama | `mistral:7b` | `mistral:7b` | 0 | 1 | 2,048 predicted tokens | Request timeout 240 seconds; 2-second delay between requests |

`max_tokens`, `max_output_tokens`, and Ollama's `num_predict` are provider-specific names for the output limit shown above. Parameters not listed in the table were not explicitly set and therefore followed provider or local-runtime defaults. The local Llama tag included `latest`, and the repository did not record an Ollama model digest; exact replication therefore requires the historical model artifact rather than the tag alone. DeepSeek similarly resolved the requested `deepseek-chat` alias to the provider-reported `deepseek-v4-flash` identifier in the saved responses.

All services were asked to return two JSON fields:

```json
{"translated_term": "...", "translation_rationale": "..."}
```

Prompts and returned model metadata were also stored with individual response rows. The pipeline ran the three independent conditions before the judge condition so that judge prompts could incorporate their candidates.

The corpus also preserves files labeled `expert_persona` from an earlier development stage. That superseded condition was not one of the four experimental prompt conditions reported in the article.

## Template Variables

The templates below use three placeholders:

- `{term_source}`: the source disciplinary term, *Digital Humanities* in the article;
- `{language_name}`: the target language name; and
- `{language_code}`: the target ISO language code.

For Min Nan Chinese, whose ISO 639-3 code is `nan`, the pipeline expanded the code to `nan (ISO 639-3 code for Min Nan Chinese — this is a real language, not a null value)` to prevent models from interpreting it as a missing-data marker.

## Minimal Condition

No system prompt was sent. The provider-specific system field or message was omitted rather than populated with an empty string.

**User prompt**

```text
Translate '{term_source}' into {language_name} (ISO {language_code}). Reply in JSON: {"translated_term": "...", "translation_rationale": "..."}
```

## Fluent-Speaker Condition

**System prompt**

```text
You are a {term_source} scholar who speaks many languages.
```

**User prompt**

```text
Translate '{term_source}' into {language_name} (ISO code: {language_code}).

Write your rationale in {language_name}, not English. (If the target language is English, write in English.) Writing in {language_name} demonstrates deep understanding of both the language and the term.

IMPORTANT: Return ONLY valid JSON with no other text. Use this exact format:
{"translated_term": "...", "translation_rationale": "..."}
```

## GitHub-Searcher Condition

**System prompt**

```text
You are a researcher studying {term_source} communities on GitHub. Because GitHub spans many language communities, you need to translate {term_source} into multiple languages to identify relevant activity on the platform.
```

**User prompt**

```text
Translate '{term_source}' into {language_name} (ISO code: {language_code}). This translation will be used as a search query to find '{term_source}' scholarship on GitHub — including repositories, users, issues, and topics.

IMPORTANT: Return ONLY valid JSON with no other text. Use this exact format:
{"translated_term": "...", "translation_rationale": "..."}
```

## Judge Condition

The judge ran after the independent prompts. Each judge received candidate translations from the three independent LLM conditions, direct translation services, and Wikipedia where available. Identical candidate strings were grouped so that agreement among sources was visible. Sources without a translation were listed separately. The judge could select a supplied candidate or generate a new one.

**System prompt**

```text
You are a {term_source} scholar who speaks many languages.
```

**User-prompt opening**

```text
Your task is to judge the following proposed translations of the academic term '{term_source}' into {language_name} (ISO code: {language_code}), then either select the best one or generate an improved translation. Please explain your evaluation rationale.
```

The pipeline then dynamically inserted the available evidence under as many of the following headings as applied:

```text
Prompt strategies (LLM variants):
  - {variant}: {description}

LLM sources:
  - {service}: {description}

Machine translation baselines:
  - {service}: {description}

Community-curated references:
  - {resource}: {description}

Proposed translations:
  1. ({source list}): "{candidate translation}"
  2. ({source list}): "{candidate translation}"

Note: The following sources produced no translation for this language: {missing source list}.
```

**User-prompt closing**

```text
As a reminder, your goal is to judge these translations, noting where sources agreed or diverged. Then you should select the best translation or generate a new one if none are satisfactory. Please provide your reasoning for your evaluation.

IMPORTANT: Return ONLY valid JSON with no other text. Use this exact format:
{"translated_term": "...", "translation_rationale": "..."}
```

Because the judge received earlier outputs, its responses measure synthesis under supplied evidence rather than independent translation performance.

## Implementation Sources

The executable templates are defined in [`scripts/candidate_generation/translation_prompts.py`](../../../scripts/candidate_generation/translation_prompts.py). Provider calls and decoding settings are defined in [`scripts/candidate_generation/translation_services.py`](../../../scripts/candidate_generation/translation_services.py), with local request timeouts set by [`scripts/candidate_generation/generate_translations.py`](../../../scripts/candidate_generation/generate_translations.py). The committed response files are documented in [`datasets/translated_terms/digital_humanities/prompt_services/README.md`](../../../datasets/translated_terms/digital_humanities/prompt_services/README.md).
