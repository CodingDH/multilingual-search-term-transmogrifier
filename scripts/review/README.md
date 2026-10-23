# Review

These scripts prepare review queues and browser interfaces or apply saved human decisions. Automated signals prioritize inspection; they do not independently establish correctness.

## Language Metadata Review

1. Run `build_family_analysis_mapping.py`.
2. Run `build_family_reconciliation_review.py`.
3. Review the CSVs in the corresponding interfaces under `html_files/`.
4. Run `apply_family_review_metadata.py`.

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
