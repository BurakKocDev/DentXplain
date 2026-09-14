from __future__ import annotations

from dentxplain.inference import build_findings


def test_build_findings_assigns_fdi_and_abstains_when_geometry_is_weak() -> None:
    pathology = [
        {"box_xyxy": [0, 0, 10, 10], "confidence": 0.8, "class_name": "Caries"},
        {"box_xyxy": [100, 0, 110, 10], "confidence": 0.7, "class_name": "Deep Caries"},
    ]
    teeth = [
        {"box_xyxy": [0, 0, 10, 10], "confidence": 0.9, "class_name": "18"},
    ]
    config = {
        "b0_confidence": 0.2,
        "b1_confidence": 0.1,
        "iou_weight": 1.0,
        "match_threshold": 0.6,
    }

    findings = build_findings(pathology, teeth, config)

    assert findings[0]["fdi"] == "18"
    assert findings[0]["status"] == "assigned"
    assert findings[1]["fdi"] is None
    assert findings[1]["status"] == "enumeration_abstained"
