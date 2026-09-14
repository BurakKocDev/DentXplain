from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

PRIMARY_METRIC = "metrics/mAP50-95(B)"
METRIC_FIELDS = (
    "metrics/precision(B)",
    "metrics/recall(B)",
    "metrics/mAP50(B)",
    PRIMARY_METRIC,
)
LOSS_FIELDS = (
    "train/box_loss",
    "train/cls_loss",
    "train/dfl_loss",
    "val/box_loss",
    "val/cls_loss",
    "val/dfl_loss",
)


def _normalize_row(row: dict[str, str]) -> dict[str, float | int]:
    normalized: dict[str, float | int] = {"epoch": int(float(row["epoch"]))}
    for field in (*METRIC_FIELDS, *LOSS_FIELDS):
        normalized[field] = float(row[field])
    return normalized


def summarize_results(results_csv: Path) -> dict[str, Any]:
    """Return a compact, machine-readable summary of an Ultralytics results CSV."""
    with results_csv.open(encoding="utf-8", newline="") as handle:
        rows = [_normalize_row(row) for row in csv.DictReader(handle)]

    if not rows:
        raise ValueError(f"No completed epochs found in {results_csv}")

    best = max(rows, key=lambda row: float(row[PRIMARY_METRIC]))
    return {
        "schema_version": "1.0",
        "selection_rule": f"maximum {PRIMARY_METRIC} on development validation",
        "completed_epochs": len(rows),
        "best": best,
        "last": rows[-1],
    }
