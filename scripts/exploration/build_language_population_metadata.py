#!/usr/bin/env python3
"""Build provenance-preserving population evidence for the language inventory.

CLDR supplies the pipeline's baseline estimates through ``language_data``.
Wikidata supplements those estimates and retains every dated/scoped observation
instead of silently replacing CLDR. Glottolog provides stable ISO 639-3 and
Glottocode identity information; it is not treated as a population source.

Outputs:
    datasets/metadata_files/language_population_evidence.csv
    datasets/metadata_files/language_population_resolved.csv
    datasets/metadata_files/wikidata_population_cache.json

Usage:
    python scripts/exploration/build_language_population_metadata.py
    python scripts/exploration/build_language_population_metadata.py --cache-only
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
import requests
from language_data.population_data import LANGUAGE_SPEAKING_POPULATION


WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "CodingDH-language-population/1.0 (research metadata pipeline)"

# Wikimedia project identifiers whose bare strings collide with unrelated
# ISO 639-3 codes. Values are the intended language identities.
PROJECT_CODE_TO_ISO3 = {
    "als": "gsw",  # Alemannic, not Tosk Albanian
    "crn": "cnr",  # Montenegrin, not El Nayar Cora
    "nrm": "nrf",  # Norman Wikimedia project, not Narom
}


def _text(value: object) -> str:
    return "" if pd.isna(value) else str(value).strip()


def _bool(value: object) -> bool:
    return _text(value).lower() in {"1", "true", "yes"}


def _iso3_for_row(row: pd.Series) -> str:
    code = _text(row.get("language_code"))
    if code in PROJECT_CODE_TO_ISO3:
        return PROJECT_CODE_TO_ISO3[code]
    bcp47 = _text(row.get("bcp47_tag")).replace("_", "-").split("-")[0].lower()
    iso2 = _text(row.get("iso639_2_t")).lower()
    if len(bcp47) == 3 and bcp47.isalpha():
        return bcp47
    if len(iso2) == 3 and iso2.isalpha():
        return iso2
    if len(code) == 3 and code.isalpha() and not _bool(row.get("is_group_iso639_2")):
        return code.lower()
    return ""


def _cldr_tag_for_row(row: pd.Series) -> str:
    for column in ("bcp47_tag", "iso639_1", "iso639_2_t", "language_code"):
        value = _text(row.get(column)).replace("_", "-")
        if value:
            return value.split("-")[0].lower()
    return ""


def _cldr_population_by_language() -> dict[str, float]:
    """Use CLDR base totals; sum territory rows only when no base row exists."""
    base: dict[str, float] = {}
    territories: defaultdict[str, float] = defaultdict(float)
    for tag, value in LANGUAGE_SPEAKING_POPULATION.items():
        tag = str(tag)
        language = tag.split("-")[0]
        if "-" in tag:
            territories[language] += float(value)
        else:
            base[language] = float(value)
    return {language: base.get(language, total) for language, total in territories.items()} | base


def _load_glottolog(metadata_dir: Path) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    path = metadata_dir / "glottolog-cache" / "languoid.csv"
    glot = pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)
    languages = glot[(glot["level"] == "language") & glot["iso639P3code"].ne("")].copy()
    by_iso3 = {
        row["iso639P3code"]: {
            "glottocode": row["id"],
            "glottolog_name": row["name"],
            "glottolog_bookkeeping": row["bookkeeping"],
        }
        for _, row in languages.iterrows()
    }
    # Wikidata can occasionally expose only a Glottocode.
    iso3_by_glottocode = {
        row["id"]: row["iso639P3code"] for _, row in languages.iterrows()
    }
    return by_iso3, iso3_by_glottocode


def _wikidata_query(iso3_codes: list[str]) -> str:
    values = " ".join(json.dumps(code) for code in iso3_codes)
    return f"""
SELECT ?language ?languageLabel ?iso3 ?population ?pointInTime
       ?appliesToPart ?appliesToPartLabel ?jurisdiction ?jurisdictionLabel
       ?statedIn ?statedInLabel ?referenceUrl WHERE {{
  VALUES ?iso3 {{ {values} }}
  ?language wdt:P220 ?iso3;
            p:P1098 ?populationStatement.
  ?populationStatement ps:P1098 ?population.
  OPTIONAL {{ ?populationStatement pq:P585 ?pointInTime. }}
  OPTIONAL {{ ?populationStatement pq:P518 ?appliesToPart. }}
  OPTIONAL {{ ?populationStatement pq:P1001 ?jurisdiction. }}
  OPTIONAL {{
    ?populationStatement prov:wasDerivedFrom ?reference.
    OPTIONAL {{ ?reference pr:P248 ?statedIn. }}
    OPTIONAL {{ ?reference pr:P854 ?referenceUrl. }}
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""


def _fetch_wikidata(iso3_codes: list[str], cache_path: Path, cache_only: bool) -> list[dict]:
    cached: list[dict] = []
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
    if cache_only:
        if not cached:
            raise FileNotFoundError(f"No Wikidata cache exists at {cache_path}")
        return cached

    rows: list[dict] = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
    for start in range(0, len(iso3_codes), 75):
        chunk = iso3_codes[start : start + 75]
        response = session.get(
            WIKIDATA_ENDPOINT,
            params={"query": _wikidata_query(chunk), "format": "json"},
            timeout=90,
        )
        response.raise_for_status()
        rows.extend(response.json()["results"]["bindings"])
        time.sleep(0.25)
    cache_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def _binding(binding: dict, key: str) -> str:
    return binding.get(key, {}).get("value", "")


def _wikidata_measure(label: str) -> str:
    normalized = label.lower()
    if "native" in normalized or "first language" in normalized:
        return "l1_speakers"
    if "sign" in normalized:
        return "signers"
    if "second language" in normalized:
        return "l2_speakers"
    return "speakers_writers_or_signers_unspecified"


def _year(value: str) -> str:
    match = re.match(r"(-?\d{4})", value)
    return match.group(1) if match else ""


def _population_applicability(row: pd.Series, glottolog: dict[str, str]) -> tuple[str, str, str]:
    modern = _text(row.get("modern_language")).lower()
    name = _text(row.get("language_name")).lower()
    bookkeeping = _text(glottolog.get("glottolog_bookkeeping")).lower()
    if bookkeeping in {"true", "1", "yes"}:
        return "bookkeeping", "uncertain", "Glottolog marks this as a bookkeeping languoid."
    if modern == "false":
        return "historical_or_non_modern", "uncertain", "CLDR marks this as ancient, historical, or non-modern."
    if any(token in name for token in ("languages", "other", "miscellaneous", "uncoded")):
        return "collective_or_residual", "uncertain", "This appears to be a collective or residual category."
    return "current_or_unspecified", "yes", "A contemporary speaker estimate is conceptually applicable."


def _comparable_wikidata(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return rows
    return rows[
        rows["population_geographic_scope"].isin(["", "worldwide_or_unspecified"])
        & rows["population_measure"].eq("speakers_writers_or_signers_unspecified")
    ].copy()


def _wikidata_fallback_candidates(rows: pd.DataFrame) -> pd.DataFrame:
    """Return observations that can plausibly represent a whole-language count."""
    if rows.empty:
        return rows
    return rows[
        rows["population_geographic_scope"].isin(["", "worldwide_or_unspecified"])
    ].copy()


def build(metadata_dir: Path, cache_only: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    inventory_path = metadata_dir / "language_codes_comprehensive_family_reviewed.csv"
    if not inventory_path.exists():
        inventory_path = metadata_dir / "language_codes_comprehensive.csv"
    inventory = pd.read_csv(inventory_path, dtype=str, keep_default_na=False)
    glottolog_by_iso3, _ = _load_glottolog(metadata_dir)
    cldr_population = _cldr_population_by_language()

    identities = []
    for _, row in inventory.iterrows():
        iso3 = _iso3_for_row(row)
        glot = glottolog_by_iso3.get(iso3, {})
        status, applicable, note = _population_applicability(row, glot)
        identities.append({
            "language_code": _text(row.get("language_code")),
            "language_name": _text(row.get("language_name")),
            "iso639_3_population_match": iso3,
            "glottocode": glot.get("glottocode", ""),
            "glottolog_name": glot.get("glottolog_name", ""),
            "glottolog_bookkeeping": glot.get("glottolog_bookkeeping", ""),
            "population_status": status,
            "population_applicable": applicable,
            "population_applicability_note": note,
            "cldr_population_tag": _cldr_tag_for_row(row),
        })
    identity = pd.DataFrame(identities)

    cache_path = metadata_dir / "wikidata_population_cache.json"
    wikidata_raw = _fetch_wikidata(
        sorted({code for code in identity["iso639_3_population_match"] if code}),
        cache_path,
        cache_only,
    )

    evidence_rows: list[dict] = []
    for _, row in identity.iterrows():
        population = cldr_population.get(row["cldr_population_tag"])
        if population is not None and population > 0:
            evidence_rows.append({
                **row.to_dict(),
                "population_value": population,
                "population_source": "CLDR",
                "population_measure": "total_speakers_estimate",
                "population_reference_year": "",
                "population_geographic_scope": "worldwide",
                "population_citation": "language_data.LANGUAGE_SPEAKING_POPULATION (CLDR territoryInfo-derived)",
                "population_source_entity": "",
            })

    codes_to_rows: defaultdict[str, list[dict]] = defaultdict(list)
    for binding in wikidata_raw:
        codes_to_rows[_binding(binding, "iso3")].append(binding)
    for _, row in identity.iterrows():
        for binding in codes_to_rows[row["iso639_3_population_match"]]:
            population_raw = _binding(binding, "population")
            try:
                population_value = float(population_raw)
            except (TypeError, ValueError):
                # Wikidata represents some unknown-value statements as blank
                # nodes. They document missingness but are not estimates.
                continue
            part_label = _binding(binding, "appliesToPartLabel")
            jurisdiction = _binding(binding, "jurisdictionLabel")
            citation = _binding(binding, "referenceUrl") or _binding(binding, "statedInLabel")
            evidence_rows.append({
                **row.to_dict(),
                "population_value": population_value,
                "population_source": "Wikidata",
                "population_measure": _wikidata_measure(part_label),
                "population_reference_year": _year(_binding(binding, "pointInTime")),
                "population_geographic_scope": jurisdiction or "worldwide_or_unspecified",
                "population_citation": citation,
                "population_source_entity": _binding(binding, "language"),
            })

    evidence_columns = list(identity.columns) + [
        "population_value", "population_source", "population_measure",
        "population_reference_year", "population_geographic_scope",
        "population_citation", "population_source_entity",
    ]
    evidence = pd.DataFrame(evidence_rows, columns=evidence_columns).drop_duplicates()
    evidence = evidence.sort_values(
        ["language_code", "population_source", "population_reference_year", "population_value"],
        na_position="last",
    ).reset_index(drop=True)

    resolved_rows = []
    for _, ident in identity.iterrows():
        rows = evidence[evidence["language_code"].eq(ident["language_code"])]
        cldr = rows[rows["population_source"].eq("CLDR")]
        wikidata_all = rows[rows["population_source"].eq("Wikidata")]
        wikidata = _wikidata_fallback_candidates(wikidata_all)
        wikidata_comparable = _comparable_wikidata(wikidata_all)
        cldr_value = float(cldr.iloc[0]["population_value"]) if not cldr.empty else math.nan
        # Prefer the newest dated Wikidata observation; undated observations sort last.
        wikidata_choice = pd.Series(dtype=object)
        if not wikidata.empty:
            wikidata = wikidata.assign(
                _year_num=pd.to_numeric(wikidata["population_reference_year"], errors="coerce").fillna(-1)
            ).sort_values(["_year_num", "population_value"], ascending=[False, False])
            wikidata_choice = wikidata.iloc[0]
        wikidata_value = float(wikidata_choice["population_value"]) if not wikidata_choice.empty else math.nan

        comparable_choice = pd.Series(dtype=object)
        if not wikidata_comparable.empty:
            wikidata_comparable = wikidata_comparable.assign(
                _year_num=pd.to_numeric(
                    wikidata_comparable["population_reference_year"], errors="coerce"
                ).fillna(-1)
            ).sort_values(["_year_num", "population_value"], ascending=[False, False])
            comparable_choice = wikidata_comparable.iloc[0]
        comparable_value = (
            float(comparable_choice["population_value"])
            if not comparable_choice.empty else math.nan
        )

        if not math.isnan(cldr_value):
            selected = cldr.iloc[0]
            selection = "cldr_primary"
        elif not math.isnan(wikidata_value):
            selected = wikidata_choice
            selection = "wikidata_fallback"
        else:
            selected = pd.Series(dtype=object)
            selection = "not_applicable" if ident["population_applicable"] == "no" else "unknown"

        ratio = math.nan
        resolution = selection
        if not math.isnan(cldr_value) and not math.isnan(comparable_value):
            ratio = max(cldr_value, comparable_value) / min(cldr_value, comparable_value) if min(cldr_value, comparable_value) > 0 else math.nan
            resolution = "sources_agree" if ratio <= 2 else "sources_diverge"

        resolved_rows.append({
            **ident.to_dict(),
            "speaker_population_selected": selected.get("population_value", math.nan),
            "population_source_selected": selected.get("population_source", ""),
            "population_measure_selected": selected.get("population_measure", ""),
            "population_reference_year_selected": selected.get("population_reference_year", ""),
            "population_geographic_scope_selected": selected.get("population_geographic_scope", ""),
            "population_citation_selected": selected.get("population_citation", ""),
            "population_resolution": resolution,
            "cldr_population": cldr_value,
            "wikidata_population_comparable": comparable_value,
            "cldr_wikidata_ratio": ratio,
            "population_evidence_count": len(rows),
        })

    resolved = pd.DataFrame(resolved_rows)
    evidence.to_csv(metadata_dir / "language_population_evidence.csv", index=False)
    resolved.to_csv(metadata_dir / "language_population_resolved.csv", index=False)
    return evidence, resolved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-dir", type=Path, default=Path("datasets/metadata_files"))
    parser.add_argument("--cache-only", action="store_true", help="Rebuild from the saved Wikidata response.")
    args = parser.parse_args()
    evidence, resolved = build(args.metadata_dir, args.cache_only)
    print(f"Wrote {len(evidence):,} source observations for {len(resolved):,} language rows.")
    print(resolved["population_resolution"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
