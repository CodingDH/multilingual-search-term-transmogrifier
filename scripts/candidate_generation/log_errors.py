"""Log and normalize translation-service errors."""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Optional

import pandas as pd
from rich.console import Console

from scripts.utils import read_csv_file

console = Console()

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
	error_df = pd.DataFrame([{
		"error_date": datetime.now().strftime("%Y-%m-%d"),
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


def clean_write_error_file(
	error_file_path: str,
	drop_fields: Optional[List[str]] = None,
) -> None:
	"""
	Deduplicate an error log file in place.

	Parameters
	----------
	error_file_path : str
	drop_fields : list of str, optional
		Column subset used for deduplication.
	"""
	if os.path.exists(error_file_path):
		error_df = read_csv_file(error_file_path, error_bad_lines=False)
		# Filter drop_fields to columns that actually exist so callers can include "variant" in the list without KeyErrors on legacy CSVs that lack the column.
		_dedup_fields = [f for f in (drop_fields or []) if f in error_df.columns] or None
		if 'error_date' in error_df.columns:
			error_df['error_date'] = pd.to_datetime(error_df['error_date'])
			error_df = error_df.sort_values('error_date').drop_duplicates(
				subset=_dedup_fields, keep='last'
			)
		elif _dedup_fields:
			error_df = error_df.drop_duplicates(subset=_dedup_fields, keep='last')
		# Promote permanent failures: drop any transient (500/408) entry for a (term, language[, variant]) tuple that already has a deterministic (400/404) entry. This prevents a stale 500 from hiding a 400 in mark_errored_terms.
		_TRANSIENT = {500, 408}
		if 'status_code' in error_df.columns:
			_has_variant = 'variant' in error_df.columns
			_perm = error_df[~error_df['status_code'].isin(_TRANSIENT)]
			if _has_variant:
				permanent_pairs = set(
					zip(
						_perm['term_source'].astype(str),
						_perm['language_code'].astype(str),
						_perm['variant'].astype(str),
					)
				)
				if permanent_pairs:
					redundant = (
						error_df['status_code'].isin(_TRANSIENT) &
						error_df.apply(
							lambda r: (str(r['term_source']), str(r['language_code']), str(r['variant'])) in permanent_pairs,
							axis=1,
						)
					)
					error_df = error_df[~redundant]
			else:
				permanent_pairs = set(
					zip(
						_perm['term_source'].astype(str),
						_perm['language_code'].astype(str),
					)
				)
				if permanent_pairs:
					redundant = (
						error_df['status_code'].isin(_TRANSIENT) &
						error_df.apply(
							lambda r: (str(r['term_source']), str(r['language_code'])) in permanent_pairs,
							axis=1,
						)
					)
					error_df = error_df[~redundant]
		error_df.to_csv(error_file_path, index=False)
	else:
		console.print('No error file to clean', style='bold blue')
