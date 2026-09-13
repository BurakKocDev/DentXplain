from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from dentxplain.data import load_annotations

COLORS = {
    "Impacted": "#ff4d6d",
    "Caries": "#00b4d8",
    "Periapical Lesion": "#ffb703",
    "Deep Caries": "#9b5de5",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a DENTEX validation contact sheet")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--columns", type=int, default=4)
    return parser.parse_args()


def category_map(payload: dict, key: str) -> dict[int, str]:
    return {int(item["id"]): str(item["name"]) for item in payload[key]}


def main() -> int:
    args = parse_args()
    payload = load_annotations(args.annotations)
    annotations_by_image: defaultdict[int, list[dict]] = defaultdict(list)
    for annotation in payload["annotations"]:
        annotations_by_image[int(annotation["image_id"])].append(annotation)

    quadrants = category_map(payload, "categories_1")
    teeth = category_map(payload, "categories_2")
    diagnoses = category_map(payload, "categories_3")
    records = sorted(payload["images"], key=lambda item: int(item["id"]))[: args.limit]

    tile_width, tile_height, header_height = 480, 260, 34
    rows = (len(records) + args.columns - 1) // args.columns
    sheet = Image.new("RGB", (args.columns * tile_width, rows * tile_height), "#07131c")
    font = ImageFont.load_default(size=15)
    small_font = ImageFont.load_default(size=12)

    for index, record in enumerate(records):
        image_id = int(record["id"])
        source = args.images / str(record["file_name"])
        with Image.open(source) as opened:
            image = opened.convert("RGB")

        available_height = tile_height - header_height
        scale = min(tile_width / image.width, available_height / image.height)
        resized = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
        tile = Image.new("RGB", (tile_width, tile_height), "black")
        x_offset = (tile_width - resized.width) // 2
        y_offset = header_height + (available_height - resized.height) // 2
        tile.paste(resized, (x_offset, y_offset))
        draw = ImageDraw.Draw(tile)

        annotations = annotations_by_image.get(image_id, [])
        draw.text(
            (8, 8),
            f"{record['file_name']} | {len(annotations)} annotation(s)",
            fill="#e6f1f7",
            font=font,
        )
        for annotation in annotations:
            x, y, width, height = (float(value) for value in annotation["bbox"])
            diagnosis = diagnoses[int(annotation["category_id_3"])]
            fdi = (
                quadrants[int(annotation["category_id_1"])]
                + teeth[int(annotation["category_id_2"])]
            )
            color = COLORS[diagnosis]
            box = (
                x_offset + round(x * scale),
                y_offset + round(y * scale),
                x_offset + round((x + width) * scale),
                y_offset + round((y + height) * scale),
            )
            draw.rectangle(box, outline=color, width=3)
            label = f"{fdi} {diagnosis}"
            label_box = draw.textbbox((box[0], box[1]), label, font=small_font)
            label_width = label_box[2] - label_box[0] + 6
            label_height = label_box[3] - label_box[1] + 4
            label_y = max(header_height, box[1] - label_height)
            draw.rectangle(
                (box[0], label_y, box[0] + label_width, label_y + label_height),
                fill=color,
            )
            draw.text((box[0] + 3, label_y + 2), label, fill="white", font=small_font)

        column = index % args.columns
        row = index // args.columns
        sheet.paste(tile, (column * tile_width, row * tile_height))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=92, optimize=True)
    print(f"Rendered {len(records)} images to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

