# Transmogrifier Scripts

Scripts for building multilingual metadata, generating candidate terms, constructing review artifacts, and analyzing the results across 881 project language-code rows. Historical filenames and columns retain the word `translation`, but the repository treats their outputs as candidates rather than validated translations.

## Structure

```text
scripts/
  experiment/         - Metadata and candidate-term generation
  exploration/        - Review datasets and analytical artifacts
  utils.py            - Shared utilities (see below)
```

### `utils.py` — Shared utilities

| Function | Purpose |
| --- | --- |
| `get_data_directory_path` / `set_data_directory_path` | Locate and persist the datasets/ root path |
| `read_csv_file` | Safe CSV loader with error handling |
| `get_language_family` | Map a language code to its broad family name |
| `detect_dominant_script` / `detect_script_disagreement` | Script-level analysis for translation comparison |
| `is_placeholder_rationale` | Returns `True` for literal placeholder strings such as `"No rationale provided"` or `"N/A"` that LLMs return instead of real reasoning |
| `enforce_translation_rationale_pairing` | Nulls out the unpaired side of any LLM translation ↔ rationale mismatch (translation-without-rationale or rationale-without-translation) in a DataFrame; called automatically by `load_variant_df` so all downstream code receives clean data |

## Generation Target

Candidate generation targets all **881 language-code rows** in `language_codes_comprehensive.csv`, built by combining registry, community, and localization metadata via `experiment/generate_language_codes.py`. The four non-language sentinel codes (`und`, `zxx`, `mis`, `mul`) are excluded before the final CSV is written; everything in the committed comprehensive file is part of the target set.

| Source | Coverage |
| --- | --- |
| Unicode CLDR 48.2 + v45 supplement | Core localization metadata, scripts, directionality, official status, and retained historical CLDR rows |
| LOC ISO 639-2 | Bibliographic ISO language inventory |
| Wikimedia | Active Wikipedia projects as community infrastructure evidence |
| SIL ISO 639-3 | English names for codes CLDR does not name cleanly |
| ISO 639-5 / Glottolog | Family metadata and reconciliation, not additional translation-target rows |

Most ancient, extinct, or low-resource languages will produce no results from direct MT services, but LLMs return translations for many of them. The `in_wikimedia`, `in_iso639_2`, and `modern_language` columns let downstream analysis filter to any subset.

## Prompt Variant Testing

LLM services are tested with four prompt strategies to evaluate the effect of different prompting approaches on translation quality:

| Variant | What it tests |
| --- | --- |
| `minimal` | Baseline — bare instruction, no context |
| `fluent_speaker` | Whether requesting rationale in the target language deepens translation quality |
| `github_searcher` | Whether search-corpus framing shapes translation choices |
| `judge` | Synthesis — aggregates all unique translations from prior variants and direct services |

The first three variants are independent, directly comparable conditions. The `judge` runs last and is a synthesis step rather than a comparison condition: it receives all unique translations produced by the other variants and services, deduplicated by value with agreeing sources grouped, and produces a best-answer translation. See `experiment/README.md` for full details.

## Usage

**Build/refresh the language list:**

```bash
cd scripts/experiment
python generate_language_codes.py
```

**Generate translations (standard pipeline, minimal prompt):**

```bash
cd scripts/experiment
python generate_translations.py
```

**Run prompt variant testing:**

```bash
cd scripts/experiment
python generate_translation_prompts.py
```

Select individual variants or "ALL" from the interactive menu. When "ALL" is chosen, variants run in order: `minimal` → `fluent_speaker` → `github_searcher` → `judge`. The judge requires the other three to have completed first.

**Refresh notebook 02 historic reference tables:**

```bash
python scripts/exploration/build_historic_reference_convergence.py --term "Digital Humanities"
```

This reads `historic_materials/translated_dh_terms.csv` and writes `historic_*.csv` outputs to `datasets/translated_terms/digital_humanities/evaluation/`. It supports the historic-reference section of notebook 02.
