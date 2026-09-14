from __future__ import annotations

import argparse
import json
from pathlib import Path

from dentxplain.data import load_annotations
from dentxplain.evaluation import (
    cascade_ground_truth_by_image,
    evaluate_cascade_configuration,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate frozen B2/C1 configurations")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = load_annotations(args.annotations)
    cached = json.loads(args.predictions.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    ground_truth = cascade_ground_truth_by_image(payload)
    results = {
        name: evaluate_cascade_configuration(
            cached["images"],
            ground_truth,
            **parameters,
        )
        for name, parameters in config["configurations"].items()
    }
    report = {
        "schema_version": "1.0",
        "evaluation_policy": "fixed pre-final configuration; no grid or retuning",
        "configuration": str(args.config),
        "cohort_image_count": cached["image_count"],
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
