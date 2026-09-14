from __future__ import annotations

import pytest

from dentxplain.cascade import best_tooth_match, box_iou, center_proximity, match_score


def test_box_iou_and_center_proximity() -> None:
    assert box_iou((0, 0, 10, 10), (0, 0, 10, 10)) == pytest.approx(1.0)
    assert box_iou((0, 0, 10, 10), (10, 10, 20, 20)) == 0
    assert center_proximity((2, 2, 8, 8), (0, 0, 10, 10)) == pytest.approx(1.0)


def test_match_score_validates_weight() -> None:
    with pytest.raises(ValueError, match="between zero and one"):
        match_score((0, 0, 1, 1), (0, 0, 1, 1), iou_weight=1.1)


def test_best_tooth_match_filters_confidence_and_selects_geometry() -> None:
    teeth = [
        {"box_xyxy": [0, 0, 10, 10], "confidence": 0.9, "class_name": "11"},
        {"box_xyxy": [20, 0, 30, 10], "confidence": 0.8, "class_name": "12"},
        {"box_xyxy": [5, 0, 15, 10], "confidence": 0.1, "class_name": "13"},
    ]

    match = best_tooth_match(
        (1, 1, 9, 9),
        teeth,
        iou_weight=0.5,
        minimum_tooth_confidence=0.25,
    )

    assert match is not None
    assert match["class_name"] == "11"
    assert match["match_score"] > 0.5
