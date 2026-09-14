from __future__ import annotations

import pytest

from dentxplain.evaluation import (
    aggregate_cascade_rows,
    paired_cascade_bootstrap,
)


def row(*, targets: int, emitted: int, localized: int, correct: int) -> dict[str, int]:
    return {
        "ground_truth_count": targets,
        "emitted_count": emitted,
        "emitted_pathology_true_positive_count": localized,
        "joint_correct_count": correct,
    }


def test_aggregate_cascade_rows_recomputes_micro_metrics() -> None:
    result = aggregate_cascade_rows(
        [
            row(targets=2, emitted=2, localized=2, correct=1),
            row(targets=1, emitted=1, localized=1, correct=1),
        ]
    )

    assert result["joint_precision"] == pytest.approx(2 / 3)
    assert result["joint_recall"] == pytest.approx(2 / 3)
    assert result["joint_f1"] == pytest.approx(2 / 3)


def test_paired_bootstrap_is_deterministic_and_reports_difference() -> None:
    first = [row(targets=1, emitted=1, localized=1, correct=0)] * 2
    second = [row(targets=1, emitted=1, localized=1, correct=1)] * 2

    result = paired_cascade_bootstrap(first, second, replicates=20, seed=7)

    assert result["second_minus_first"]["point"]["joint_f1"] == 1.0
    assert result["second_minus_first"]["confidence_interval_95"]["joint_f1"] == [
        1.0,
        1.0,
    ]


def test_paired_bootstrap_validates_inputs() -> None:
    with pytest.raises(ValueError, match="same non-zero length"):
        paired_cascade_bootstrap([], [], replicates=1, seed=1)
