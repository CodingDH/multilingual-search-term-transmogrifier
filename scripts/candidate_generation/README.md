# Candidate Generation

This package generates multilingual candidate terms and rationales from direct translation services, Wikipedia, hosted LLMs, and local Ollama models. A populated response is not treated as proof of linguistic validity.

| Module | Purpose |
| --- | --- |
| `generate_translations.py` | Main service orchestrator and output writer |
| `generate_translation_prompts.py` | Run the four prompt conditions |
| `translation_prompts.py` | Prompt templates, service labels, and judge evidence formatting |
| `translation_services.py` | Direct-service and model clients |
| `data_processing.py` | Parse and normalize service responses |
| `log_errors.py` | Append service error observations without erasing earlier failures |
| `translation_versions.py` | Assign `transmogrifier_id` values and select historical views |
| `normalize_service_observation_files.py` | Preview or migrate legacy wide prompt-service CSVs to service-local schemas |

```bash
python -m scripts.candidate_generation.generate_translations
python -m scripts.candidate_generation.generate_translation_prompts
```

The first three prompt conditions generate candidates independently. The judge runs afterward with distinct candidates from those prompts, direct services, and Wikipedia. Outputs are written under `datasets/candidate_terms/{term}/`. Regeneration can differ as models, APIs, and upstream services change, so preserve prompt, model, date, and repository-commit provenance.

Candidate-output CSVs preserve successive observations. `translation_versions.py`
adds a deterministic `transmogrifier_id` and exposes four explicit read modes:
`latest` for routine analysis, `selected` for a reviewed list of IDs, `as_of`
for a historical cutoff, and `all_history` for longitudinal work. Generation
scripts append observations and return a latest-only view to existing callers.
This domain-specific loader belongs in `translation_versions.py`, rather than
the general `scripts/utils.py`, because its identity and selection rules apply
only to candidate observations.

Each prompt-service CSV is service-local. It contains common observation keys,
generic generation settings, and fields prefixed by the service named in the
filename. The cumulative in-memory generation frame is never persisted whole:
foreign-service candidates, baseline terms, mutable family metadata, composite
term selections, and temporary `exclude_*` flags remain in their authoritative
files. This prevents later services in one run from duplicating all earlier
responses. Legacy files can be audited without modification and then migrated
atomically:

```bash
python -m scripts.candidate_generation.normalize_service_observation_files \
  --data-directory datasets --term digital_humanities

python -m scripts.candidate_generation.normalize_service_observation_files \
  --data-directory datasets --term digital_humanities --apply
```

```python
from scripts.candidate_generation.translation_versions import load_translation_versions

current = load_translation_versions(path, mode="latest")
historical = load_translation_versions(path, mode="all_history")
as_of_submission = load_translation_versions(
    path,
    mode="as_of",
    as_of="2026-11-01",
)
```

`selected` mode accepts a separate DataFrame containing `transmogrifier_id`
and, optionally, a boolean `selected` column. The loader never overwrites the
historical source file.

## Observation Policies

The default command queries only service-prompt-language cells that do not
already have a usable cached output. Loading a cached response is not a new
observation and does not establish that the service would return the same value
today.

Use `--refresh-existing` only when the purpose is to observe the enabled
services again. The pipeline re-queries every enabled cell and appends each
successful response with a new UTC `coding_dh_generated_at_utc`, even when the visible term
and rationale are unchanged:

```bash
python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" \
  --variant minimal fluent_speaker github_searcher judge \
  --refresh-existing
```

Prior deterministic failures remain excluded unless `--retry-errors` is also
supplied. A complete longitudinal refresh normally uses both flags:

```bash
python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" \
  --variant minimal fluent_speaker github_searcher judge \
  --refresh-existing --retry-errors
```

Refreshes can incur substantial API cost. Error logs are historical observation
tables as well: a repeated failure receives a new timestamp and identifier
rather than replacing the earlier record.

`coding_dh_generated_at_utc` records when Coding DH observed the service
response or failure. Provider fields such as `openai_created` and
`ollama_created_at` remain separate source-reported timestamps. Legacy files
with `coding_dh_date` are normalized to the specific generation field when
loaded and are rewritten to the current schema only when the pipeline next
updates that file.

Errors remain physically separate from successful model-output CSVs.
`error_observation_id` names one dated failure event; no stored
`latest_error_observation_id` is maintained. Historical failure analyses can
read all error events. A future recovery analysis would compare dated success
and error histories on demand.

During a command that runs several prompt variants, prompt-invariant services
(Wikipedia and direct translation services) are refreshed once and then reused
as evidence for the remaining prompt conditions. Each selected LLM prompt
condition is refreshed independently.

Wikipedia refreshes append a complete dated language snapshot rather than only
the productive interlanguage labels. Blank rows record that no label was
present at that observation time, allowing later additions, edits, and removals
to be reconstructed. Without `--refresh-existing`, the pipeline reuses the
latest stored Wikipedia snapshot.

## Before Running

1. Build or load `datasets/metadata_files/language_codes_comprehensive.csv`.
2. Configure the data directory and credentials described in the repository README.
3. Start Ollama and install the documented local models if local services are enabled.
4. Decide whether the run is a new experiment or an intentional regeneration of an existing term. Existing API outputs should not be overwritten casually because model behavior changes over time.

## Recommended Order

`generate_translations.py` is the reproducible command-line entry point. Supply independent prompts before `judge`:

```bash
python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" \
  --variant minimal fluent_speaker github_searcher judge
```

Large runs can be divided by infrastructure while preserving the same variant order:

```bash
python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" --ollama-only \
  --variant minimal fluent_speaker github_searcher judge

python -m scripts.candidate_generation.generate_translations \
  --terms "Digital Humanities" --api-only \
  --variant minimal fluent_speaker github_searcher judge
```

`generate_translation_prompts.py` provides the older interactive interface to the same prompt experiment. Use either that interface or the explicit CLI command above, not both for the same run. The judge requires prior candidate files and must remain last.

## Output Order

Direct-service and Wikipedia files are prompt invariant and live under `direct_services/`. LLM outputs live under `prompt_services/`, with service and prompt condition encoded in each filename. Error logs are written separately so explicit failures remain distinguishable from populated but questionable candidates.

After generation, run notebook 02 before building the browser review dataset. Notebook 02 creates the automated review signals consumed by `scripts.review.build_review_explorer_data`.
