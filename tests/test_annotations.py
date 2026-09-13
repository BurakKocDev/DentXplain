from __future__ import annotations

from dentxplain.data import audit_annotations


def valid_payload() -> dict:
    return {
        "images": [{"id": 1, "file_name": "sample.png", "width": 100, "height": 80}],
        "annotations": [
            {
                "id": 10,
                "image_id": 1,
                "bbox": [10, 20, 30, 40],
                "segmentation": [[10, 20, 40, 20, 40, 60, 10, 60]],
                "category_id_1": 3,
                "category_id_2": 7,
                "category_id_3": 0,
            }
        ],
        "categories_1": [
            {"id": 0, "name": "1"},
            {"id": 1, "name": "2"},
            {"id": 2, "name": "3"},
            {"id": 3, "name": "4"},
        ],
        "categories_2": [{"id": index, "name": str(index + 1)} for index in range(8)],
        "categories_3": [
            {"id": 0, "name": "Impacted"},
            {"id": 1, "name": "Caries"},
            {"id": 2, "name": "Periapical Lesion"},
            {"id": 3, "name": "Deep Caries"},
        ],
    }


def test_valid_hierarchical_annotation() -> None:
    report = audit_annotations(valid_payload())

    assert report["image_count"] == 1
    assert report["annotation_count"] == 1
    assert report["category_counts"]["fdi"] == {"48": 1}
    assert report["category_counts"]["diagnosis"] == {"Impacted": 1}
    assert report["invalid_bbox_ids"] == []
    assert report["out_of_bounds_bbox_ids"] == []
    assert all(report["category_schema_matches"].values())


def test_reports_orphan_and_out_of_bounds_boxes() -> None:
    payload = valid_payload()
    payload["annotations"].extend(
        [
            {
                "id": 11,
                "image_id": 1,
                "bbox": [90, 70, 20, 20],
                "category_id_1": 0,
                "category_id_2": 0,
                "category_id_3": 1,
            },
            {
                "id": 12,
                "image_id": 999,
                "bbox": [0, 0, 1, 1],
                "category_id_1": 0,
                "category_id_2": 0,
                "category_id_3": 1,
            },
        ]
    )

    report = audit_annotations(payload)

    assert report["out_of_bounds_bbox_ids"] == [11]
    assert report["orphan_annotation_ids"] == [12]


def test_zero_annotation_images_are_included_in_density_statistics() -> None:
    payload = valid_payload()
    payload["images"].append(
        {"id": 2, "file_name": "empty.png", "width": 100, "height": 80}
    )

    report = audit_annotations(payload)

    assert report["images_without_annotations"] == [2]
    assert report["annotations_per_image"] == {
        "minimum": 0,
        "maximum": 1,
        "mean": 0.5,
    }
