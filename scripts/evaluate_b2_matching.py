from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from dentxplain.data import load_annotations
from dentxplain.evaluation import (
    cascade_ground_truth_by_image,
    evaluate_cascade_configuration,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tune the B2 unconstrained cascade")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--anatomy-constrained", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = load_annotations(args.annotations)
    cached = json.loads(args.predictions.read_text(encoding="utf-8"))
    ground_truth = cascade_ground_truth_by_image(payload)

    grid = []
    for b0_confidence, b1_confidence, iou_weight, match_threshold in itertools.product(
        (0.1, 0.2, 0.3, 0.4, 0.5),
        (0.1, 0.25, 0.5),
        (0.0, 0.25, 0.5, 0.75, 1.0),
        (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7),
    ):
        grid.append(
            evaluate_cascade_configuration(
                cached["images"],
                ground_truth,
                b0_confidence=b0_confidence,
                b1_confidence=b1_confidence,
                iou_weight=iou_weight,
                match_threshold=match_threshold,
                anatomy_constrained=args.anatomy_constrained,
            )
        )
    grid.sort(
        key=lambda row: (row["joint_f1"], row["joint_precision"], row["joint_recall"]),
        reverse=True,
    )
    report = {
        "schema_version": "1.0",
        "selection_rule": "maximum joint F1; ties by precision then recall",
        "mode": "C1 anatomy-constrained" if args.anatomy_constrained else "B2 unconstrained",
        "cohort_image_count": cached["image_count"],
        "configuration_count": len(grid),
        "best": grid[0],
        "top_20": grid[:20],
        "configurations": grid,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["best"], indent=2))
    print(f"configuration_count={len(grid)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
