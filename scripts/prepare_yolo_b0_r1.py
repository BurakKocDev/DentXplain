from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from dentxplain.data import b0_r1_repeat_reason

CLASS_NAMES = {
    0: "Impacted",
    1: "Caries",
    2: "Periapical Lesion",
    3: "Deep Caries",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare the B0-R1 resampling ablation")
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def safe_hardlink(source: Path, destination: Path) -> None:
    if destination.exists():
        if not os.path.samefile(source, destination):
            raise FileExistsError(f"Refusing to replace {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, destination)


def alias_name(file_name: str, reason: str) -> str:
    path = Path(file_name)
    return f"{path.stem}__r1_{reason}{path.suffix}"


def label_counts(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            counts[CLASS_NAMES[int(line.split(maxsplit=1)[0])]] += 1
    return counts


def write_yaml(output: Path) -> None:
    yaml = (
        f"path: {output.resolve().as_posix()}\n"
        "train: images/train\n"
        "val: images/calibration_validation\n"
        "names:\n"
        "  0: Impacted\n"
        "  1: Caries\n"
        "  2: Periapical Lesion\n"
        "  3: Deep Caries\n"
    )
    (output / "dentex_b0_r1.yaml").write_text(yaml, encoding="utf-8")


def main() -> int:
    args = parse_args()
    split = json.loads(args.split.read_text(encoding="utf-8"))
    counts_by_image = {
        file_name: label_counts(args.source / "labels" / "train" / f"{Path(file_name).stem}.txt")
        for file_name in split["training"]
    }

    effective_counts: Counter[str] = Counter()
    repeated_by_reason: Counter[str] = Counter()
    aliases: list[dict[str, str]] = []
    for split_key, directory_name in (
        ("training", "train"),
        ("calibration_validation", "calibration_validation"),
    ):
        for file_name in split[split_key]:
            image_source = args.source / "images" / directory_name / file_name
            label_source = args.source / "labels" / directory_name / f"{Path(file_name).stem}.txt"
            safe_hardlink(image_source, args.output / "images" / directory_name / file_name)
            safe_hardlink(
                label_source,
                args.output / "labels" / directory_name / f"{Path(file_name).stem}.txt",
            )
            if split_key != "training":
                continue
            effective_counts.update(counts_by_image[file_name])
            reason = b0_r1_repeat_reason(counts_by_image[file_name])
            if reason is None:
                continue
            alias = alias_name(file_name, reason)
            safe_hardlink(image_source, args.output / "images" / directory_name / alias)
            safe_hardlink(
                label_source,
                args.output / "labels" / directory_name / f"{Path(alias).stem}.txt",
            )
            effective_counts.update(counts_by_image[file_name])
            repeated_by_reason[reason] += 1
            aliases.append({"source": file_name, "alias": alias, "reason": reason})

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "policy": (
            "one extra copy for each training image containing Periapical Lesion; "
            "otherwise one extra copy when Deep Caries count exceeds Caries count"
        ),
        "original_training_image_count": len(split["training"]),
        "effective_training_image_count": len(split["training"]) + len(aliases),
        "validation_image_count": len(split["calibration_validation"]),
        "repeated_image_count": len(aliases),
        "repeated_by_reason": dict(sorted(repeated_by_reason.items())),
        "effective_training_box_counts": dict(sorted(effective_counts.items())),
        "aliases": aliases,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_yaml(args.output)
    (args.output / "preparation_report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "aliases"}, indent=2))
    print(f"dataset_yaml={args.output / 'dentex_b0_r1.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
