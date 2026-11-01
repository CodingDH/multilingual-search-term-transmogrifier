"""Log and normalize translation-service errors."""

from __future__ import annotations

import os
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd

from scripts.utils import read_csv_file

def log_error_to_file(
	error_file_path: str,
	additional_data: dict,
	status_code: int,
	error_url: str,
	error_message: str = "",
) -> None:
	"""
	Append a structured error record to a CSV error log.

	Parameters
	----------
	error_file_path : str
	additional_data : dict
		Extra columns to record (e.g. term_source, language_code).
	status_code : int
	error_url : str
		A description of the failing call.
	error_message : str
		The full error message from the service or exception.
	"""
	observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
	error_service = Path(error_file_path).stem.removesuffix("_translation_errors")
	payload = {
		"error_service": error_service,
		"coding_dh_date": observed_at,
		"error_url": error_url,
		"status_code": status_code,
		"error_message": error_message,
		**additional_data,
	}
	error_observation_id = "err_" + hashlib.sha256(
		json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
	).hexdigest()[:20]
	error_df = pd.DataFrame([{
		"error_observation_id": error_observation_id,
		"error_service": error_service,
		"coding_dh_date": observed_at,
		"error_date": observed_at[:10],
		"error_url": error_url,
		"status_code": status_code,
		"error_message": error_message,
	}])
	error_df = pd.concat([error_df, pd.DataFrame([additional_data])], axis=1)

	if os.path.exists(error_file_path):
		existing = pd.read_csv(error_file_path, nrows=0)
		missing_cols = [c for c in error_df.columns if c not in existing.columns]
		if missing_cols:
			# Schema migration: backfill any new columns so existing rows stay aligned.
			existing_full = read_csv_file(error_file_path, error_bad_lines=False)
			for col in missing_cols:
				existing_full[col] = ''
			existing_full.to_csv(error_file_path, index=False)
			# Re-read header after migration so reindex below uses the updated schema.
			existing = pd.read_csv(error_file_path, nrows=0)
		# Reorder new row to match the file's column order exactly — mismatches cause values to land in the wrong columns when appending without a header.
		file_cols = existing.columns.tolist()
		for c in file_cols:
			if c not in error_df.columns:
				error_df[c] = None
		error_df = error_df.reindex(columns=file_cols)
		error_df.to_csv(error_file_path, mode='a', header=False, index=False)
	else:
		os.makedirs(os.path.dirname(error_file_path), exist_ok=True)
		error_df.to_csv(error_file_path, index=False)


def prepare_error_log(error_file_path: str) -> None:
	"""
	Validate an existing error log without collapsing historical observations.

	Parameters
	----------
	error_file_path : str
	"""
	if os.path.exists(error_file_path):
		read_csv_file(error_file_path, error_bad_lines=False)


def clean_write_error_file(
	error_file_path: str,
	drop_fields: Optional[List[str]] = None,
) -> None:
	"""Backward-compatible alias that no longer removes historical errors."""
	prepare_error_log(error_file_path)
