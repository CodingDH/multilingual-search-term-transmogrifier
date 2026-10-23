"""Cross-cutting file, path, chart, and language-family utilities."""

from __future__ import annotations

import os
from typing import Dict, Optional, Tuple

import altair as alt
import apikey
import pandas as pd
import vl_convert as vlc
from rich.console import Console

console = Console()

# Colorblind-friendly Coding DH palette for publication figures. The order is
# stable so categorical colors remain consistent across notebooks and exports.
CODING_DH_CATEGORICAL_COLORS: Tuple[str, ...] = (
	"#0072B2",  # electric blue
	"#E69F00",  # amber
	"#009E73",  # teal green
	"#CC79A7",  # neon pink
	"#D55E00",  # vermilion
	"#56B4E9",  # cyan
	"#F0C808",  # print-friendly yellow
	"#3A3A3A",  # charcoal
)
CODING_DH_SEQUENTIAL_SCHEME = "viridis"
CODING_DH_DIVERGING_SCHEME = "blueorange"


def save_chart(chart: alt.Chart, filename: str, scale_factor: float = 2.0) -> None:
	"""
	Save an Altair chart using vl-convert without changing its display renderer.

	Parameters
	----------
	chart : alt.Chart
		Altair chart to save.
	filename : str
		Path to save the chart to. Supported extensions are .svg and .png.
	scale_factor : int or float
		Scale factor for PNG output. A value of 2 writes an image at twice the
		default resolution.
	"""
	extension = os.path.splitext(str(filename))[-1].lower().lstrip(".")
	os.makedirs(os.path.dirname(str(filename)), exist_ok=True)
	with alt.data_transformers.enable("default"), alt.data_transformers.disable_max_rows():
		if extension == "svg":
			with open(filename, "w", encoding="utf-8") as f:
				f.write(vlc.vegalite_to_svg(chart.to_dict()))
		elif extension == "png":
			with open(filename, "wb") as f:
				f.write(vlc.vegalite_to_png(chart.to_dict(), scale=scale_factor))
		else:
			raise ValueError("Only svg and png formats are supported")


def read_csv_file(file_path: str, error_bad_lines: bool = True) -> pd.DataFrame:
	"""
	Read a CSV file with UTF-8 encoding, falling back to latin-1 on failure.

	Parameters
	----------
	file_path : str
	error_bad_lines : bool
		Passed to pandas; set False to skip malformed rows.

	Returns
	-------
	pd.DataFrame
	"""
	bad_lines = 'skip' if not error_bad_lines else 'error'
	# converters preserves 'nan' (Min Nan Chinese, ISO 639-3) as the string "nan" rather than letting pandas promote it to float NaN via its default NA list.
	_conv = {'language_code': str}
	try:
		return pd.read_csv(file_path, encoding='utf-8', on_bad_lines=bad_lines, converters=_conv)
	except UnicodeDecodeError:
		return pd.read_csv(file_path, encoding='latin-1', on_bad_lines=bad_lines, converters=_conv)
	except pd.errors.ParserError:
		# Fall back to the Python engine, which is more lenient with malformed rows (e.g. column-count mismatches from schema migrations).
		return pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', engine='python', converters=_conv)


def set_data_directory_path(path: str) -> None:
	"""
	Sets the Multilingual Search Term Transmogrifier data directory path.

	:param path: Path to data directory
	"""
	apikey.save("MULTILINGUAL_SEARCH_TERM_TRANSMOGRIFIER_DATA_DIRECTORY", path)
	console.print(f'Multilingual Search Term Transmogrifier data directory path set to {path}', style='bold blue')

def get_data_directory_path() -> str:
	"""
	Gets the Multilingual Search Term Transmogrifier data directory path.

	:return: Data directory path
	"""
	configured_path = apikey.load("MULTILINGUAL_SEARCH_TERM_TRANSMOGRIFIER_DATA_DIRECTORY")
	if configured_path and os.path.isdir(configured_path):
		return configured_path

	project_data_path = os.path.abspath(
		os.path.join(os.path.dirname(__file__), os.pardir, 'datasets')
	)
	if os.path.isdir(project_data_path):
		return project_data_path

	return configured_path


def get_search_data_directory_path() -> str:
	"""Return the external search-results directory used by ``searching_for_DH``."""
	return apikey.load("SEARCHING_FOR_DH_DATA_DIRECTORY")


_LANG_FAMILY_CACHE: Optional[Dict[str, str]] = None


def get_language_family(code: str) -> str:
	"""Return the reviewed family/analysis label for a language code. Falls back to 'Other' when unknown.

	Prefers `language_codes_comprehensive_family_reviewed.csv` when present, using
	`family_name_analysis` for chart/grouping work and falling back through the
	reviewed and pre-review reconciled columns. If the reviewed metadata layer has
	not been generated yet, falls back to `language_codes_comprehensive.csv` and
	uses `family_name_reconciled` over raw `family_name`.
	"""
	global _LANG_FAMILY_CACHE
	if _LANG_FAMILY_CACHE is None:
		data_dir = get_data_directory_path()
		metadata_dir = os.path.join(data_dir, 'metadata_files')
		reviewed_path = os.path.join(metadata_dir, 'language_codes_comprehensive_family_reviewed.csv')
		base_path = os.path.join(metadata_dir, 'language_codes_comprehensive.csv')
		csv_path = reviewed_path if os.path.exists(reviewed_path) else base_path
		if os.path.exists(csv_path):
			# converters preserves 'nan' (Min Nan Chinese, ISO 639-3) as a string
			df = pd.read_csv(csv_path, converters={'language_code': str})
			family_candidates = [
				'family_name_analysis',
				'family_name_reconciled_reviewed',
				'family_name_reconciled',
				'family_name',
			]
			fam_col = pd.Series(['Other'] * len(df), index=df.index, dtype='object')
			for col in reversed([c for c in family_candidates if c in df.columns]):
				fam_col = df[col].where(df[col].notna() & df[col].astype(str).str.strip().ne(''), fam_col)
			_LANG_FAMILY_CACHE = dict(
				zip(df['language_code'],
					fam_col.fillna('Other').astype(str))
			)
		else:
			_LANG_FAMILY_CACHE = {}
	return _LANG_FAMILY_CACHE.get(code, 'Other')
