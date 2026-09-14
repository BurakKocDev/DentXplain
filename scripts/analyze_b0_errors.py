from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from dentxplain.data import load_annotations
from dentxplain.evaluation import analyze_detection_errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze cached B0 detection errors")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confidence", type=float, default=0.2)
    parser.add_argument("--iou", type=float, default=0.5)
    return parser.parse_args()


def ground_truth_by_image(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    image_name_by_id = {
        int(image["id"]): str(image["file_name"]) for image in payload["images"]
    }
    diagnosis_names = {
        int(category["id"]): str(category["name"])
        for category in payload["categories_3"]
    }
    output: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for annotation in payload["annotations"]:
        x, y, width, height = (float(value) for value in annotation["bbox"])
        output[image_name_by_id[int(annotation["image_id"])]].append(
            {
                "box_xyxy": [x, y, x + width, y + height],
                "class_name": diagnosis_names[int(annotation["category_id_3"])],
            }
        )
    return dict(output)


def main() -> int:
    args = parse_args()
    annotations = load_annotations(args.annotations)
    cached = json.loads(args.predictions.read_text(encoding="utf-8"))
    image_names = set(cached["images"])
    all_ground_truth = ground_truth_by_image(annotations)
    ground_truth = {name: all_ground_truth.get(name, []) for name in image_names}
    predictions = {
        name: content["b0"]["predictions"]
        for name, content in cached["images"].items()
    }
    report = analyze_detection_errors(
        predictions,
        ground_truth,
        confidence_threshold=args.confidence,
        iou_threshold=args.iou,
    )
    report["schema_version"] = "1.0"
    report["cohort"] = "joint development cohort unseen by B0 and B1 training"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "by_class": report["by_class"]}, indent=2))
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
