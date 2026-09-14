from __future__ import annotations

import argparse
import json
from pathlib import Path

from dentxplain.data import load_annotations
from dentxplain.evaluation import (
    cascade_ground_truth_by_image,
    evaluate_cascade_configuration,
    paired_cascade_bootstrap,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paired image-level bootstrap for B2/C1")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260915)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    annotations = load_annotations(args.annotations)
    cached = json.loads(args.predictions.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    ground_truth = cascade_ground_truth_by_image(annotations)
    per_image: dict[str, list[dict]] = {"b2": [], "c1": []}
    for file_name, cached_image in cached["images"].items():
        for method in ("b2", "c1"):
            per_image[method].append(
                evaluate_cascade_configuration(
                    {file_name: cached_image},
                    {file_name: ground_truth.get(file_name, [])},
                    **config["configurations"][method],
                )
            )

    report = paired_cascade_bootstrap(
        per_image["b2"],
        per_image["c1"],
        replicates=args.replicates,
        seed=args.seed,
    )
    report["schema_version"] = "1.0"
    report["first_method"] = "b2"
    report["second_method"] = "c1"
    report["sampling_unit"] = "image"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
