from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image

from dentxplain.data import audit_annotations, load_annotations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit DENTEX validation data")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--images", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_image_files(image_root: Path, payload: dict) -> dict:
    expected = {str(image["file_name"]): image for image in payload["images"]}
    candidates = [
        path
        for path in image_root.rglob("*")
        if path.is_file() and ".ipynb_checkpoints" not in path.parts
    ]
    actual = {path.name: path for path in candidates}
    corrupt: list[str] = []
    dimension_mismatches: list[dict] = []
    hashes: defaultdict[str, list[str]] = defaultdict(list)

    for name, path in sorted(actual.items()):
        hashes[file_sha256(path)].append(name)
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                expected_row = expected.get(name)
                if expected_row is not None and image.size != (
                    int(expected_row["width"]),
                    int(expected_row["height"]),
                ):
                    dimension_mismatches.append(
                        {
                            "file_name": name,
                            "actual": list(image.size),
                            "expected": [
                                int(expected_row["width"]),
                                int(expected_row["height"]),
                            ],
                        }
                    )
        except (OSError, SyntaxError):
            corrupt.append(name)

    return {
        "expected_image_count": len(expected),
        "actual_image_count": len(actual),
        "missing_images": sorted(set(expected) - set(actual)),
        "extra_images": sorted(set(actual) - set(expected)),
        "corrupt_images": sorted(corrupt),
        "dimension_mismatches": dimension_mismatches,
        "exact_duplicate_groups": sorted(
            sorted(names) for names in hashes.values() if len(names) > 1
        ),
    }


def main() -> int:
    args = parse_args()
    payload = load_annotations(args.annotations)
    report = {
        "schema_version": "1.0",
        "annotation_file": str(args.annotations),
        "annotation_sha256": file_sha256(args.annotations),
        "annotations": audit_annotations(payload),
    }
    if args.images is not None:
        report["images"] = audit_image_files(args.images, payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
