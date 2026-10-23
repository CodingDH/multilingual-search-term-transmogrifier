# Review

These scripts prepare review queues and browser interfaces or apply saved human decisions. Automated signals prioritize inspection; they do not independently establish correctness.

## Language Metadata Review

Run this sequence after regenerating language metadata or changing family evidence:

1. Run `python -m scripts.review.build_family_analysis_mapping`.
2. Open `html_files/family_analysis_mapping_reviewer.html`, load the generated CSV, and save `family_analysis_mapping_reviewed.csv`.
3. Run `python -m scripts.review.build_family_reconciliation_review`.
4. Open `html_files/family_reconciliation_reviewer.html`, complete row-level decisions, and save `family_reconciliation_reviewed.csv`.
5. Run `python -m scripts.review.apply_family_review_metadata`.
6. Confirm that `language_codes_comprehensive_family_reviewed.csv` was rebuilt before rerunning notebook 01 or family-level analyses.

The first interface standardizes labels used for aggregate analysis. The second reviews language-to-family assignments. Reversing those roles would collapse distinct editorial decisions.

## Candidate Review

| Module | Purpose |
| --- | --- |
| `analyze_scripts.py` | Detect dominant scripts and script disagreement |
| `translation_classifier.py` | Detect mixed scripts, placeholders, source retention, repetition, and related signals |
| `apply_review_filters.py` | Load and apply review decisions and pairing rules |
| `build_review_explorer_data.py` | Prepare the multilingual candidate-review dataset |
| `build_search_relevance_review.py` | Prepare the post-search relevance queue |

```bash
python -m scripts.review.build_review_explorer_data --term "Digital Humanities"
python -m scripts.review.build_search_relevance_review
```

## Candidate Review Order

1. Generate all intended direct-service and prompt-service files.
2. Run notebook 02 to create `automated_review_signals.csv`.
3. Run `build_review_explorer_data.py` for the term.
4. Load `review_explorer_data.csv` in `html_files/review_explorer.html`.
5. Save the reviewed decisions as `manual_exclusions.csv` in the term's `evaluation/` directory.
6. Rebuild downstream disagreement artifacts before exporting search terms.

`analyze_scripts.py`, `translation_classifier.py`, and `apply_review_filters.py` are imported helpers, not standalone stages. Their signals support review prioritization; only saved review decisions determine exclusions and corrections.

## Post-Search Review

Run `build_search_relevance_review.py` only after the private GitHub collection pipeline has finished and its data directory is configured. Load the resulting queue into `html_files/search_relevance_reviewer.html`, save the reviewed CSV, and then rerun notebook 09. This stage evaluates both term credibility and retrieval relevance; it does not alter the original candidate-generation files.
