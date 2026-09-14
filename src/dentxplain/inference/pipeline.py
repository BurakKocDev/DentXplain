from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image

from dentxplain.cascade import anatomy_constrained_teeth, best_tooth_match

DISCLAIMER = "Research prototype only; not for diagnosis or treatment decisions."


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def serialize_result(result: Any) -> list[dict[str, Any]]:
    predictions = []
    if result.boxes is None:
        return predictions
    for xyxy, confidence, class_id in zip(
        result.boxes.xyxy.cpu().tolist(),
        result.boxes.conf.cpu().tolist(),
        result.boxes.cls.cpu().tolist(),
        strict=True,
    ):
        numeric_class_id = int(class_id)
        predictions.append(
            {
                "box_xyxy": [round(float(value), 2) for value in xyxy],
                "confidence": round(float(confidence), 6),
                "class_id": numeric_class_id,
                "class_name": str(result.names[numeric_class_id]),
            }
        )
    return predictions


def build_findings(
    pathology_predictions: list[dict[str, Any]],
    tooth_predictions: list[dict[str, Any]],
    configuration: dict[str, Any],
) -> list[dict[str, Any]]:
    pathology = [
        prediction
        for prediction in pathology_predictions
        if float(prediction["confidence"]) >= float(configuration["b0_confidence"])
    ]
    teeth = anatomy_constrained_teeth(
        tooth_predictions,
        minimum_confidence=float(configuration["b1_confidence"]),
    )
    findings = []
    for prediction in sorted(
        pathology,
        key=lambda row: float(row["confidence"]),
        reverse=True,
    ):
        tooth_match = best_tooth_match(
            tuple(float(value) for value in prediction["box_xyxy"]),
            teeth,
            iou_weight=float(configuration["iou_weight"]),
            minimum_tooth_confidence=float(configuration["b1_confidence"]),
        )
        assigned = (
            tooth_match is not None
            and float(tooth_match["match_score"]) >= float(configuration["match_threshold"])
        )
        findings.append(
            {
                "diagnosis": prediction["class_name"],
                "confidence": float(prediction["confidence"]),
                "box_xyxy": prediction["box_xyxy"],
                "fdi": tooth_match["class_name"] if assigned else None,
                "tooth_confidence": float(tooth_match["confidence"]) if assigned else None,
                "match_score": float(tooth_match["match_score"]) if assigned else None,
                "status": "assigned" if assigned else "enumeration_abstained",
            }
        )
    return findings


class DentXplainPipeline:
    """Load the frozen B0/B1 models and return anatomy-constrained findings."""

    def __init__(self, project_root: Path, config_path: Path, device: str | None = None) -> None:
        os.environ.setdefault("YOLO_CONFIG_DIR", str(project_root / ".ultralytics"))
        import torch
        from ultralytics import YOLO

        self.project_root = project_root.resolve()
        self.config = json.loads(config_path.read_text(encoding="utf-8"))
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        models = self.config["models"]
        model_paths = {
            name: self.project_root / model["path"] for name, model in models.items()
        }
        for name, path in model_paths.items():
            if not path.is_file():
                raise FileNotFoundError(path)
            if file_sha256(path) != models[name]["sha256"]:
                raise ValueError(f"Model hash mismatch: {path}")
        self.b0 = YOLO(str(model_paths["b0"]))
        self.b1 = YOLO(str(model_paths["b1"]))

    def _predict_model(self, model: Any, image: Image.Image) -> list[dict[str, Any]]:
        result = model.predict(
            source=image,
            imgsz=int(self.config["image_size"]),
            conf=float(self.config["minimum_cached_confidence"]),
            iou=0.7,
            max_det=300,
            device=self.device,
            verbose=False,
        )[0]
        return serialize_result(result)

    def predict(self, image: Image.Image, image_id: str | None = None) -> dict[str, Any]:
        image = image.convert("RGB")
        b0_predictions = self._predict_model(self.b0, image)
        b1_predictions = self._predict_model(self.b1, image)
        configuration = self.config["configurations"]["c1"]
        findings = build_findings(b0_predictions, b1_predictions, configuration)
        assigned_count = sum(finding["status"] == "assigned" for finding in findings)
        return {
            "schema_version": "1.0",
            "model_bundle": "dentxplain_c1_v1",
            "image_id": image_id,
            "image": {"width": image.width, "height": image.height},
            "summary": {
                "candidate_count": len(findings),
                "assigned_count": assigned_count,
                "enumeration_abstained_count": len(findings) - assigned_count,
                "status": "candidates_detected" if findings else "no_threshold_candidates",
                "expert_review_required": True,
            },
            "findings": findings,
            "thresholds": configuration,
            "disclaimer": DISCLAIMER,
        }
