from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from dentxplain.data import load_annotations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze the official final cohort")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    annotations = load_annotations(args.annotations)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    file_names = sorted(str(image["file_name"]) for image in annotations["images"])
    if len(file_names) != int(config["expected_image_count"]):
        raise ValueError("Final image count does not match frozen configuration")
    if sha256(args.annotations) != config["annotation_sha256"]:
        raise ValueError("Final annotation hash does not match frozen configuration")
    missing = [file_name for file_name in file_names if not (args.images / file_name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing {len(missing)} final images")
    for model in config["models"].values():
        model_path = Path(model["path"])
        if sha256(model_path) != model["sha256"]:
            raise ValueError(f"Model hash mismatch: {model_path}")

    manifest = {
        "schema_version": "1.0",
        "purpose": "single locked final evaluation; never threshold selection",
        "configuration": str(args.config),
        "annotation_sha256": config["annotation_sha256"],
        "final_evaluation": file_names,
        "final_evaluation_count": len(file_names),
    }
    rendered = json.dumps(manifest, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"final_evaluation_count={len(file_names)}")
    print(f"manifest_sha256={hashlib.sha256(rendered.encode()).hexdigest()}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
