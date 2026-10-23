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

## Workflow

1. Optionally refresh external service support with `curation/refresh_service_support.py` when provider coverage has changed.
2. Run `generate_language_codes.py`. It downloads missing upstream metadata, reuses local caches, merges the source inventories, enriches names and families, and writes the generated metadata files.
3. Run `curation/audit_language_identifiers.py` as a read-only check after a regeneration.
4. Run the family review workflow documented in [`scripts/review/README.md`](../review/README.md) when family evidence or assignments changed.
5. Rerun notebook 01 to refresh source-coverage and family-analysis figures.

The standard build imports the supporting modules automatically. Do not run `parse_cldr_json.py`, `reconcile_language_families.py`, `map_language_identifiers.py`, or `language_metadata_overrides.py` as separate pipeline stages.

## Inputs And Outputs

| Type | Location |
| --- | --- |
| Generated metadata | `datasets/metadata_files/language_codes_comprehensive.csv` |
| Reviewed analytical layer | `datasets/metadata_files/language_codes_comprehensive_family_reviewed.csv` |
| Script-level rows | `datasets/metadata_files/language_scripts_long.csv` |
| Family hierarchy | `datasets/metadata_files/iso_639_set5.csv` |
| Download caches | `datasets/metadata_files/cldr-cache/` and `glottolog-cache/` |

The generated comprehensive CSV preserves source provenance. The reviewed family CSV is a downstream analytical layer and does not overwrite the source-build artifact.

See `datasets/metadata_files/README.md` for column-level documentation and provenance.
