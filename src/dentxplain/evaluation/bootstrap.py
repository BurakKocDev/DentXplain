from __future__ import annotations

import math
import random
from typing import Any

METRICS = (
    "joint_precision",
    "joint_recall",
    "joint_f1",
    "fdi_accuracy_on_emitted_pathology_tp",
)


def aggregate_cascade_rows(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    counts = {
        key: sum(int(row[key]) for row in rows)
        for key in (
            "ground_truth_count",
            "emitted_count",
            "emitted_pathology_true_positive_count",
            "joint_correct_count",
        )
    }
    correct = counts["joint_correct_count"]
    emitted = counts["emitted_count"]
    targets = counts["ground_truth_count"]
    localized = counts["emitted_pathology_true_positive_count"]
    precision = correct / emitted if emitted else 0.0
    recall = correct / targets if targets else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        **counts,
        "joint_precision": precision,
        "joint_recall": recall,
        "joint_f1": f1,
        "fdi_accuracy_on_emitted_pathology_tp": (
            correct / localized if localized else 0.0
        ),
    }


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between zero and one")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def paired_cascade_bootstrap(
    first_rows: list[dict[str, Any]],
    second_rows: list[dict[str, Any]],
    *,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    if len(first_rows) != len(second_rows) or not first_rows:
        raise ValueError("paired rows must have the same non-zero length")
    if replicates <= 0:
        raise ValueError("replicates must be positive")

    random_generator = random.Random(seed)
    first_samples = {metric: [] for metric in METRICS}
    second_samples = {metric: [] for metric in METRICS}
    difference_samples = {metric: [] for metric in METRICS}
    for _ in range(replicates):
        indices = [random_generator.randrange(len(first_rows)) for _ in first_rows]
        first = aggregate_cascade_rows([first_rows[index] for index in indices])
        second = aggregate_cascade_rows([second_rows[index] for index in indices])
        for metric in METRICS:
            first_value = float(first[metric])
            second_value = float(second[metric])
            first_samples[metric].append(first_value)
            second_samples[metric].append(second_value)
            difference_samples[metric].append(second_value - first_value)

    first_point = aggregate_cascade_rows(first_rows)
    second_point = aggregate_cascade_rows(second_rows)

    def intervals(samples: dict[str, list[float]]) -> dict[str, list[float]]:
        return {
            metric: [percentile(values, 0.025), percentile(values, 0.975)]
            for metric, values in samples.items()
        }

    return {
        "replicates": replicates,
        "seed": seed,
        "first": {"point": first_point, "confidence_interval_95": intervals(first_samples)},
        "second": {
            "point": second_point,
            "confidence_interval_95": intervals(second_samples),
        },
        "second_minus_first": {
            "point": {
                metric: float(second_point[metric]) - float(first_point[metric])
                for metric in METRICS
            },
            "confidence_interval_95": intervals(difference_samples),
        },
    }
