from __future__ import annotations

import math
from typing import Any

Box = tuple[float, float, float, float]


def box_iou(first: Box, second: Box) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = first_area + second_area - intersection
    return intersection / union if union > 0 else 0.0


def center_proximity(pathology_box: Box, tooth_box: Box) -> float:
    pathology_x = (pathology_box[0] + pathology_box[2]) / 2
    pathology_y = (pathology_box[1] + pathology_box[3]) / 2
    tooth_x = (tooth_box[0] + tooth_box[2]) / 2
    tooth_y = (tooth_box[1] + tooth_box[3]) / 2
    distance = math.hypot(pathology_x - tooth_x, pathology_y - tooth_y)
    tooth_diagonal = math.hypot(tooth_box[2] - tooth_box[0], tooth_box[3] - tooth_box[1])
    if tooth_diagonal <= 0:
        return 0.0
    return max(0.0, 1.0 - distance / tooth_diagonal)


def match_score(pathology_box: Box, tooth_box: Box, *, iou_weight: float) -> float:
    if not 0 <= iou_weight <= 1:
        raise ValueError("iou_weight must be between zero and one")
    return iou_weight * box_iou(pathology_box, tooth_box) + (
        1 - iou_weight
    ) * center_proximity(pathology_box, tooth_box)


def best_tooth_match(
    pathology_box: Box,
    tooth_predictions: list[dict[str, Any]],
    *,
    iou_weight: float,
    minimum_tooth_confidence: float,
) -> dict[str, Any] | None:
    eligible = [
        prediction
        for prediction in tooth_predictions
        if float(prediction["confidence"]) >= minimum_tooth_confidence
    ]
    if not eligible:
        return None

    scored = [
        {
            **prediction,
            "match_score": match_score(
                pathology_box,
                tuple(float(value) for value in prediction["box_xyxy"]),
                iou_weight=iou_weight,
            ),
        }
        for prediction in eligible
    ]
    return max(scored, key=lambda prediction: prediction["match_score"])
