# Language Metadata

This package builds and loads the shared language inventory consumed by candidate generation and downstream analysis.

| Module | Purpose |
| --- | --- |
| `generate_language_codes.py` | Orchestrate source ingestion, enrichment, and canonical CSV output |
| `parse_cldr_json.py` | Download, cache, and parse CLDR language, script, alias, and family data |
| `language_metadata_overrides.py` | Preserve curated family assignments, SIL names, and the CLDR v45 supplement |
| `reconcile_language_families.py` | Assign ISO 639-5 families and reconcile them against Glottolog review decisions |
| `map_language_identifiers.py` | Add BCP 47 context and translation-service identifier support |
| [`curation/`](curation/README.md) | Optional audits, refreshes, spot checks, and assignment maintenance |

```bash
python -m scripts.language_metadata.generate_language_codes
```

The build writes `language_codes_comprehensive.csv`, `language_scripts_long.csv`, and `iso_639_set5.csv` under `datasets/metadata_files/`. `load_language_codes()` is the public loader used by candidate generation. Browser-reviewed family metadata remains a separate post-build layer created by scripts in `scripts/review/`.

See `datasets/metadata_files/README.md` for column-level documentation and provenance.
