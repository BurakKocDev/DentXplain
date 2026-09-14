from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXPECTED_CATEGORY_NAMES = {
    "categories_1": ["1", "2", "3", "4"],
    "categories_2": ["1", "2", "3", "4", "5", "6", "7", "8"],
    "categories_3": ["Impacted", "Caries", "Periapical Lesion", "Deep Caries"],
}


def load_annotations(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Annotation root must be a JSON object")
    return payload


def _category_map(payload: dict[str, Any], key: str) -> dict[int, str]:
    categories = payload.get(key)
    if not isinstance(categories, list):
        raise ValueError(f"Missing category list: {key}")

    mapping: dict[int, str] = {}
    for category in categories:
        if not isinstance(category, dict) or "id" not in category or "name" not in category:
            raise ValueError(f"Invalid category entry in {key}")
        mapping[int(category["id"])] = str(category["name"])
    return mapping


def audit_annotations(payload: dict[str, Any]) -> dict[str, Any]:
    images = payload.get("images")
    annotations = payload.get("annotations")
    if not isinstance(images, list) or not isinstance(annotations, list):
        raise ValueError("Annotation payload must contain images and annotations lists")

    category_maps = {
        key: _category_map(payload, key)
        for key in EXPECTED_CATEGORY_NAMES
        if key in payload
    }
    if not category_maps:
        raise ValueError("Annotation payload must contain at least one category list")
    category_schema_matches = {
        key: list(mapping.values()) == EXPECTED_CATEGORY_NAMES[key]
        for key, mapping in category_maps.items()
    }

    image_by_id = {int(image["id"]): image for image in images}
    image_ids = [int(image["id"]) for image in images]
    annotation_ids = [int(annotation["id"]) for annotation in annotations]
    annotations_per_image: Counter[int] = Counter()
    category_counts = {
        "quadrant": Counter(),
        "tooth_position": Counter(),
        "diagnosis": Counter(),
        "fdi": Counter(),
    }
    orphan_annotation_ids: list[int] = []
    invalid_bbox_ids: list[int] = []
    out_of_bounds_bbox_ids: list[int] = []
    annotation_identity: defaultdict[tuple, list[int]] = defaultdict(list)

    for annotation in annotations:
        annotation_id = int(annotation["id"])
        image_id = int(annotation["image_id"])
        identity = (
            image_id,
            annotation.get("category_id_1"),
            annotation.get("category_id_2"),
            annotation.get("category_id_3"),
            tuple(annotation.get("bbox", [])),
            tuple(tuple(polygon) for polygon in annotation.get("segmentation", [])),
        )
        annotation_identity[identity].append(annotation_id)
        annotations_per_image[image_id] += 1
        image = image_by_id.get(image_id)
        if image is None:
            orphan_annotation_ids.append(annotation_id)

        quadrant_map = category_maps.get("categories_1")
        tooth_map = category_maps.get("categories_2")
        diagnosis_map = category_maps.get("categories_3")
        quadrant = (
            quadrant_map.get(int(annotation["category_id_1"]))
            if quadrant_map is not None and "category_id_1" in annotation
            else None
        )
        tooth = (
            tooth_map.get(int(annotation["category_id_2"]))
            if tooth_map is not None and "category_id_2" in annotation
            else None
        )
        diagnosis = (
            diagnosis_map.get(int(annotation["category_id_3"]))
            if diagnosis_map is not None and "category_id_3" in annotation
            else None
        )
        if quadrant_map is not None:
            category_counts["quadrant"][quadrant or "UNKNOWN"] += 1
        if tooth_map is not None:
            category_counts["tooth_position"][tooth or "UNKNOWN"] += 1
        if diagnosis_map is not None:
            category_counts["diagnosis"][diagnosis or "UNKNOWN"] += 1
        if quadrant is not None and tooth is not None:
            category_counts["fdi"][f"{quadrant}{tooth}"] += 1

        bbox = annotation.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            invalid_bbox_ids.append(annotation_id)
            continue
        x, y, width, height = (float(value) for value in bbox)
        if width <= 0 or height <= 0:
            invalid_bbox_ids.append(annotation_id)
        if image is not None and (
            x < 0
            or y < 0
            or x + width > float(image["width"])
            or y + height > float(image["height"])
        ):
            out_of_bounds_bbox_ids.append(annotation_id)

    images_without_annotations = sorted(set(image_ids) - set(annotations_per_image))
    per_image_counts = [annotations_per_image.get(image_id, 0) for image_id in image_ids]
    return {
        "image_count": len(images),
        "annotation_count": len(annotations),
        "images_with_annotations": len(annotations_per_image),
        "images_without_annotations": images_without_annotations,
        "duplicate_image_id_count": len(image_ids) - len(set(image_ids)),
        "duplicate_annotation_id_count": len(annotation_ids) - len(set(annotation_ids)),
        "exact_duplicate_annotation_groups": sorted(
            sorted(ids) for ids in annotation_identity.values() if len(ids) > 1
        ),
        "orphan_annotation_ids": sorted(orphan_annotation_ids),
        "invalid_bbox_ids": sorted(invalid_bbox_ids),
        "out_of_bounds_bbox_ids": sorted(out_of_bounds_bbox_ids),
        "segmentation_annotation_count": sum(
            bool(annotation.get("segmentation")) for annotation in annotations
        ),
        "category_schema_matches": category_schema_matches,
        "category_counts": {
            key: dict(sorted(counts.items())) for key, counts in category_counts.items()
        },
        "annotations_per_image": {
            "minimum": min(per_image_counts, default=0),
            "maximum": max(per_image_counts, default=0),
            "mean": (
                round(len(annotations) / len(images), 4) if images else 0.0
            ),
        },
    }
