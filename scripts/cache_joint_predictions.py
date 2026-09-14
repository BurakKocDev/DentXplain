from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cache B0 and B1 predictions for B2")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-key", default="joint_development")
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--b0-weights", type=Path, required=True)
    parser.add_argument("--b1-weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-size", type=int, default=960)
    parser.add_argument("--confidence", type=float, default=0.05)
    parser.add_argument("--device", default="0")
    return parser.parse_args()


def serialize_result(result: Any) -> dict[str, Any]:
    boxes = result.boxes
    predictions = []
    if boxes is not None:
        for xyxy, confidence, class_id in zip(
            boxes.xyxy.cpu().tolist(),
            boxes.conf.cpu().tolist(),
            boxes.cls.cpu().tolist(),
            strict=True,
        ):
            numeric_class_id = int(class_id)
            predictions.append(
                {
                    "box_xyxy": [round(float(value), 4) for value in xyxy],
                    "confidence": round(float(confidence), 8),
                    "class_id": numeric_class_id,
                    "class_name": str(result.names[numeric_class_id]),
                }
            )
    return {
        "width": int(result.orig_shape[1]),
        "height": int(result.orig_shape[0]),
        "predictions": predictions,
    }


def predict(model: Any, sources: list[str], args: argparse.Namespace) -> dict[str, dict]:
    output: dict[str, dict] = {}
    results = model.predict(
        source=sources,
        imgsz=args.image_size,
        conf=args.confidence,
        iou=0.7,
        max_det=300,
        device=args.device,
        stream=True,
        save=False,
        verbose=False,
    )
    for result in results:
        output[Path(result.path).name] = serialize_result(result)
    return output


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("YOLO_CONFIG_DIR", str(project_root / ".ultralytics"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    file_names = list(manifest[args.manifest_key])
    sources = [str((args.images / file_name).resolve()) for file_name in file_names]
    missing = [source for source in sources if not Path(source).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing {len(missing)} manifest images")

    from ultralytics import YOLO

    started = time.perf_counter()
    b0_predictions = predict(YOLO(args.b0_weights), sources, args)
    b1_predictions = predict(YOLO(args.b1_weights), sources, args)
    if set(b0_predictions) != set(file_names) or set(b1_predictions) != set(file_names):
        raise RuntimeError("Prediction output does not cover the requested manifest")

    payload = {
        "schema_version": "1.0",
        "cohort_manifest": str(args.manifest),
        "cohort_manifest_key": args.manifest_key,
        "image_count": len(file_names),
        "image_size": args.image_size,
        "minimum_cached_confidence": args.confidence,
        "models": {
            "b0": str(args.b0_weights),
            "b1": str(args.b1_weights),
        },
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "images": {
            file_name: {
                "b0": b0_predictions[file_name],
                "b1": b1_predictions[file_name],
            }
            for file_name in file_names
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"image_count={len(file_names)}")
    print(f"b0_prediction_count={sum(len(row['predictions']) for row in b0_predictions.values())}")
    print(f"b1_prediction_count={sum(len(row['predictions']) for row in b1_predictions.values())}")
    print(f"elapsed_seconds={payload['elapsed_seconds']}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
