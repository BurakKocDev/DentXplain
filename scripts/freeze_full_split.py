from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from dentxplain.data import load_annotations, stratified_file_split


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze the DENTEX full-label development split")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--duplicate-audit", type=Path, required=True)
    parser.add_argument("--holdout-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=20260913)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def distribution(file_names: list[str], signatures: dict[str, tuple[str, ...]]) -> dict:
    presence: Counter[str] = Counter()
    signature_counts: Counter[str] = Counter()
    for file_name in file_names:
        signature = signatures[file_name]
        presence.update(signature)
        signature_counts[" + ".join(signature)] += 1
    return {
        "image_count": len(file_names),
        "diagnosis_presence": dict(sorted(presence.items())),
        "signature_counts": dict(sorted(signature_counts.items())),
    }


def main() -> int:
    args = parse_args()
    payload = load_annotations(args.annotations)
    duplicate_audit = json.loads(args.duplicate_audit.read_text(encoding="utf-8"))

    full_exact_groups = [
        [member["file_name"] for member in group["members"] if member["collection"] == "full"]
        for group in duplicate_audit["exact_duplicate_groups"]
    ]
    full_exact_groups = [group for group in full_exact_groups if len(group) > 1]
    if full_exact_groups:
        raise ValueError(
            "The full-label pool contains exact duplicates; group-aware splitting is required"
        )

    category_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_3"]
    }
    image_names = {int(image["id"]): str(image["file_name"]) for image in payload["images"]}
    labels_by_image: defaultdict[int, set[str]] = defaultdict(set)
    for annotation in payload["annotations"]:
        labels_by_image[int(annotation["image_id"])].add(
            category_names[int(annotation["category_id_3"])]
        )
    signatures = {
        file_name: tuple(sorted(labels_by_image[image_id])) or ("NO_TARGET_ANNOTATION",)
        for image_id, file_name in image_names.items()
    }

    training, calibration_validation = stratified_file_split(
        signatures,
        holdout_fraction=args.holdout_fraction,
        seed=args.seed,
    )
    if set(training) & set(calibration_validation):
        raise RuntimeError("Split overlap detected")
    if set(training) | set(calibration_validation) != set(signatures):
        raise RuntimeError("Split does not cover the full development pool")

    final_exact_overlap = [
        group["members"]
        for group in duplicate_audit["exact_duplicate_groups"]
        if {member["collection"] for member in group["members"]} >= {"full", "locked_final"}
    ]
    if final_exact_overlap:
        raise RuntimeError("Full-label development pool overlaps the locked final set")

    manifest = {
        "schema_version": "1.0",
        "dataset": "DENTEX full-label development pool",
        "seed": args.seed,
        "holdout_fraction": args.holdout_fraction,
        "annotation_sha256": file_sha256(args.annotations),
        "duplicate_audit_sha256": file_sha256(args.duplicate_audit),
        "locked_final_policy": "Official 50-image validation cohort; never fit or tune",
        "training": training,
        "calibration_validation": calibration_validation,
        "distribution": {
            "all": distribution(sorted(signatures), signatures),
            "training": distribution(training, signatures),
            "calibration_validation": distribution(calibration_validation, signatures),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["distribution"], indent=2))
    print(f"manifest_sha256={file_sha256(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
