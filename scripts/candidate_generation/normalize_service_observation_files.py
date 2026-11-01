#!/usr/bin/env python3
"""Normalize historical per-service candidate files to service-local schemas."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.table import Table

from scripts.candidate_generation.translation_versions import (
    add_transmogrifier_ids,
    infer_service_context,
    select_service_observation_columns,
)
from scripts.utils import get_data_directory_path

console = Console()


def normalize_file(path: Path, *, apply: bool) -> dict[str, object]:
    """Normalize one CSV without collapsing historical observations."""
    service, prompt_variant = infer_service_context(path)
    original_size = path.stat().st_size
    frame = pd.read_csv(path, converters={"language_code": str}, on_bad_lines="warn")
    original_columns = len(frame.columns)
    normalized = add_transmogrifier_ids(
        frame,
        service=service,
        prompt_variant=prompt_variant,
    )
    normalized = select_service_observation_columns(normalized, service=service)

    if normalized["transmogrifier_id"].duplicated().any():
        duplicate_count = int(normalized["transmogrifier_id"].duplicated().sum())
        raise ValueError(f"{path.name}: {duplicate_count} duplicate observation IDs")

    if apply:
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        normalized.to_csv(temporary_path, index=False, quoting=csv.QUOTE_ALL)
        temporary_path.replace(path)

    projected_size = path.stat().st_size if apply else len(
        normalized.to_csv(index=False, quoting=csv.QUOTE_ALL).encode("utf-8")
    )
    return {
        "file": path.name,
        "rows": len(normalized),
        "before_columns": original_columns,
        "after_columns": len(normalized.columns),
        "before_mb": original_size / 1_000_000,
        "after_mb": projected_size / 1_000_000,
    }


def normalize_prompt_service_files(
    data_directory: Path,
    *,
    term_slug: str,
    apply: bool,
) -> list[dict[str, object]]:
    prompt_directory = data_directory / "candidate_terms" / term_slug / "prompt_services"
    if not prompt_directory.is_dir():
        raise FileNotFoundError(f"Prompt-service directory not found: {prompt_directory}")
    return [
        normalize_file(path, apply=apply)
        for path in sorted(prompt_directory.glob("*.csv"))
    ]


def print_summary(results: list[dict[str, object]], *, apply: bool) -> None:
    table = Table(title="Service observation schema migration")
    columns = ("file", "rows", "before_columns", "after_columns", "before_mb", "after_mb")
    for column in columns:
        table.add_column(column)
    for result in results:
        table.add_row(*[
            f"{result[column]:.2f}" if column.endswith("_mb") else str(result[column])
            for column in columns
        ])
    console.print(table)
    before = sum(float(result["before_mb"]) for result in results)
    after = sum(float(result["after_mb"]) for result in results)
    action = "Migrated" if apply else "Projected"
    console.print(
        f"{action} {len(results)} files: {before:.1f} MB -> {after:.1f} MB "
        f"({(1 - after / before) * 100:.1f}% reduction)",
        style="bold green" if apply else "bold cyan",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--term", default="digital_humanities", help="Term directory slug")
    parser.add_argument("--data-directory", type=Path, help="Override the configured datasets directory")
    parser.add_argument("--apply", action="store_true", help="Rewrite files atomically; otherwise preview only")
    args = parser.parse_args()
    data_directory = args.data_directory or Path(get_data_directory_path())
    results = normalize_prompt_service_files(
        data_directory,
        term_slug=args.term,
        apply=args.apply,
    )
    print_summary(results, apply=args.apply)


if __name__ == "__main__":
    main()
