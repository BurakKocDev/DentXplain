from __future__ import annotations

from typing import Any

UPPER_ORDER = tuple(
    [f"1{position}" for position in range(8, 0, -1)]
    + [f"2{position}" for position in range(1, 9)]
)
LOWER_ORDER = tuple(
    [f"4{position}" for position in range(8, 0, -1)]
    + [f"3{position}" for position in range(1, 9)]
)


def _center_x(prediction: dict[str, Any]) -> float:
    box = prediction["box_xyxy"]
    return (float(box[0]) + float(box[2])) / 2


def _best_monotonic_arch(
    predictions: list[dict[str, Any]],
    expected_order: tuple[str, ...],
) -> list[dict[str, Any]]:
    rank = {fdi: index for index, fdi in enumerate(expected_order)}
    candidates = sorted(
        (prediction for prediction in predictions if prediction["class_name"] in rank),
        key=lambda prediction: (_center_x(prediction), rank[prediction["class_name"]]),
    )
    if not candidates:
        return []

    scores = [float(prediction["confidence"]) for prediction in candidates]
    previous: list[int | None] = [None] * len(candidates)
    for current_index, current in enumerate(candidates):
        current_rank = rank[current["class_name"]]
        current_x = _center_x(current)
        for candidate_index in range(current_index):
            candidate = candidates[candidate_index]
            if (
                rank[candidate["class_name"]] < current_rank
                and _center_x(candidate) < current_x
            ):
                proposed = scores[candidate_index] + float(current["confidence"])
                if proposed > scores[current_index]:
                    scores[current_index] = proposed
                    previous[current_index] = candidate_index

    selected_indices: list[int] = []
    index: int | None = max(range(len(candidates)), key=scores.__getitem__)
    while index is not None:
        selected_indices.append(index)
        index = previous[index]
    return [candidates[index] for index in reversed(selected_indices)]


def anatomy_constrained_teeth(
    predictions: list[dict[str, Any]],
    *,
    minimum_confidence: float,
) -> list[dict[str, Any]]:
    """Keep a maximum-confidence, one-to-one monotonic FDI sequence per arch."""
    eligible = [
        prediction
        for prediction in predictions
        if float(prediction["confidence"]) >= minimum_confidence
    ]
    upper = _best_monotonic_arch(eligible, UPPER_ORDER)
    lower = _best_monotonic_arch(eligible, LOWER_ORDER)
    return upper + lower
