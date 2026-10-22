# Exploration

Scripts for exploring translation disagreements and measuring consistency across services and prompt variants. The goal is not to determine a "correct" translation but to understand *why* disagreements occur.

> **Exclusion policy:** See [docs/exclusion_strategy.md](../../docs/exclusion_strategy.md) for the full taxonomy of automated review signals and the three-tier exclusion policy (service exploration → translation analysis → search term generation). The signals produced by `automated_review_signals.csv` and the manual review decisions in `manual_exclusions.csv` are applied differently at each tier.

## Workflow Overview

```text
experiment/    → raw translations, fully automated, no human loop
                         ↓
  Optional     build_historic_reference_convergence.py
  Historic     → historic_reference_*.csv
  Check        (used by notebook 02; historic Digital Humanities only)
                         ↓
notebooks/02_translation_overview.ipynb
               → automated_review_signals.csv   (per-language automated review signals)
                         ↓
  Review       build_review_explorer_data.py
               → review_explorer_data.csv
                         ↓
  Human        html_files/review_explorer.html
  Review       (load CSV, inspect flagged languages, mark exclusions)
               → manual_exclusions.csv   (downloaded from the HTML)
                         ↓
exploration/
  Step 1       explore_confidence_within_variant.py
               → confidence_scores.csv (LLM agreement per variant)
                         ↓
  Step 2       explore_confidence_across_variants.py
               → across_variant_detail.csv (prompt robustness per service)
                         ↓
  Step 3       explore_disagreements.py  [--exclusions manual_exclusions.csv]
               → disagreement_analysis.csv (string comparison + evidence)
                         ↓
  Step 4       build_disagreement_explorer_data.py
               → disagreement_explorer_data.csv (prompt/rationale matrix)
                         ↓
  Step 5       build_disagreement_patterns.py
               → disagreement_patterns.csv (multidimensional synthesis)
```

The **review stage** sits between raw translation (notebook 02) and the analytical pipeline. It surfaces automated review signals — missing rationales, mixed-script output, placeholder/refusal terms, script disagreements between services, source-term leakage, repetition loops, and search-safety issues — before any downstream analysis runs. Human review decisions (service exclusions) are persisted as `manual_exclusions.csv` and passed to `explore_disagreements.py`.

The **historic check** is separate from the active translation-evaluation pipeline. It supports notebook 02's discussion of the initial Digital Humanities prompt-reference artifact and should be run only when refreshing the historic-reference convergence tables.

The **search relevance review** occurs after the companion GitHub search finishes. Run `build_search_relevance_review.py`, inspect the generated queue in `html_files/search_relevance_reviewer.html`, and save the reviewed CSV before treating search-result counts as evidence of multilingual discovery.

---

## Files

### `build_language_population_metadata.py` — CLDR/Wikidata population evidence

Builds a population metadata layer without changing the 881-row language-code
inventory. Glottolog's cached ISO 639-3/Glottocode records resolve identities;
CLDR and Wikidata remain separate population observations so their coverage and
disagreement can be inspected in notebook 01.

```bash
python scripts/exploration/build_language_population_metadata.py
python scripts/exploration/build_language_population_metadata.py --cache-only
```

- **Inputs:** `language_codes_comprehensive_family_reviewed.csv`,
  `glottolog-cache/languoid.csv`, CLDR-derived `language_data` population data,
  and Wikidata `P1098` statements
- **Cache:** `wikidata_population_cache.json`
- **Evidence output:** `language_population_evidence.csv`, with one row per
  source observation and retained measure/date/scope/citation metadata
- **Resolved output:** `language_population_resolved.csv`, with CLDR preferred
  where present, Wikidata used as a fallback, and CLDR/Wikidata ratios retained
  for comparable observations

The resolver uses CLDR's base-language total when available and sums territory
rows only as a fallback. This avoids double-counting the base total together
with its regional components. Known Wikimedia/ISO code collisions are resolved
explicitly before Wikidata matching.

---

### `build_search_relevance_review.py` — Post-search term relevance queue

Builds a review table for every retained search term that returned at least one GitHub item. It reads repository, issue, and user-search CSVs from the directory stored under `SEARCHING_FOR_DH_DATA_DIRECTORY` (or supplied through `--search-dir`), deduplicates items within each term, and separates phrase-search repositories, topic-derived repositories, issues, pull requests, individual users, and organizations. GitHub returns pull requests through the issue-search endpoint and organizations through the user-search endpoint, so the builder makes those hidden endpoint groupings explicit.

The output includes up to five representative samples of each result type and two editable judgments: term credibility and retrieval relevance. For the Digital Humanities run, the builder seeds conservative Codex proposals. Downstream handling is derived rather than separately reviewed: credible terms with mostly relevant retrieval are `retain`, suspect terms with mostly irrelevant retrieval are `exclude`, and every mixed combination is `retain_track`. This preserves expansive discovery while allowing later analyses to report relevance stability. Every seeded row is marked `codex_provisional`; changing a field in the HTML reviewer marks it `human_reviewed`. A saved reviewed CSV always overrides these proposals when the queue is rebuilt. Notebook 09 removes only exclusions with `review_status == human_reviewed`; provisional exclusions remain available until confirmed.

The builder also calculates exclusive versus shared results, coverage already supplied by the English query, marginal results beyond English, and each term's strongest overlap neighbors. A separate `search_result_term_overlap_edges.csv` contains the complete weighted term-to-term network, while `search_result_overlap_summary.csv` records global unique-result and multiplicity totals for Notebook 09.

```bash
python scripts/exploration/build_search_relevance_review.py
```

- **Input:** `reviewed_grouped_translated_terms.csv` plus completed GitHub search result files
- **Output:** `search_terms/search_result_relevance_review.csv`
- **Analytical outputs:** `search_terms/search_result_term_overlap_edges.csv` and `search_terms/search_result_overlap_summary.csv`
- **Reviewer:** `html_files/search_relevance_reviewer.html`
- **Reviewed artifact:** `search_terms/search_result_relevance_reviewed.csv`

If the reviewed artifact already exists, rebuilding carries its decisions forward by normalized search term.

---

### `build_language_code_pipeline_figure.py` — Article figure: language-list history and final architecture

Builds the methods figure that combines two views of the language-code pipeline: the historical expansion from the original 185-code ISO 639-1 list to the 881-row target set, and the final separation between sources that define language rows and sources that enrich existing rows.

- **Historical sequence**: ISO 639-1 baseline → Wikimedia → LOC ISO 639-2 → CLDR 48.2 plus the retained CLDR 45 supplement
- **Current row-defining sources**: CLDR 48.2, LOC ISO 639-2, Wikimedia, and the CLDR 45 supplement
- **Metadata enrichment**: SIL ISO 639-3 names, ISO 639-5/CLDR and Glottolog family evidence, reviewed family decisions, and IANA/BCP 47 normalization through `langcodes`
- **Outputs**: `docs/papers/translation-to-transmogrification/figures/analysis/language_code_pipeline_history_and_final.{png,pdf,svg}`

```bash
python scripts/exploration/build_language_code_pipeline_figure.py
```

The historical counts reproduce the source build-up documented in notebook 01: 185 → 272 → 465 → 881. The enrichment layers do not add language rows.

---

### `translation_classifier.py` — Mixed-script and placeholder translation classifier

Classifies each translation string as `unchanged`, `stripped`, `nulled`, or `placeholder` based on script content and refusal detection. The four-action output propagates to `automated_review_signals.csv` (notebook 02), `review_explorer_data.csv`, and the HTML review explorer.

**Placeholder detection** runs first: if the text contains a refusal phrase (`"untranslatable"`, `"unable to translate"`, `"no direct translation"`, `"cannot be reliably translated"`, `"Note: ..."`, etc.) it is classified as `placeholder` and returned as `None` without entering the script-mixing logic. The regex also covers `"no confirmed/widely recognized/accepted translation"` and adverb-insertion variants like `"cannot be reliably translated"`.

**Script-mixing patterns** are then applied to remaining strings:

| Pattern | Description | Action |
| --- | --- | --- |
| A — Romanization helper | `"native_term (romanization)"` or `"native / romaji"` — model appended an unrequested Latin transliteration | `stripped` — parenthetical/slash removed, primary script kept |
| B — Character-level noise | Scripts interleaved mid-word with no structural delimiter | `nulled` — not salvageable |
| C — Colon-separated prefix | `"Digital Humanities : native_term"` — source term echoed before a colon | `stripped` — prefix discarded if it contains no dominant-script characters |
| D — Space-separated Latin prefix | `"Digital Humanities के दिशा कौशल"` — same as C but whitespace-delimited | `stripped` — leading Latin tokens stripped; non-Latin-leading strings are never touched |

Mixed-script detection uses a two-tier test designed to avoid false positives from orthographic extensions (Ossetian æ, Chuvash ă, Chechen palochka substitutes):

- **Tier 1** — ≥5 distinct minority-script characters → always flagged
- **Tier 2** — ≥3 distinct minority characters AND ≥25% of all script characters → flagged
- A single stray character representing <10% of the string is always ignored

**Script detection** delegates to `_char_script` in `scripts/utils.py`. When the `regex` package is available (the default), script identity is resolved via Unicode Script property patterns (`\p{Script=...}`) covering 55+ scripts including Thai, Lao, New Tai Lue, N'Ko, Vai, and other scripts that the old range-table missed. A `functools.lru_cache` prevents re-matching the same codepoint more than once per process. If `regex` is not installed the classifier falls back to an inline range table covering the 7 most common scripts.

**Importable API:** `curate_translation(text) → (result, action)`, `curate_df(df) → (curated_df, summary_df)`, `is_placeholder_term(text) → bool`, `is_repetition_loop(text) → bool`, `has_extreme_term_length(text, max_chars=100) → bool`, `has_unicode_escape(text) → bool`

---

### `build_review_explorer_data.py` — Review stage: build data for HTML explorer

Merges raw translations (prompt_services + direct_services) with `automated_review_signals.csv` (produced by notebook 02) into a single wide CSV for the review explorer. **No dependency on Steps 1–3** — this runs directly after notebook 02.

- **Input**: `translated_terms/{term}/evaluation/automated_review_signals.csv` + raw per-variant CSV files
- **Output**: `translated_terms/{term}/evaluation/review_explorer_data.csv`

Each row is one language. Columns include:

- Automated review signal booleans and which services triggered them: `has_missing_rationale`, `has_mixed_script`, `has_romanization`, `has_script_disagreement`, `has_source_term`, `has_placeholder_term`, `has_repetition_loop`, `has_extreme_term_length`, `has_unicode_escape`
- `review_tier`: `REVIEW_HIGH` (≥2 flags) / `REVIEW_MED` (1 flag) / `CLEAN` (0 flags)
- Per-service × per-variant term and rationale columns: `{svc}_term_{variant}`, `{svc}_rationale_{variant}`
- Non-LLM reference terms: `wikipedia_translated_term` (community reference), `gt_translated_term`, `enmt_translated_term`, `lingvanex_translated_term` (MT baselines)

Rows are sorted flagged-first so the HTML explorer opens on the cases that need attention.

```bash
python scripts/exploration/build_review_explorer_data.py --term "Digital Humanities"
python scripts/exploration/build_review_explorer_data.py --output-dir path/to/dir
```

---

### `build_historic_reference_convergence.py` — Notebook support: historic DH reference agreement

Builds the precomputed tables used by notebook 02's historic reference-convergence section. This script intentionally uses only the two CSVs in `historic_materials/` and hard-filters both to `term_source == "Digital Humanities"` by default.

The December 13, 2022 file, `translated_dh_terms.csv`, supports the first historic check: exact normalized agreement between `term` (pre-existing/Wikipedia-derived Digital Humanities term where available) and `translated_term` (historic Google Translate output). The November 2024 file, `initial_translated_terms.csv`, supports the second historic check: exact normalized agreement among `wikipedia_translated_term`, `gt_translated_term`, `enmt_translated_term`, and `openai_translated_term`.

- **Inputs**: `historic_materials/translated_dh_terms.csv`, `historic_materials/initial_translated_terms.csv`
- **Output**: `translated_terms/digital_humanities/evaluation/historic_2022_*.csv` and `historic_2024_*.csv`
- **Default term filter**: `Digital Humanities`

```bash
python scripts/exploration/build_historic_reference_convergence.py --term "Digital Humanities"
```

Generated files:

| File | Purpose |
| --- | --- |
| `historic_2022_reference_artifacts.csv` / `historic_2024_reference_artifacts.csv` | Records the historic artifact used and its row/translation counts |
| `historic_2022_reference_service_presence.csv` / `historic_2024_reference_service_presence.csv` | Counts availability of the compared fields in each artifact |
| `historic_2022_pairwise_reference_agreement.csv` / `historic_2024_pairwise_reference_agreement.csv` | Pairwise exact-normalized agreement for the relevant comparison fields |
| `historic_2022_reference_count_summary.csv` / `historic_2024_reference_count_summary.csv` | Source availability and agreement by number of historic outputs present |
| `historic_2022_all_source_convergence_summary.csv` / `historic_2024_all_source_convergence_summary.csv` | Overall convergence categories: no outputs, one output only, agree, diverge |
| `historic_2022_reference_convergence_detail.csv` / `historic_2024_reference_convergence_detail.csv` | Per-language detail tables used for examples in notebook 02 |

---

### `build_family_reconciliation_review.py` — Metadata review: unified family reconciliation queue

Builds `datasets/metadata_files/family_reconciliation_review.csv`, a unified review queue for family reconciliation. It combines ISO/Glottolog disagreement pairs from `family_reconciliation.csv` with JSON fallback language rows whose raw `family_name` assignment comes from `language_family_assignments.json` because no manual `MANUAL_LANG_TO_SET5` mapping wins.

Run this after generating and, if needed, reviewing `family_analysis_mapping.csv`; the builder annotates JSON fallback rows with that analysis-label policy so problematic labels can be corrected at the row level.

```bash
python scripts/exploration/build_family_reconciliation_review.py
```

Review tiers:

| Tier | Meaning |
| --- | --- |
| `REVIEW_HIGH` | The coherence layer flags a likely abandoned macrofamily, contested macrofamily, geographic grouping, special non-family category, or incorrect direct assignment |
| `REVIEW_MED` | No Glottolog match, Glottolog disagreed but the reconciliation decision kept the ISO/JSON family, CLDR has no ISO 639-5 hierarchy support, or a lower-confidence coherence issue needs spot-checking |
| `REFERENCE_ONLY` | Glottolog agreed or already reclassified the row; usually lower review priority |

The coherence columns (`coherence_issue`, `suggested_iso639_5`, `suggested_family_name`, `suggestion_confidence`, `suggestion_reason`) do not alter the pipeline output. They identify cases where the current JSON-derived family label may be too broad or unstable, such as abandoned macrofamilies (`Altaic`, `Niger-Kordofanian`), geographic groupings (`North American Indian languages`), or a known direct error (`frm` / Middle French).

The CSV includes editable browser-review columns: `reviewer_decision`, `reviewer_family_name`, `reviewer_iso639_5`, and `reviewer_notes`. The HTML reviewer downloads the edited file as `family_reconciliation_reviewed.csv`. When that reviewed file is saved in `datasets/metadata_files/`, run `apply_family_review_metadata.py` to apply reviewed pair decisions and JSON fallback rows where `reviewer_decision == "revise"` and `reviewer_family_name` is non-empty. This writes a reviewed metadata layer while leaving the generated language-code list unchanged.

---

### `build_family_analysis_mapping.py` — Metadata review: analysis family labels

Builds `datasets/metadata_files/family_analysis_mapping.csv`, one row per current `family_name_reconciled` value. The file proposes a `family_name_analysis` label for charts and aggregate comparison, preserving the reconciled Glottolog/review label by default. The HTML reviewer is for label-level decisions only: spelling variants, missing labels, and special non-family categories. Problematic macrofamily or geographic labels are marked `row_level_reconciliation` and passed to the unified reconciliation queue for language-level review.

```bash
python scripts/exploration/build_family_analysis_mapping.py
```

Review the generated CSV in `html_files/family_analysis_mapping_reviewer.html`. The reviewer groups rows by proposed analysis label, shows language counts, raw-family provenance, mapping actions, and sample languages, and downloads the edited file as `family_analysis_mapping_reviewed.csv`.

This file is not applied directly to `language_codes_comprehensive.csv`. It is the review surface for deciding analysis-label overrides. `apply_family_review_metadata.py` consumes the reviewed mapping later and writes the durable reviewed metadata layer, `language_codes_comprehensive_family_reviewed.csv`.

---

### `apply_family_review_metadata.py` — Metadata review: apply reviewed family layer

Applies reviewed family metadata after the language-code list has already been generated. This is the preferred way to use reviewed family names in downstream analysis without rerunning `generate_language_codes.py` or rewriting the source-build artifact.

```bash
python scripts/exploration/apply_family_review_metadata.py
```

Inputs:

| File | Purpose |
| --- | --- |
| `language_codes_comprehensive.csv` | Generated language-code/source-build artifact |
| `family_analysis_mapping_reviewed.csv` | Reviewed label policy for `family_name_analysis`; falls back to `family_analysis_mapping.csv` |
| `family_reconciliation_reviewed.csv` | Optional reviewed row/pair family corrections |

Output:

| File | Purpose |
| --- | --- |
| `language_codes_comprehensive_family_reviewed.csv` | Reviewed family metadata layer used by downstream `get_language_family()` calls when present |

The output preserves `family_name` and `family_name_reconciled_pre_review`, adds `family_name_reconciled_reviewed`, and writes `family_name_analysis` for chart/grouping work.

---

### `html_files/review_explorer.html` — Review stage: human review interface

Single-file HTML explorer for the review stage. Load `review_explorer_data.csv` via the "Load CSV" button.

**Navigation:** sidebar groups languages by review tier (REVIEW_HIGH → REVIEW_MED → CLEAN). Filter by tier, specific flag, or rationale text search.

**Card contents per language:**

- Automated review signal pills showing which flags fired and which services triggered them
- Term cluster panel — groups all 32 LLM cells (8 services × 4 variants) by normalized term; click to select
- Rationale matrix — full variants × services grid, click to expand rationale text
- Non-LLM reference terms — Wikipedia (community reference) and Google Translate / Lingvanex / EasyNMT (MT baselines)
- Service exclusions panel — toggle individual translations or per-variant rationales to exclude
- Notes field

**Outputs:**

- **Download Exclusions** → `manual_exclusions.csv` (pass to `explore_disagreements.py --exclusions`)
- **Export Selected** → `reviewed_terms.csv` (selected translation candidates with provenance)

State (selections, exclusions, notes) is persisted in `localStorage` between sessions.

---

### `explore_confidence_within_variant.py` — Step 1: Within-variant LLM agreement

For each prompt variant separately, measures how much the eight LLM services (OpenAI, Claude, Gemini, DeepSeek, Llama, Gemma, Qwen, Mistral) agree on the same translation. API services (OpenAI, Claude, Gemini, DeepSeek) and local Ollama services (Llama, Gemma, Qwen, Mistral) are both included.

- **Question**: "Within a single variant, do the LLMs converge on the same translation?"
- **Input**: `translated_terms/{term}/direct_services/` and `translated_terms/{term}/prompt_services/`
- **Output**: `translated_terms/{term}/evaluation/confidence_scores.csv`, `confidence_summary.csv`

Confidence = fraction of services agreeing on the most common translation. The four non-LLM sources — MT baselines (GT, EasyNMT, Lingvanex) and the Wikipedia community reference — are tracked separately as a prompt-invariant block.

The `family_name` column is refreshed through `get_language_family()` before export. When `language_codes_comprehensive_family_reviewed.csv` exists, this means `confidence_scores.csv` uses the reviewed `family_name_analysis` labels rather than the raw pre-review family names.

**Data quality — translation/rationale pairing.** The central function exposed by this file, `load_variant_df`, is used by every downstream notebook and script to load per-variant data. Before returning, it calls `enforce_translation_rationale_pairing` (`scripts/utils.py`), which nulls out mismatched LLM columns:

| Failure mode | Example | Action |
| --- | --- | --- |
| Translation present, rationale absent or placeholder | Model returns term but omits explanation | Translation cell → `NaN` |
| Rationale present (or placeholder string), translation absent | Model explains but returns no term | Rationale cell → `NaN` |

Placeholder rationales — literal strings such as `"No rationale provided"`, `"N/A"`, `"None"` — are detected by `is_placeholder_rationale` (`scripts/utils.py`) and treated identically to `NaN`. This enforcement happens once at load time so all callers receive consistent, paired data.

```bash
python scripts/exploration/explore_confidence_within_variant.py --term "Digital Humanities"
python scripts/exploration/explore_confidence_within_variant.py --variants minimal github_searcher
```

---

### `explore_confidence_across_variants.py` — Step 2: Cross-variant prompt robustness

For each (language × service), compares translations across the four prompt variants. Measures whether a given LLM gives the same answer regardless of how it was asked.

- **Question**: "Does the same LLM produce the same translation for 'github_searcher' and 'minimal'?"
- **Input**: `translated_terms/{term}/prompt_services/` for each variant
- **Output**: `translated_terms/{term}/evaluation/across_variant_detail.csv`, `across_variant_service_summary.csv`

Agreement rate = fraction of variants that produced the same translation for a given (language × service). Low agreement means the service is prompt-sensitive for that language; it is a convergence signal, not direct proof that no grounded answer exists.

The exported `language_family` column is resolved with `get_language_family()`, so downstream notebooks inherit the reviewed analysis-family labels when the reviewed metadata layer is present.

```bash
python scripts/exploration/explore_confidence_across_variants.py --term "Digital Humanities"
python scripts/exploration/explore_confidence_across_variants.py --variants minimal fluent_speaker github_searcher
```

---

### `explore_disagreements.py` — Step 3: Translation comparison

Assigns each language a descriptive string-comparison status after exclusions and corrections:

| Comparison status | Description |
| --- | --- |
| `exact_convergence` | At least two usable outputs remain and all match after trimming and case-folding |
| `near_form_convergence` | Outputs collapse under normalization or remain within the edit-distance tolerance |
| `substantive_variation` | Normalized outputs remain farther apart than the tolerance |
| `insufficient_comparison` | Fewer than two usable outputs remain |

Wikipedia presence, source retention, script disagreement, and rationale signals are exported as independent evidence. They do not determine the comparison status.

- **Input**: `translated_terms/{term}/evaluation/across_variant_detail.csv` + variant DataFrames (for rationale columns)
- **Output**: `translated_terms/{term}/evaluation/disagreement_analysis.csv`

The script recomputes `language_family` from `get_language_family()` during classification rather than copying a family label from `across_variant_detail.csv`. This keeps the disagreement outputs aligned with the reviewed family metadata even if an intermediate CSV was generated earlier.

**Data quality — additional pairing enforcement.** Translations are sourced from `across_variant_detail.csv` (which aggregates across all variants), while rationales are loaded from a single specified variant file. A language can therefore appear in the detail CSV with a service translation even if that service has no rationale in the chosen variant. After loading both dictionaries, any LLM service that has a translation but no valid rationale in the loaded variant is dropped from the comparison and rationale-similarity score. This is a second pass on top of the pairing already applied by `load_variant_df`.

**Manual exclusions.** Pass `--exclusions path/to/manual_exclusions.csv` (downloaded from `html_files/review_explorer.html` during the review stage) to suppress specific (language × service) translations or per-variant rationales before comparison.

```bash
python scripts/exploration/explore_disagreements.py --term "Digital Humanities"
python scripts/exploration/explore_disagreements.py --variant judge
python scripts/exploration/explore_disagreements.py --exclusions datasets/translated_terms/digital_humanities/evaluation/manual_exclusions.csv
```

---

### `build_disagreement_explorer_data.py` — Notebook support: disagreement analysis matrix

Builds `translated_terms/{term}/evaluation/disagreement_explorer_data.csv` after `explore_disagreements.py` has written `disagreement_analysis.csv`. Despite the historical script name, this file is no longer tied to a standalone HTML disagreement explorer. It is a notebook-support table consumed by notebook 06 for rationale classification and by the disagreement-pattern build.

The script merges:

- `disagreement_analysis.csv` comparison statuses and independent evidence
- per-language confidence aggregates from `confidence_scores.csv`
- service translations parsed into separate columns
- term and rationale columns for each LLM service × prompt variant, with translation/rationale pairing enforced before export
- prompt-invariant baseline terms where available

Before saving, the merged `language_family` column is refreshed from `get_language_family()` so the explorer-support table uses the reviewed analysis labels.

```bash
python scripts/exploration/build_disagreement_explorer_data.py --term "Digital Humanities"
python scripts/exploration/build_disagreement_explorer_data.py --term "Digital Humanities" --rationale-variant fluent_speaker
```

---

### `build_disagreement_patterns.py` — Step 5: multidimensional synthesis

Builds `disagreement_patterns.csv` for notebook 08. It combines the neutral comparison table with prompt-level LLM terms and English-rationale signals. The output keeps each analytical dimension separate:

- exact-form cluster shape and dominant-form share;
- API, local-LLM, MT, and cross-group alignment;
- singleton service outliers and MT/LLM dominant-form splits;
- prompt stability, GitHub source echo, and judge-prompt effects;
- Wikipedia relationship, source retention, and script evidence;
- overlapping definitional registers and rationale stances.

These fields describe patterns and select cases for review; they do not infer correctness or a single cause.

```bash
python scripts/exploration/build_disagreement_patterns.py --term "Digital Humanities"
```

---

### `rationale_classifier.py` — Notebook support: rationale genre classification

Importable helper functions for notebook 06. The classifier asks whether rationale prose reveals prompt variant or service identity after masking obvious leakage such as service names, prompt names, source-term tokens, language names, and translated terms.

This is not a standalone CLI step. Notebook 06 imports the masking and classification helpers to run the main rationale-genre analysis and masking ablations.

---

## Output Structure

All outputs are written to `translated_terms/{term}/evaluation/`:

```text
evaluation/
  historic_reference_artifacts.csv       # Historic check: input artifact summary for notebook 02
  historic_reference_service_presence.csv  # Historic check: availability of historic term/GT fields
  historic_pairwise_reference_agreement.csv  # Historic check: exact agreement between historic term and GT output
  historic_reference_count_summary.csv   # Historic check: availability/agreement by number of fields present
  historic_all_source_convergence_summary.csv  # Historic check: convergence categories
  historic_reference_convergence_detail.csv  # Historic check: per-language examples
  automated_review_signals.csv               # Review: per-language automated review signals (notebook 02); signals: missing_rationale, mixed_script, romanization, script_disagreement, source_term, placeholder_term, repetition_loop, extreme_term_length, unicode_escape
  review_explorer_data.csv        # Review: merged input for html_files/review_explorer.html
  manual_exclusions.csv           # Review: human decisions downloaded from review_explorer.html
  confidence_scores.csv           # Step 1: per-row LLM agreement scores per variant
  confidence_summary.csv          # Step 1: aggregate stats per term/variant
  across_variant_detail.csv       # Step 2: per (language × service) agreement rate
  across_variant_service_summary.csv  # Step 2: aggregate stats per service
  disagreement_analysis.csv       # Step 3: comparison status and evidence per language
  disagreement_explorer_data.csv  # Notebook support: merged comparison/confidence/rationale matrix for notebooks 06 and 08
  disagreement_patterns.csv       # Multidimensional synthesis table for notebook 08
```

---

## Shared Dependencies

- `../../scripts/utils.py`

| Function | Used by | Purpose |
| --- | --- | --- |
| `get_data_directory_path` | all scripts | Locate the datasets/ root |
| `read_csv_file` | all scripts | Safe CSV loader with error handling |
| `get_language_family` | steps 1–3 | Map language code → family name |
| `_char_script(cp)` | `translation_classifier.py`, `detect_dominant_script` | Map a Unicode code point to a script family name. Uses `regex` `\p{Script=...}` patterns covering 55+ scripts when available; falls back to a range table for the 30 most common scripts. Results are `lru_cache`'d per process. |
| `detect_dominant_script(text)` | notebook 02 (§1.8.1 script disagreement) | Return the plurality script of a translation string, ignoring punctuation and digits |
| `is_placeholder_rationale` | step 1 (`load_variant_df`), step 3 | Detect literal placeholder strings returned instead of real rationales (e.g. `"No rationale provided"`, `"N/A"`) |
| `enforce_translation_rationale_pairing` | step 1 (`load_variant_df`), review (`build_review_explorer_data.py`) | Null out unpaired translation/rationale columns for all LLM services at load time |
