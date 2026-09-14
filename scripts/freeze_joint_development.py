from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze a B0/B1 joint development cohort unseen by both models"
    )
    parser.add_argument("--duplicate-audit", type=Path, required=True)
    parser.add_argument("--b0-split", type=Path, required=True)
    parser.add_argument("--b1-split", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = json.loads(args.duplicate_audit.read_text(encoding="utf-8"))
    b0_split = json.loads(args.b0_split.read_text(encoding="utf-8"))
    b1_split = json.loads(args.b1_split.read_text(encoding="utf-8"))

    full_hashes = {
        str(record["file_name"]): str(record["sha256"])
        for record in audit["records"]
        if record["collection"] == "full"
    }
    enumeration_hashes = {
        str(record["file_name"]): str(record["sha256"])
        for record in audit["records"]
        if record["collection"] == "enumeration"
    }
    b1_training_hashes = {
        enumeration_hashes[file_name] for file_name in b1_split["training"]
    }
    b1_validation_hashes = {
        enumeration_hashes[file_name]
        for file_name in b1_split["calibration_validation"]
    }

    excluded_b1_training_overlap: list[str] = []
    joint_development: list[str] = []
    for file_name in b0_split["calibration_validation"]:
        if full_hashes[file_name] in b1_training_hashes:
            excluded_b1_training_overlap.append(file_name)
        else:
            joint_development.append(file_name)

    joint_hashes = {full_hashes[file_name] for file_name in joint_development}
    if joint_hashes & b1_training_hashes:
        raise AssertionError("B1 training image leaked into joint development")

    manifest = {
        "schema_version": "1.0",
        "purpose": "B2/C1 threshold selection and development comparison",
        "source": {
            "duplicate_audit": str(args.duplicate_audit),
            "b0_split": str(args.b0_split),
            "b1_split": str(args.b1_split),
        },
        "rule": (
            "B0 calibration-validation images excluding every exact encoded-image "
            "SHA-256 observed in B1 training"
        ),
        "b0_calibration_validation_count": len(b0_split["calibration_validation"]),
        "excluded_b1_training_overlap": {
            "count": len(excluded_b1_training_overlap),
            "files": sorted(excluded_b1_training_overlap),
        },
        "joint_development": sorted(joint_development),
        "joint_development_count": len(joint_development),
        "exact_overlap_with_b1_validation_count": len(
            joint_hashes & b1_validation_hashes
        ),
        "locked_final_status": "untouched",
    }
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    digest = hashlib.sha256(rendered.encode()).hexdigest()
    print(f"joint_development_count={len(joint_development)}")
    print(f"excluded_b1_training_overlap={len(excluded_b1_training_overlap)}")
    print(
        "exact_overlap_with_b1_validation="
        f"{manifest['exact_overlap_with_b1_validation_count']}"
    )
    print(f"manifest_sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
