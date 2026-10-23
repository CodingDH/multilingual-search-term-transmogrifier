# Evaluation and Review Artifacts

This directory contains generated review tables and analytical outputs derived from the Digital Humanities translation corpus. It intentionally preserves the raw service files elsewhere and adds interpretation in separate columns and files.

The directory mixes several row units. Always identify the file's unit before aggregating it: one row may represent a language, a service-prompt cell, a pair of services, a classifier feature, or a corpus-level summary.

## Artifact Map

### Review and exclusion layer

| File | Status | Row unit | Purpose |
| --- | --- | --- | --- |
| `automated_review_signals.csv` | Generated intermediate | One language | Flags suspicious translation/rationale patterns across service-prompt cells. |
| `review_explorer_data.csv` | Generated review queue | One language | Wide browser-review table combining source terms, LLM outputs, rationales, cleaned terms, and signals. |
| `manual_exclusions.csv` | Reviewed artifact | One language-service decision | Canonical saved translation, prompt-specific search, and correction decisions. |
| `older_manual_exclusions.csv` | Legacy | One language-service decision | Superseded schema containing the old `expert_persona` condition. |
| `llama_leakage_audit.csv` | Diagnostic | One flagged row | Focused audit of possible source leakage in Llama files. |

### Exact-form agreement and disagreement

| File | Status | Row unit | Purpose |
| --- | --- | --- | --- |
| `confidence_scores.csv` | Generated intermediate | Language x prompt condition | Within-condition exact normalized agreement among available LLMs. “Confidence” means convergence frequency, not correctness. |
| `confidence_summary.csv` | Generated summary | Prompt/service grouping | Aggregate within-condition convergence statistics. |
| `across_variant_detail.csv` | Generated intermediate | Language x service | Exact-form variation across prompt conditions for one service. |
| `across_variant_service_summary.csv` | Generated summary | Service | Cross-prompt stability summary. |
| `disagreement_analysis.csv` | Generated analytical table | One language | Conservative string comparison, script evidence, source retention, and rationale signals. |
| `disagreement_explorer_data.csv` | Generated review/analysis table | One language | Wide combination of disagreement evidence and all current service-prompt outputs. |
| `disagreement_patterns.csv` | Generated synthesis | One language | Multidimensional disagreement shape, group alignment, prompt behavior, and judge effect. |

### Error and coverage summaries

| File | Status | Row unit | Purpose |
| --- | --- | --- | --- |
| `service_variant_outcomes.csv` | Generated summary | Service x prompt | Possible cells, parsed translations, missing cells, and logged-error rates. |
| `service_variant_error_summary.csv` | Generated summary | Service x prompt x error category | Raw error rows, affected languages, and opportunity-normalized rates. |
| `service_variant_error_residuals.csv` | Generated analysis | Service x prompt x error category | Observed versus independence-expected errors and standardized residuals. |

### Rationale classification

| File | Status | Row unit | Purpose |
| --- | --- | --- | --- |
| `rationale_classifier_performance_frozen.csv` | Frozen result | Classification task | Canonical article metrics for service, prompt, and joint classifiers. |
| `stable_features.csv` | Generated/frozen analysis | Task x class x term | Features recurring across cross-validation folds. |
| `service_ablation_results.csv` | Generated analysis | Masking condition x class x ranked term | Vocabulary robustness when service-identifying terms are masked. |
| `variant_ablation_results.csv` | Generated analysis | Masking condition x class x ranked term | Vocabulary robustness when prompt-identifying terms are masked. |
| `rationale_joint_service_prompt_specificity.csv` | Generated analysis | Service x prompt x term | Features distinctive against both same-prompt other-service and same-service other-prompt comparisons. |
| `classifier_cache/*.joblib` | Cache/frozen model | Serialized model | Fitted classifier objects used to keep figures and coefficients aligned with frozen scores. |

The classifier performance file should be cited for reported scores rather than refitting during every notebook run. Cross-validation includes stochastic components, and small score changes across environments do not indicate a new substantive result.

### Rationale content and experimental definitional analysis

| File | Status | Row unit | Purpose |
| --- | --- | --- | --- |
| `rationale_signal_detail.csv` | Generated analytical table | Language x service x prompt | Overlapping lexical signals for compositional, scholarly, human-centered, generic-knowledge, borrowing, coinage, established-equivalent, and uncertainty claims. |
| `rationale_digital_humanities_context_by_service_prompt.csv` | Generated exploratory table | Service x prompt x anchor x context term | Vocabulary occurring around exact `digital` or `humanities` mentions. |
| `rationale_digital_humanities_context_contrast.csv` | Generated exploratory table | Context term | Difference in document-level association with `digital` versus `humanities`. |
| `definitional_nmf_topic_candidates.csv` | Experimental | Topic candidate | NMF topic-vocabulary candidates used to test possible definitional frames. |
| `definitional_embedding_topic_candidates.csv` | Experimental | Embedding cluster candidate | Unsupervised embedding-cluster candidates used for sensitivity analysis. |

The definitional topic and lexical-rule files are exploratory. They are retained for transparency and follow-up work but should not be treated as validated semantic labels or linguistic ground truth.

### Translation and rationale embeddings

| File | Status | Row unit | Purpose |
| --- | --- | --- | --- |
| `translation_projection_language_metrics.csv` | Generated embedding analysis | One language | Available services and mean/max pairwise translation distance. |
| `embedding_prompt_model_variation.csv` | Generated embedding analysis | One language | Independent-prompt variation within models versus model variation within prompts. |
| `embedding_prompt_model_variation_with_judge.csv` | Generated embedding analysis | One language | Same comparison including judge outputs. |
| `embedding_service_prompt_centroid_distances.csv` | Generated embedding analysis | Service x prompt | Distance from each service-prompt centroid to the global space. |
| `translation_full_grid_similarity.csv` | Generated embedding analysis | One language | Independent versus judge-inclusive translation similarity. |
| `rationale_prompt_model_variation_with_judge.csv` | Generated embedding analysis | One language | Prompt/model variation in rationale space including judge. |
| `rationale_service_prompt_centroid_distances.csv` | Generated embedding analysis | Service x prompt | Rationale centroid distances. |
| `rationale_full_grid_similarity.csv` | Generated embedding analysis | One language | Independent versus judge-inclusive rationale similarity. |
| `translation_rationale_pairwise_alignment.csv` | Generated embedding analysis | Language x prompt x service pair | Translation and rationale distance for one pair. |
| `translation_rationale_language_alignment.csv` | Generated embedding analysis | Language x prompt | Correlation between pairwise translation and rationale distances. |
| `translation_rationale_alignment_summary.csv` | Generated summary | Prompt/comparison | Corpus-level alignment correlations. |

These files support methodological exploration and a planned follow-up embedding study. Embedding distance measures representational proximity under the named model, not linguistic equivalence or translation accuracy. UMAP projections are visual aids; substantive distances are calculated in the original embedding space.

### Historic reference comparisons

The canonical historic outputs are the dated `historic_2022_*` and `historic_2024_*` groups generated from the two files in `historic_materials/`.

| Filename suffix | Row unit | Purpose |
| --- | --- | --- |
| `reference_artifacts.csv` | One source artifact | Documents input file, coverage, and role. |
| `reference_service_presence.csv` | One historic source/service | Translation coverage. |
| `pairwise_reference_agreement.csv` | One source pair | Exact normalized agreement among overlapping rows. |
| `reference_count_summary.csv` | Source-count grouping | Convergence by number of available sources. |
| `all_source_convergence_summary.csv` | Convergence category | Corpus-level convergence counts. |
| `reference_convergence_detail.csv` | One language | Available outputs and exact normalized differences. |

Undated `historic_*` files belong to an earlier single-artifact workflow. They are retained for provenance but should not be used in place of the dated 2022 and 2024 outputs.

## Key Column Dictionaries

### Automated review signals

`automated_review_signals.csv` and `review_explorer_data.csv` use paired columns:

- `has_{signal}`: language has at least one flagged service-prompt output.
- `{signal}_services`: semicolon-separated services responsible for the flag.

Signals include missing or placeholder rationales, mixed or unexpected scripts, romanization, source-term retention, placeholder terms, repetition loops, extreme lengths, Unicode escapes, very short outputs, refusal language, transliteration claims, language-name-as-term responses, and unexpected rationale language.

These are triage indicators. For example, source-term retention can be an error, a borrowing, or an established local convention.

### Manual exclusions

| Column | Meaning |
| --- | --- |
| `language_code`, `language_name` | Reviewed language row. |
| `service` | Decision scope: a named service, `analysis_exclusion`, `search_exclusion`, or `term_correction`. |
| `exclude_translation` | Exclude the translation from analysis when true. |
| `exclude_term_minimal`, `exclude_term_fluent_speaker`, `exclude_term_github_searcher`, `exclude_term_judge` | Exclude the service-condition term from search-term generation. |
| `original_term`, `corrected_term` | Preserved source value and reviewed replacement. |
| `notes` | Review rationale. |

The same language can have multiple rows when decisions apply to different services or scopes. Do not reduce this file to one row per language without preserving that scope.

### Exact-form comparison

| Column | Meaning |
| --- | --- |
| `comparison_status` | Broad result such as `exact_convergence`, `near_form_convergence`, or `substantive_variation`. |
| `n_unique_raw`, `n_unique_normalized` | Distinct forms before and after conservative normalization. |
| `max_edit_distance`, `distance_threshold` | String-distance evidence used for near-form comparison. |
| `source_retention_*` | Counts and services retaining tokens from the English source phrase. |
| `has_script_disagreement`, `scripts_found` | Whether outputs use more than one detected script. |
| `absence_signals`, `construction_signals`, `debate_signals` | Lexical evidence extracted from rationales. |
| `service_translations` | Serialized service-to-term mapping retained for inspection. |

Normalization is intentionally conservative. It standardizes comparison without automatically merging distinct spellings, transliterations, scripts, inflections, or translation strategies.

### Disagreement synthesis

| Column | Meaning |
| --- | --- |
| `disagreement_shape` | `unanimous`, `near_unanimous_with_outlier`, `dominant_form_with_alternatives`, or `fragmented_disagreement`. |
| `n_exact_form_clusters` | Number of exact normalized clusters. |
| `largest_cluster_size`, `dominant_form_share` | Size and share of the largest cluster. |
| `dominant_cluster_services` | Services contributing the largest form cluster. |
| `service_group_pattern` | Alignment pattern across API, local, MT, and LLM groupings. |
| `wikipedia_relationship` | Whether Wikipedia is absent, matches the dominant form, matches an alternative, or is isolated. |
| `prompt_stable_*`, `prompt_sensitive_*` | Service-level exact-form behavior across prompts. |
| `minimal_unique_llm_forms`, `judge_unique_llm_forms` | Candidate proliferation before and during judge synthesis. |
| `judge_effect` | Judge-induced convergence, limited change, or increased variation. |
| `mean_embedding_distance`, `max_embedding_distance` | Supplementary semantic-distance evidence, not correctness. |

## Regeneration

The review stage is documented in [`scripts/review/README.md`](../../../../scripts/review/README.md), and downstream comparison is documented in [`scripts/analysis/README.md`](../../../../scripts/analysis/README.md). The usual order is:

1. `explore_confidence_within_variant.py`
2. `explore_confidence_across_variants.py`
3. notebook 02 writes automated review signals
4. `build_review_explorer_data.py` prepares the browser dataset
5. browser review is saved as `manual_exclusions.csv`
6. `explore_disagreements.py`
7. `build_disagreement_explorer_data.py`
8. `build_disagreement_patterns.py`
9. notebooks 05-08 perform embedding and rationale analyses

Historic tables are rebuilt with:

```bash
python scripts/analysis/build_historic_reference_convergence.py --term "Digital Humanities"
```

## Interpretation Boundaries

- Exact agreement does not establish correctness.
- Disagreement does not establish that all forms are semantically unrelated.
- Automated signals do not substitute for speakers or linguistic expertise.
- Rationales are outputs to analyze, not verified explanations of internal model reasoning.
- Embedding and classifier results depend on model, preprocessing, and feature choices; frozen results preserve the article's reported analytical state.
