"""Version and select historical translation observations.

Translation CSVs retain every observation. Callers explicitly select the latest, reviewed, as-of, or complete historical view when reading them.

``transmogrifier_id`` identifies one dated translation observation, not a language entity or a judgment of linguistic validity. Language metadata uses ``language_code``/``project_language_code`` instead.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Literal

import pandas as pd

VersionMode = Literal["latest", "selected", "as_of", "all_history"]
CANDIDATE_GENERATED_AT_COLUMN = "coding_dh_generated_at_utc"
LEGACY_CANDIDATE_DATE_COLUMN = "coding_dh_date"
PROMPT_VARIANTS = (
    "fluent_speaker",
    "github_searcher",
    "minimal",
    "judge",
)

SERVICE_OBSERVATION_COLUMNS = (
    "language_code",
    "language_name",
    "project_language_code",
    "term_source",
    CANDIDATE_GENERATED_AT_COLUMN,
    "service",
    "prompt_variant",
    "model_identifier",
    "transmogrifier_id",
    "generation_temperature",
    "generation_top_p",
    "generation_max_output_tokens",
    "generation_settings_source",
)


def normalize_candidate_timestamps(frame: pd.DataFrame) -> pd.DataFrame:
    """Expose the specific generation timestamp while reading legacy files."""
    result = frame.copy()
    if CANDIDATE_GENERATED_AT_COLUMN not in result.columns:
        if LEGACY_CANDIDATE_DATE_COLUMN in result.columns:
            result[CANDIDATE_GENERATED_AT_COLUMN] = result[
                LEGACY_CANDIDATE_DATE_COLUMN
            ]
        else:
            result[CANDIDATE_GENERATED_AT_COLUMN] = None
    elif LEGACY_CANDIDATE_DATE_COLUMN in result.columns:
        missing = (
            result[CANDIDATE_GENERATED_AT_COLUMN].isna()
            | result[CANDIDATE_GENERATED_AT_COLUMN].astype(str).str.strip().eq("")
        )
        result.loc[missing, CANDIDATE_GENERATED_AT_COLUMN] = result.loc[
            missing, LEGACY_CANDIDATE_DATE_COLUMN
        ]
    return result


def select_service_observation_columns(
    frame: pd.DataFrame,
    *,
    service: str,
) -> pd.DataFrame:
    """Keep common observation keys and fields owned by one service.

    Generation operates on a cumulative working frame, but each persisted CSV
    is an observation log for one service. Foreign-service outputs, baseline
    candidates, mutable language metadata, composite terms, and transient
    exclusion flags therefore do not belong in that file.
    """
    normalized_service = service.strip().lower().replace("-", "_").replace(" ", "_")
    common = [column for column in SERVICE_OBSERVATION_COLUMNS if column in frame.columns]
    owned = [
        column for column in frame.columns
        if column.startswith(f"{normalized_service}_") and column not in common
    ]
    generic_output = [
        column for column in ("translation", "rationale", "raw_response")
        if column in frame.columns and column not in common
    ]
    return frame[common + owned + generic_output].copy()


def infer_service_context(path: str | Path) -> tuple[str, str]:
    """Infer service and prompt variant from an established translation filename."""
    stem = Path(path).stem
    if stem.endswith("_translations"):
        stem = stem[: -len("_translations")]
    for variant in PROMPT_VARIANTS:
        suffix = f"_{variant}"
        if stem.endswith(suffix):
            return stem[: -len(suffix)], variant
    return stem, "direct"


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return str(value)


def _version_payload(row: pd.Series) -> dict[str, str]:
    service = _text(row.get("service")).replace("-", "_").replace(" ", "_")
    candidate_columns = sorted(
        column
        for column in row.index
        if column.endswith("_translated_term")
        or column.endswith("_translation_rationale")
        or column in {"translation", "rationale"}
    )
    service_columns = [
        column for column in candidate_columns if service and column.startswith(f"{service}_")
    ]
    output_columns = service_columns or candidate_columns
    columns = [
        "term_source",
        "language_code",
        "service",
        "prompt_variant",
        "model_identifier",
        CANDIDATE_GENERATED_AT_COLUMN,
        *output_columns,
    ]
    return {column: _text(row.get(column)) for column in columns}


def add_transmogrifier_ids(
    frame: pd.DataFrame,
    *,
    service: str | None = None,
    prompt_variant: str | None = None,
    model_identifier: str | None = None,
) -> pd.DataFrame:
    """Add context and deterministic observation IDs without removing history.

    The ID payload contains the source term, language, service, prompt variant,
    model identifier, observation timestamp, and the named service's output.
    Consequently, the same visible output observed at two times receives two
    IDs, while replaying the exact same stored observation produces the same ID.
    """
    result = normalize_candidate_timestamps(frame)
    if service is not None:
        result["service"] = service
    if prompt_variant is not None:
        result["prompt_variant"] = prompt_variant
    if model_identifier is not None:
        result["model_identifier"] = model_identifier
    elif service is not None:
        # Cumulative generation frames may carry another service's context.
        # Re-infer the model from the named service's own response column.
        result["model_identifier"] = None
    if "model_identifier" not in result.columns:
        result["model_identifier"] = None
    for current_service in result.get(
        "service", pd.Series(index=result.index, dtype="object")
    ).dropna().astype(str).unique():
        model_column = f"{current_service.replace('-', '_').replace(' ', '_')}_model"
        if model_column in result.columns:
            missing_model = result["model_identifier"].isna() | result[
                "model_identifier"
            ].astype(str).str.strip().eq("")
            result.loc[missing_model, "model_identifier"] = result.loc[
                missing_model, model_column
            ]

    if "transmogrifier_id" not in result.columns:
        result["transmogrifier_id"] = None
    missing = result["transmogrifier_id"].isna() | result["transmogrifier_id"].astype(str).str.strip().eq("")
    for index in result.index[missing]:
        encoded = json.dumps(
            _version_payload(result.loc[index]),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        result.at[index, "transmogrifier_id"] = f"tm_{hashlib.sha256(encoded).hexdigest()[:20]}"
    return result


def select_translation_versions(
    frame: pd.DataFrame,
    mode: VersionMode = "latest",
    *,
    as_of: str | pd.Timestamp | None = None,
    selected_versions: pd.DataFrame | None = None,
    identity_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Return an explicit version view without mutating the historical source."""
    if mode not in {"latest", "selected", "as_of", "all_history"}:
        raise ValueError(f"Unsupported translation version mode: {mode}")
    result = add_transmogrifier_ids(frame)
    if mode == "all_history" or result.empty:
        return result.reset_index(drop=True)
    if mode == "selected":
        if selected_versions is None or "transmogrifier_id" not in selected_versions.columns:
            raise ValueError("selected mode requires selected_versions with transmogrifier_id")
        selected = selected_versions.copy()
        if "selected" in selected.columns:
            selected_flag = selected["selected"].fillna(False)
            if selected_flag.dtype == "object":
                selected_flag = selected_flag.astype(str).str.strip().str.lower().isin(
                    {"true", "1", "yes", "y", "selected"}
                )
            else:
                selected_flag = selected_flag.astype(bool)
            selected = selected[selected_flag]
        return result[
            result["transmogrifier_id"].isin(selected["transmogrifier_id"])
        ].reset_index(drop=True)
    if CANDIDATE_GENERATED_AT_COLUMN not in result.columns:
        raise ValueError(
            f"latest and as_of modes require {CANDIDATE_GENERATED_AT_COLUMN}"
        )

    result["_version_time"] = pd.to_datetime(
        result[CANDIDATE_GENERATED_AT_COLUMN],
        format="mixed",
        errors="coerce",
        utc=True,
    )
    if mode == "as_of":
        if as_of is None:
            raise ValueError("as_of mode requires an as_of timestamp")
        boundary = pd.Timestamp(as_of)
        boundary = boundary.tz_localize("UTC") if boundary.tzinfo is None else boundary.tz_convert("UTC")
        result = result[result["_version_time"] <= boundary]

    identity = identity_columns or [
        column
        for column in ("term_source", "language_code", "service", "prompt_variant")
        if column in result.columns
    ]
    if not identity:
        raise ValueError("No translation identity columns are available")
    result = result.sort_values(
        ["_version_time", "transmogrifier_id"], na_position="first"
    ).drop_duplicates(identity, keep="last")
    return result.drop(columns="_version_time").reset_index(drop=True)


def load_translation_versions(
    path: str | Path,
    mode: VersionMode = "latest",
    *,
    as_of: str | pd.Timestamp | None = None,
    selected_versions: pd.DataFrame | None = None,
    service: str | None = None,
    prompt_variant: str | None = None,
) -> pd.DataFrame:
    """Load one translation CSV and return the requested version view."""
    path = Path(path)
    frame = pd.read_csv(path, on_bad_lines="warn", converters={"language_code": str})
    frame = normalize_candidate_timestamps(frame)
    inferred_service, inferred_variant = infer_service_context(path)
    frame = add_transmogrifier_ids(
        frame,
        service=service or inferred_service,
        prompt_variant=prompt_variant or inferred_variant,
    )
    frame = select_service_observation_columns(
        frame,
        service=service or inferred_service,
    )
    return select_translation_versions(
        frame,
        mode,
        as_of=as_of,
        selected_versions=selected_versions,
    )


def save_translation_history(
    path: str | Path,
    new_rows: pd.DataFrame,
    *,
    service: str | None = None,
    prompt_variant: str | None = None,
    model_identifier: str | None = None,
) -> pd.DataFrame:
    """Append unique observations and rewrite one schema-aligned historical CSV."""
    path = Path(path)
    inferred_service, inferred_variant = infer_service_context(path)
    incoming = add_transmogrifier_ids(
        new_rows,
        service=service or inferred_service,
        prompt_variant=prompt_variant or inferred_variant,
        model_identifier=model_identifier,
    )
    incoming = select_service_observation_columns(
        incoming,
        service=service or inferred_service,
    )
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        incoming.to_csv(path, index=False, quoting=csv.QUOTE_ALL)
        return incoming.reset_index(drop=True)

    disk_columns = pd.read_csv(path, nrows=0).columns.tolist()
    existing = load_translation_versions(path, mode="all_history")
    new_ids = ~incoming["transmogrifier_id"].isin(existing["transmogrifier_id"])
    incoming = incoming[new_ids].copy()
    if incoming.empty:
        if list(existing.columns) != disk_columns:
            temporary_path = path.with_suffix(f"{path.suffix}.tmp")
            existing.to_csv(temporary_path, index=False, quoting=csv.QUOTE_ALL)
            temporary_path.replace(path)
        return existing.reset_index(drop=True)

    combined_columns = list(existing.columns) + [
        column for column in incoming.columns if column not in existing.columns
    ]
    if list(existing.columns) == disk_columns and set(incoming.columns).issubset(existing.columns):
        incoming.reindex(columns=combined_columns).to_csv(
            path,
            mode="a",
            header=False,
            index=False,
            quoting=csv.QUOTE_ALL,
        )
        combined = pd.concat([existing, incoming], ignore_index=True, sort=False)
        return combined.reset_index(drop=True)

    combined = pd.concat([existing, incoming], ignore_index=True, sort=False)
    combined = combined.reindex(columns=combined_columns)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    combined.to_csv(temporary_path, index=False, quoting=csv.QUOTE_ALL)
    temporary_path.replace(path)
    return combined.reset_index(drop=True)
