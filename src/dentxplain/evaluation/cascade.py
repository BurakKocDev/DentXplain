from __future__ import annotations

from collections import defaultdict
from typing import Any

from dentxplain.cascade import anatomy_constrained_teeth, best_tooth_match, box_iou


def cascade_ground_truth_by_image(
    payload: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    image_name_by_id = {
        int(image["id"]): str(image["file_name"]) for image in payload["images"]
    }
    quadrant_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_1"]
    }
    tooth_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_2"]
    }
    diagnosis_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_3"]
    }
    output: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for annotation in payload["annotations"]:
        x, y, width, height = (float(value) for value in annotation["bbox"])
        output[image_name_by_id[int(annotation["image_id"])]].append(
            {
                "box_xyxy": (x, y, x + width, y + height),
                "diagnosis": diagnosis_names[int(annotation["category_id_3"])],
                "fdi": (
                    f"{quadrant_names[int(annotation['category_id_1'])]}"
                    f"{tooth_names[int(annotation['category_id_2'])]}"
                ),
            }
        )
    return dict(output)


def match_pathology_predictions(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
) -> dict[int, int]:
    matched_ground_truth: set[int] = set()
    matches: dict[int, int] = {}
    ordered_predictions = sorted(
        enumerate(predictions),
        key=lambda item: float(item[1]["confidence"]),
        reverse=True,
    )
    for prediction_index, prediction in ordered_predictions:
        candidates = [
            (ground_truth_index, box_iou(tuple(prediction["box_xyxy"]), truth["box_xyxy"]))
            for ground_truth_index, truth in enumerate(ground_truth)
            if ground_truth_index not in matched_ground_truth
            and prediction["class_name"] == truth["diagnosis"]
        ]
        if not candidates:
            continue
        ground_truth_index, overlap = max(candidates, key=lambda item: item[1])
        if overlap >= 0.5:
            matches[prediction_index] = ground_truth_index
            matched_ground_truth.add(ground_truth_index)
    return matches


def evaluate_cascade_configuration(
    cached_images: dict[str, Any],
    ground_truth: dict[str, list[dict[str, Any]]],
    *,
    b0_confidence: float,
    b1_confidence: float,
    iou_weight: float,
    match_threshold: float,
    anatomy_constrained: bool,
) -> dict[str, float | int]:
    total_ground_truth = 0
    b0_predictions = 0
    b0_true_positives = 0
    emitted = 0
    joint_correct = 0
    emitted_pathology_true_positives = 0

    for file_name, cached in cached_images.items():
        truths = ground_truth.get(file_name, [])
        total_ground_truth += len(truths)
        pathology = [
            prediction
            for prediction in cached["b0"]["predictions"]
            if float(prediction["confidence"]) >= b0_confidence
        ]
        teeth = cached["b1"]["predictions"]
        if anatomy_constrained:
            teeth = anatomy_constrained_teeth(
                teeth,
                minimum_confidence=b1_confidence,
            )
        pathology_matches = match_pathology_predictions(pathology, truths)
        b0_predictions += len(pathology)
        b0_true_positives += len(pathology_matches)

        for prediction_index, prediction in enumerate(pathology):
            tooth_match = best_tooth_match(
                tuple(prediction["box_xyxy"]),
                teeth,
                iou_weight=iou_weight,
                minimum_tooth_confidence=b1_confidence,
            )
            if tooth_match is None or float(tooth_match["match_score"]) < match_threshold:
                continue
            emitted += 1
            truth_index = pathology_matches.get(prediction_index)
            if truth_index is None:
                continue
            emitted_pathology_true_positives += 1
            if tooth_match["class_name"] == truths[truth_index]["fdi"]:
                joint_correct += 1

    joint_precision = joint_correct / emitted if emitted else 0.0
    joint_recall = joint_correct / total_ground_truth if total_ground_truth else 0.0
    joint_f1 = (
        2 * joint_precision * joint_recall / (joint_precision + joint_recall)
        if joint_precision + joint_recall
        else 0.0
    )
    return {
        "b0_confidence": b0_confidence,
        "b1_confidence": b1_confidence,
        "iou_weight": iou_weight,
        "match_threshold": match_threshold,
        "ground_truth_count": total_ground_truth,
        "b0_prediction_count": b0_predictions,
        "b0_true_positive_count": b0_true_positives,
        "b0_precision_at_iou50": (
            b0_true_positives / b0_predictions if b0_predictions else 0.0
        ),
        "b0_recall_at_iou50": b0_true_positives / total_ground_truth,
        "emitted_count": emitted,
        "abstained_prediction_count": b0_predictions - emitted,
        "emitted_pathology_true_positive_count": emitted_pathology_true_positives,
        "joint_correct_count": joint_correct,
        "wrong_fdi_on_emitted_pathology_tp": emitted_pathology_true_positives - joint_correct,
        "joint_precision": joint_precision,
        "joint_recall": joint_recall,
        "joint_f1": joint_f1,
        "fdi_accuracy_on_emitted_pathology_tp": (
            joint_correct / emitted_pathology_true_positives
            if emitted_pathology_true_positives
            else 0.0
        ),
        "assignment_coverage_on_pathology_tp": (
            emitted_pathology_true_positives / b0_true_positives
            if b0_true_positives
            else 0.0
        ),
    }
