from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from dentxplain.data import grouped_stratified_file_split, load_annotations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze the leakage-safe B1 FDI split")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--duplicate-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--holdout-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=20260913)
    return parser.parse_args()


def fdi_name(
    annotation: dict,
    quadrant_names: dict[int, str],
    tooth_names: dict[int, str],
) -> str:
    quadrant = quadrant_names[int(annotation["category_id_1"])]
    position = tooth_names[int(annotation["category_id_2"])]
    return f"{quadrant}{position}"


def count_boxes(
    file_names: list[str], annotations_by_name: dict[str, list[str]]
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for file_name in file_names:
        counts.update(annotations_by_name[file_name])
    return dict(sorted(counts.items()))


def main() -> int:
    args = parse_args()
    payload = load_annotations(args.annotations)
    audit = json.loads(args.duplicate_audit.read_text(encoding="utf-8"))

    quadrant_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_1"]
    }
    tooth_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_2"]
    }
    image_name_by_id = {
        int(image["id"]): str(image["file_name"]) for image in payload["images"]
    }
    annotations_by_name: defaultdict[str, list[str]] = defaultdict(list)
    for annotation in payload["annotations"]:
        file_name = image_name_by_id[int(annotation["image_id"])]
        annotations_by_name[file_name].append(
            fdi_name(annotation, quadrant_names, tooth_names)
        )

    records = audit["records"]
    hash_by_enumeration_file = {
        str(record["file_name"]): str(record["sha256"])
        for record in records
        if record["collection"] == "enumeration"
    }
    locked_hashes = {
        str(record["sha256"])
        for record in records
        if record["collection"] == "locked_final"
    }
    annotation_files = set(image_name_by_id.values())
    if set(hash_by_enumeration_file) != annotation_files:
        raise ValueError("Duplicate audit and enumeration annotation file sets differ")

    excluded = sorted(
        file_name
        for file_name, sha256 in hash_by_enumeration_file.items()
        if sha256 in locked_hashes
    )
    eligible = sorted(annotation_files - set(excluded))
    signatures = {
        file_name: tuple(sorted(set(annotations_by_name[file_name])))
        for file_name in eligible
    }
    groups = {file_name: hash_by_enumeration_file[file_name] for file_name in eligible}
    training, calibration_validation = grouped_stratified_file_split(
        signatures,
        groups,
        holdout_fraction=args.holdout_fraction,
        seed=args.seed,
    )

    train_hashes = {groups[file_name] for file_name in training}
    validation_hashes = {groups[file_name] for file_name in calibration_validation}
    if train_hashes & validation_hashes:
        raise AssertionError("Exact-image group crossed the B1 split")

    duplicate_groups: defaultdict[str, list[str]] = defaultdict(list)
    for file_name in eligible:
        duplicate_groups[groups[file_name]].append(file_name)
    internal_duplicate_groups = sorted(
        sorted(members) for members in duplicate_groups.values() if len(members) > 1
    )
    manifest = {
        "schema_version": "1.0",
        "purpose": "B1 FDI tooth detector development split",
        "source_annotations": str(args.annotations),
        "duplicate_audit": str(args.duplicate_audit),
        "seed": args.seed,
        "holdout_fraction": args.holdout_fraction,
        "locked_final_overlap_exclusion": {
            "count": len(excluded),
            "files": excluded,
        },
        "eligible_image_count": len(eligible),
        "internal_exact_duplicate_groups": internal_duplicate_groups,
        "training": training,
        "calibration_validation": calibration_validation,
        "statistics": {
            "training": {
                "image_count": len(training),
                "box_count": sum(len(annotations_by_name[name]) for name in training),
                "fdi_box_counts": count_boxes(training, annotations_by_name),
            },
            "calibration_validation": {
                "image_count": len(calibration_validation),
                "box_count": sum(
                    len(annotations_by_name[name]) for name in calibration_validation
                ),
                "fdi_box_counts": count_boxes(calibration_validation, annotations_by_name),
            },
        },
    }
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    digest = hashlib.sha256(rendered.encode()).hexdigest()
    print(json.dumps(manifest["statistics"], indent=2))
    print(f"excluded_locked_final_overlap={len(excluded)}")
    print(f"internal_exact_duplicate_groups={len(internal_duplicate_groups)}")
    print(f"manifest_sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
