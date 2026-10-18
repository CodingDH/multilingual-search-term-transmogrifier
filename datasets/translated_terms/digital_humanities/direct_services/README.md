# Direct-Service Outputs

These files preserve prompt-invariant evidence collected for `Digital Humanities`. They are queried once per language rather than once per LLM prompt condition.

## Files

| File | Source | Rows | Primary output |
| --- | --- | ---: | --- |
| `wikipedia_translations.csv` | Wikipedia interlanguage-link labels | 40 productive rows | `wikipedia_translated_term` |
| `gt_translations.csv` | Google Translate | 881 language rows | `gt_translated_term` |
| `enmt_translations.csv` | EasyNMT / Helsinki-NLP models | 881 language rows | `enmt_translated_term` |
| `lingvanex_translations.csv` | Lingvanex | 881 language rows | `lingvanex_translated_term` |

Wikipedia is treated as community-edited terminology evidence, not as a machine translation service. A Wikipedia label can still be ambiguous: it may identify an article title, disciplinary category, or locally established naming practice rather than a uniquely correct translation.

## Column Dictionary

| Column or pattern | Meaning |
| --- | --- |
| `language_code` | Project language identifier. Read as a string. |
| `language_name` | English display name available at collection time. Not present in every historical schema. |
| `term_source` | Source phrase requested, here `Digital Humanities`. |
| `{service}_translated_term` | Output returned by the named service. Blank means no stored usable output. |
| `term` | Pipeline-selected term present in some cumulative files. It is not an independently generated service output. |
| `coding_dh_date` | Collection or write timestamp. |
| `family_name` | Family label attached at generation time. For analysis, prefer the reviewed family metadata joined through `language_code`. |
| `exclude_*` | Historical generation-time flags carried through cumulative merges. Current exclusions are stored in `../evaluation/manual_exclusions.csv`. |
| other service term columns | Earlier direct-service evidence merged into a later service file. Use the file named for a service as the provenance source for that service's primary output. |

## Row and Coverage Semantics

Google Translate, EasyNMT, and Lingvanex files retain all 881 target rows so unsupported or failed cases remain visible as blanks. The Wikipedia file stores only productive interlanguage-label rows. Coverage comparisons must therefore count nonblank output fields rather than compare file lengths.

## Provenance

These are raw generated/source outputs. Corrections and exclusions are applied later and do not overwrite these files. This preserves the original evidence for audit and historical comparison.
