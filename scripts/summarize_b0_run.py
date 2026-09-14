from __future__ import annotations

import argparse
import json
from pathlib import Path

from dentxplain.evaluation import summarize_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize a completed or active B0 run")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = summarize_results(args.run_dir / "results.csv")
    rendered = json.dumps(summary, indent=2, ensure_ascii=False)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{rendered}\n", encoding="utf-8")

    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
