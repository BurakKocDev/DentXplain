from __future__ import annotations

import pytest

from dentxplain.evaluation import analyze_detection_errors, greedy_detection_matches


def test_greedy_detection_matches_respects_class_and_iou() -> None:
    predictions = [
        {"box_xyxy": [0, 0, 10, 10], "confidence": 0.9, "class_name": "Caries"},
        {"box_xyxy": [20, 0, 30, 10], "confidence": 0.8, "class_name": "Deep"},
    ]
    targets = [
        {"box_xyxy": [0, 0, 10, 10], "class_name": "Caries"},
        {"box_xyxy": [20, 0, 30, 10], "class_name": "Caries"},
    ]

    matches, matched_predictions, matched_targets = greedy_detection_matches(
        predictions, targets
    )

    assert matches == {0: 0}
    assert matched_predictions == {0}
    assert matched_targets == {0}


def test_error_analysis_counts_and_exposes_label_swap() -> None:
    predictions = {
        "a.png": [
            {"box_xyxy": [0, 0, 10, 10], "confidence": 0.9, "class_name": "Caries"},
            {"box_xyxy": [20, 0, 30, 10], "confidence": 0.8, "class_name": "Deep"},
            {"box_xyxy": [40, 0, 50, 10], "confidence": 0.1, "class_name": "Caries"},
        ]
    }
    targets = {
        "a.png": [
            {"box_xyxy": [0, 0, 10, 10], "class_name": "Caries"},
            {"box_xyxy": [20, 0, 30, 10], "class_name": "Periapical"},
        ]
    }

    report = analyze_detection_errors(
        predictions,
        targets,
        confidence_threshold=0.2,
    )

    assert report["overall"] == {
        "true_positive_count": 1,
        "false_positive_count": 1,
        "false_negative_count": 1,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }
    assert report["likely_class_confusions"] == [
        {"ground_truth": "Periapical", "predicted": "Deep", "count": 1}
    ]


def test_error_analysis_validates_thresholds() -> None:
    with pytest.raises(ValueError, match="confidence_threshold"):
        analyze_detection_errors({}, {}, confidence_threshold=1.1)
    with pytest.raises(ValueError, match="iou_threshold"):
        greedy_detection_matches([], [], iou_threshold=-0.1)
