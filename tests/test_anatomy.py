from __future__ import annotations

from dentxplain.cascade import anatomy_constrained_teeth


def tooth(fdi: str, center_x: float, confidence: float) -> dict:
    return {
        "class_name": fdi,
        "confidence": confidence,
        "box_xyxy": [center_x - 1, 0, center_x + 1, 4],
    }


def test_anatomy_constraint_keeps_monotonic_arch_and_rejects_conflict() -> None:
    predictions = [
        tooth("18", 10, 0.9),
        tooth("17", 20, 0.9),
        tooth("28", 15, 0.2),
        tooth("16", 30, 0.9),
    ]

    selected = anatomy_constrained_teeth(predictions, minimum_confidence=0.1)

    assert [prediction["class_name"] for prediction in selected] == ["18", "17", "16"]


def test_anatomy_constraint_keeps_only_one_candidate_per_fdi() -> None:
    predictions = [tooth("11", 10, 0.4), tooth("11", 11, 0.9)]

    selected = anatomy_constrained_teeth(predictions, minimum_confidence=0.1)

    assert len(selected) == 1
    assert selected[0]["confidence"] == 0.9


def test_anatomy_constraint_filters_low_confidence() -> None:
    selected = anatomy_constrained_teeth(
        [tooth("11", 10, 0.2), tooth("41", 10, 0.8)],
        minimum_confidence=0.5,
    )

    assert [prediction["class_name"] for prediction in selected] == ["41"]
