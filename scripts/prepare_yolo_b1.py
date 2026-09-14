from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from dentxplain.data import load_annotations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare the leakage-safe B1 YOLO dataset")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def safe_hardlink(source: Path, destination: Path) -> None:
    if destination.exists():
        if not os.path.samefile(source, destination):
            raise FileExistsError(f"Refusing to replace {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, destination)


def fdi_name(
    annotation: dict,
    quadrant_names: dict[int, str],
    tooth_names: dict[int, str],
) -> str:
    return (
        f"{quadrant_names[int(annotation['category_id_1'])]}"
        f"{tooth_names[int(annotation['category_id_2'])]}"
    )


def yolo_line(annotation: dict, image: dict, class_id: int) -> str:
    x, y, width, height = (float(value) for value in annotation["bbox"])
    image_width = float(image["width"])
    image_height = float(image["height"])
    center_x = (x + width / 2) / image_width
    center_y = (y + height / 2) / image_height
    return (
        f"{class_id} {center_x:.8f} {center_y:.8f} "
        f"{width / image_width:.8f} {height / image_height:.8f}"
    )


def write_yaml(output_root: Path, names: list[str]) -> None:
    lines = [
        f"path: {output_root.resolve().as_posix()}",
        "train: images/train",
        "val: images/calibration_validation",
        "names:",
    ]
    lines.extend(f"  {class_id}: '{name}'" for class_id, name in enumerate(names))
    (output_root / "dentex_b1.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    payload = load_annotations(args.annotations)
    split = json.loads(args.split.read_text(encoding="utf-8"))
    image_by_name = {str(image["file_name"]): image for image in payload["images"]}
    annotations_by_image: defaultdict[int, list[dict]] = defaultdict(list)
    for annotation in payload["annotations"]:
        annotations_by_image[int(annotation["image_id"])].append(annotation)
    quadrant_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_1"]
    }
    tooth_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_2"]
    }
    names = [
        f"{quadrant}{position}"
        for quadrant in ("1", "2", "3", "4")
        for position in ("1", "2", "3", "4", "5", "6", "7", "8")
    ]
    class_id_by_name = {name: class_id for class_id, name in enumerate(names)}

    report: dict[str, dict] = {}
    for split_name in ("training", "calibration_validation"):
        destination_name = "train" if split_name == "training" else split_name
        class_counts: Counter[str] = Counter()
        duplicate_label_count = 0
        for file_name in split[split_name]:
            image = image_by_name[file_name]
            source = args.images / file_name
            if not source.is_file():
                raise FileNotFoundError(source)
            image_destination = args.output / "images" / destination_name / file_name
            label_destination = (
                args.output / "labels" / destination_name / f"{Path(file_name).stem}.txt"
            )
            safe_hardlink(source, image_destination)
            label_lines: list[str] = []
            seen_labels: set[str] = set()
            for annotation in annotations_by_image[int(image["id"])]:
                fdi = fdi_name(annotation, quadrant_names, tooth_names)
                label = yolo_line(annotation, image, class_id_by_name[fdi])
                if label in seen_labels:
                    duplicate_label_count += 1
                    continue
                seen_labels.add(label)
                label_lines.append(label)
                class_counts[fdi] += 1
            label_destination.parent.mkdir(parents=True, exist_ok=True)
            label_destination.write_text("\n".join(label_lines) + "\n", encoding="utf-8")
        report[split_name] = {
            "image_count": len(split[split_name]),
            "duplicate_source_label_count_removed": duplicate_label_count,
            "box_count": sum(class_counts.values()),
            "fdi_box_counts": dict(sorted(class_counts.items())),
        }

    args.output.mkdir(parents=True, exist_ok=True)
    write_yaml(args.output, names)
    report_path = args.output / "preparation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"dataset_yaml={args.output / 'dentex_b1.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
