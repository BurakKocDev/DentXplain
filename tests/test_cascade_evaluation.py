from __future__ import annotations

from dentxplain.evaluation import (
    cascade_ground_truth_by_image,
    evaluate_cascade_configuration,
)


def test_ground_truth_builds_diagnosis_and_fdi() -> None:
    payload = {
        "images": [{"id": 1, "file_name": "a.png"}],
        "categories_1": [{"id": 0, "name": "2"}],
        "categories_2": [{"id": 0, "name": "6"}],
        "categories_3": [{"id": 0, "name": "Caries"}],
        "annotations": [
            {
                "image_id": 1,
                "category_id_1": 0,
                "category_id_2": 0,
                "category_id_3": 0,
                "bbox": [1, 2, 3, 4],
            }
        ],
    }

    assert cascade_ground_truth_by_image(payload) == {
        "a.png": [
            {"box_xyxy": (1.0, 2.0, 4.0, 6.0), "diagnosis": "Caries", "fdi": "26"}
        ]
    }


def test_fixed_cascade_counts_joint_correct_prediction() -> None:
    cached = {
        "a.png": {
            "b0": {
                "predictions": [
                    {
                        "box_xyxy": [0, 0, 10, 10],
                        "confidence": 0.9,
                        "class_name": "Caries",
                    }
                ]
            },
            "b1": {
                "predictions": [
                    {"box_xyxy": [0, 0, 10, 10], "confidence": 0.9, "class_name": "11"}
                ]
            },
        }
    }
    truth = {
        "a.png": [{"box_xyxy": (0, 0, 10, 10), "diagnosis": "Caries", "fdi": "11"}]
    }

    result = evaluate_cascade_configuration(
        cached,
        truth,
        b0_confidence=0.2,
        b1_confidence=0.1,
        iou_weight=1.0,
        match_threshold=0.5,
        anatomy_constrained=False,
    )

    assert result["joint_correct_count"] == 1
    assert result["joint_f1"] == 1.0
