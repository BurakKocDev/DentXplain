from __future__ import annotations

import argparse
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the DentXplain B0 diagnosis detector")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model", default="yolov8s.pt")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--image-size", type=int, default=640)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--device", default="0")
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--save-period", type=int, default=5)
    parser.add_argument("--rect", action="store_true")
    parser.add_argument("--name", default="b0_smoke_640")
    parser.add_argument("--project", type=Path, default=Path("artifacts/training"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("YOLO_CONFIG_DIR", str(project_root / ".ultralytics"))

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(
        data=str(args.data.resolve()),
        epochs=args.epochs,
        imgsz=args.image_size,
        batch=args.batch,
        workers=args.workers,
        device=args.device,
        project=str(args.project.resolve()),
        name=args.name,
        seed=20260913,
        deterministic=True,
        amp=True,
        rect=args.rect,
        cache=False,
        plots=True,
        patience=args.patience,
        save_period=args.save_period,
        mosaic=0.0,
        mixup=0.0,
        copy_paste=0.0,
        degrees=0.0,
        translate=0.05,
        scale=0.15,
        fliplr=0.5,
        hsv_h=0.0,
        hsv_s=0.0,
        hsv_v=0.1,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
