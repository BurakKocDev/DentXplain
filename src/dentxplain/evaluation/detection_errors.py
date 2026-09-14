from __future__ import annotations

from collections import Counter
from typing import Any

from dentxplain.cascade import box_iou


def greedy_detection_matches(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    *,
    iou_threshold: float = 0.5,
) -> tuple[dict[int, int], set[int], set[int]]:
    """Match detections to same-class targets in descending confidence order."""
    if not 0 <= iou_threshold <= 1:
        raise ValueError("iou_threshold must be between zero and one")

    matched_targets: set[int] = set()
    matches: dict[int, int] = {}
    ordered_predictions = sorted(
        enumerate(predictions),
        key=lambda item: float(item[1]["confidence"]),
        reverse=True,
    )
    for prediction_index, prediction in ordered_predictions:
        candidates = [
            (
                target_index,
                box_iou(
                    tuple(float(value) for value in prediction["box_xyxy"]),
                    tuple(float(value) for value in target["box_xyxy"]),
                ),
            )
            for target_index, target in enumerate(ground_truth)
            if target_index not in matched_targets
            and prediction["class_name"] == target["class_name"]
        ]
        if not candidates:
            continue
        target_index, overlap = max(candidates, key=lambda item: item[1])
        if overlap >= iou_threshold:
            matches[prediction_index] = target_index
            matched_targets.add(target_index)

    return matches, set(matches), matched_targets


def _safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def analyze_detection_errors(
    predictions_by_image: dict[str, list[dict[str, Any]]],
    ground_truth_by_image: dict[str, list[dict[str, Any]]],
    *,
    confidence_threshold: float,
    iou_threshold: float = 0.5,
) -> dict[str, Any]:
    """Summarize B0 false positives, misses, and likely class confusions."""
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence_threshold must be between zero and one")

    class_counts: dict[str, Counter[str]] = {}
    confusion_counts: Counter[tuple[str, str]] = Counter()
    false_positives: list[dict[str, Any]] = []
    false_negatives: list[dict[str, Any]] = []
    image_rows: list[dict[str, Any]] = []

    image_names = sorted(set(predictions_by_image) | set(ground_truth_by_image))
    for image_name in image_names:
        predictions = [
            prediction
            for prediction in predictions_by_image.get(image_name, [])
            if float(prediction["confidence"]) >= confidence_threshold
        ]
        targets = ground_truth_by_image.get(image_name, [])
        matches, matched_predictions, matched_targets = greedy_detection_matches(
            predictions,
            targets,
            iou_threshold=iou_threshold,
        )

        for target_index in matches.values():
            class_name = str(targets[target_index]["class_name"])
            class_counts.setdefault(class_name, Counter())["tp"] += 1

        unmatched_prediction_indices = [
            index for index in range(len(predictions)) if index not in matched_predictions
        ]
        unmatched_target_indices = [
            index for index in range(len(targets)) if index not in matched_targets
        ]
        for prediction_index in unmatched_prediction_indices:
            prediction = predictions[prediction_index]
            class_name = str(prediction["class_name"])
            class_counts.setdefault(class_name, Counter())["fp"] += 1
            false_positives.append(
                {
                    "image": image_name,
                    "class_name": class_name,
                    "confidence": float(prediction["confidence"]),
                    "box_xyxy": prediction["box_xyxy"],
                }
            )
        for target_index in unmatched_target_indices:
            target = targets[target_index]
            class_name = str(target["class_name"])
            class_counts.setdefault(class_name, Counter())["fn"] += 1
            false_negatives.append(
                {
                    "image": image_name,
                    "class_name": class_name,
                    "box_xyxy": target["box_xyxy"],
                }
            )

        # Pair remaining boxes geometrically to expose likely label swaps.
        available_targets = set(unmatched_target_indices)
        for prediction_index in sorted(
            unmatched_prediction_indices,
            key=lambda index: float(predictions[index]["confidence"]),
            reverse=True,
        ):
            prediction = predictions[prediction_index]
            candidates = [
                (
                    target_index,
                    box_iou(
                        tuple(float(value) for value in prediction["box_xyxy"]),
                        tuple(float(value) for value in targets[target_index]["box_xyxy"]),
                    ),
                )
                for target_index in available_targets
                if prediction["class_name"] != targets[target_index]["class_name"]
            ]
            if not candidates:
                continue
            target_index, overlap = max(candidates, key=lambda item: item[1])
            if overlap >= iou_threshold:
                confusion_counts[
                    (
                        str(targets[target_index]["class_name"]),
                        str(prediction["class_name"]),
                    )
                ] += 1
                available_targets.remove(target_index)

        image_rows.append(
            {
                "image": image_name,
                "ground_truth_count": len(targets),
                "prediction_count": len(predictions),
                "true_positive_count": len(matches),
                "false_positive_count": len(unmatched_prediction_indices),
                "false_negative_count": len(unmatched_target_indices),
                "error_count": len(unmatched_prediction_indices) + len(unmatched_target_indices),
            }
        )

    class_names = sorted(class_counts)
    by_class: dict[str, dict[str, float | int]] = {}
    for class_name in class_names:
        counts = class_counts[class_name]
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        precision = _safe_ratio(tp, tp + fp)
        recall = _safe_ratio(tp, tp + fn)
        by_class[class_name] = {
            "true_positive_count": tp,
            "false_positive_count": fp,
            "false_negative_count": fn,
            "precision": precision,
            "recall": recall,
            "f1": _safe_ratio(2 * tp, 2 * tp + fp + fn),
        }

    total_tp = sum(int(row["true_positive_count"]) for row in by_class.values())
    total_fp = sum(int(row["false_positive_count"]) for row in by_class.values())
    total_fn = sum(int(row["false_negative_count"]) for row in by_class.values())
    return {
        "confidence_threshold": confidence_threshold,
        "iou_threshold": iou_threshold,
        "image_count": len(image_names),
        "overall": {
            "true_positive_count": total_tp,
            "false_positive_count": total_fp,
            "false_negative_count": total_fn,
            "precision": _safe_ratio(total_tp, total_tp + total_fp),
            "recall": _safe_ratio(total_tp, total_tp + total_fn),
            "f1": _safe_ratio(2 * total_tp, 2 * total_tp + total_fp + total_fn),
        },
        "by_class": by_class,
        "likely_class_confusions": [
            {"ground_truth": pair[0], "predicted": pair[1], "count": count}
            for pair, count in confusion_counts.most_common()
        ],
        "hardest_images": sorted(
            image_rows,
            key=lambda row: (
                int(row["error_count"]),
                int(row["false_negative_count"]),
                int(row["false_positive_count"]),
            ),
            reverse=True,
        )[:25],
        "high_confidence_false_positives": sorted(
            false_positives,
            key=lambda row: float(row["confidence"]),
            reverse=True,
        )[:50],
        "false_negatives": false_negatives,
    }
