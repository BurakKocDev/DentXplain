from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find exact and perceptual duplicate candidates across image collections"
    )
    parser.add_argument(
        "--collection",
        action="append",
        required=True,
        metavar="NAME=PATH",
        help="Named image directory; repeat for every collection",
    )
    parser.add_argument("--near-threshold", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def parse_collection(value: str) -> tuple[str, Path]:
    name, separator, raw_path = value.partition("=")
    if not separator or not name or not raw_path:
        raise ValueError(f"Invalid collection {value!r}; expected NAME=PATH")
    return name, Path(raw_path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def difference_hash(image: Image.Image, hash_size: int = 16) -> str:
    grayscale = image.convert("L").resize(
        (hash_size + 1, hash_size), Image.Resampling.LANCZOS
    )
    pixels = list(grayscale.get_flattened_data())
    bits = 0
    for row in range(hash_size):
        offset = row * (hash_size + 1)
        for column in range(hash_size):
            bits = (bits << 1) | int(
                pixels[offset + column] > pixels[offset + column + 1]
            )
    return f"{bits:0{hash_size * hash_size // 4}x}"


def scan_collection(name: str, root: Path) -> list[dict]:
    records: list[dict] = []
    for path in sorted(root.rglob("*.png")):
        if ".ipynb_checkpoints" in path.parts:
            continue
        with Image.open(path) as image:
            width, height = image.size
            perceptual_hash = difference_hash(image)
        records.append(
            {
                "collection": name,
                "file_name": path.name,
                "bytes": path.stat().st_size,
                "width": width,
                "height": height,
                "sha256": file_sha256(path),
                "dhash_256": perceptual_hash,
            }
        )
    return records


def reference(record: dict) -> dict:
    return {
        "collection": record["collection"],
        "file_name": record["file_name"],
    }


def main() -> int:
    args = parse_args()
    records: list[dict] = []
    collection_summary: dict[str, dict] = {}
    for raw_collection in args.collection:
        name, root = parse_collection(raw_collection)
        collection_records = scan_collection(name, root)
        records.extend(collection_records)
        collection_summary[name] = {
            "root": str(root),
            "image_count": len(collection_records),
            "bytes": sum(record["bytes"] for record in collection_records),
        }

    by_sha256: defaultdict[str, list[dict]] = defaultdict(list)
    by_file_name: defaultdict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_sha256[record["sha256"]].append(record)
        by_file_name[record["file_name"]].append(record)

    exact_groups = [
        {
            "sha256": digest,
            "members": [reference(record) for record in group],
        }
        for digest, group in sorted(by_sha256.items())
        if len(group) > 1
    ]
    reused_file_names = [
        {
            "file_name": file_name,
            "members": [
                {**reference(record), "sha256": record["sha256"]} for record in group
            ],
        }
        for file_name, group in sorted(by_file_name.items())
        if len({record["collection"] for record in group}) > 1
    ]

    near_candidates: list[dict] = []
    for left, right in combinations(records, 2):
        if left["sha256"] == right["sha256"]:
            continue
        left_ratio = left["width"] / left["height"]
        right_ratio = right["width"] / right["height"]
        if abs(left_ratio - right_ratio) / max(left_ratio, right_ratio) > 0.03:
            continue
        distance = (int(left["dhash_256"], 16) ^ int(right["dhash_256"], 16)).bit_count()
        if distance <= args.near_threshold:
            near_candidates.append(
                {
                    "left": reference(left),
                    "right": reference(right),
                    "dhash_distance": distance,
                }
            )

    report = {
        "schema_version": "1.0",
        "method": {
            "exact": "SHA-256 over encoded file bytes",
            "near_candidate": "256-bit difference hash, <= threshold, aspect ratio delta <= 3%",
            "near_threshold": args.near_threshold,
            "warning": "Perceptual matches are review candidates, not automatic duplicate labels.",
        },
        "collections": collection_summary,
        "exact_duplicate_groups": exact_groups,
        "near_duplicate_candidates": near_candidates,
        "reused_file_names_across_collections": reused_file_names,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "collections": collection_summary,
                "exact_duplicate_group_count": len(exact_groups),
                "near_duplicate_candidate_count": len(near_candidates),
                "reused_file_name_count": len(reused_file_names),
                "output": str(args.output),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
