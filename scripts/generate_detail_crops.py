#!/usr/bin/env python3
"""Generate deterministic full-resolution detail crops for visual QA."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("regions", type=Path, help="JSON file containing normalized crop boxes")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "region"


def load_regions(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    regions = data.get("regions") if isinstance(data, dict) else None
    if not isinstance(regions, list) or not regions:
        raise ValueError("regions JSON needs a non-empty 'regions' list")
    return regions


def pixel_box(region: dict[str, Any], width: int, height: int) -> tuple[int, int, int, int]:
    box = region.get("box")
    if not isinstance(box, list) or len(box) != 4 or not all(isinstance(value, (int, float)) for value in box):
        raise ValueError("box must contain four normalized numbers [x0, y0, x1, y1]")
    x0, y0, x1, y1 = (float(value) for value in box)
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError(f"invalid normalized box: {box}")
    padding = float(region.get("padding", 0.02))
    if padding < 0 or padding > 0.25:
        raise ValueError("padding must be between 0 and 0.25")
    dx = (x1 - x0) * padding
    dy = (y1 - y0) * padding
    return (
        max(0, math.floor((x0 - dx) * width)),
        max(0, math.floor((y0 - dy) * height)),
        min(width, math.ceil((x1 + dx) * width)),
        min(height, math.ceil((y1 + dy) * height)),
    )


def white_composite(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    canvas = Image.new("RGBA", rgba.size, "white")
    canvas.alpha_composite(rgba)
    return canvas.convert("RGB")


def make_contact_sheet(items: list[tuple[str, str, Image.Image]], path: Path) -> None:
    columns = 2
    tile_size = (1000, 650)
    label_height = 64
    rows = math.ceil(len(items) / columns)
    sheet = Image.new("RGB", (columns * tile_size[0], rows * (tile_size[1] + label_height)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=22)
    for index, (region_id, label, image) in enumerate(items):
        column = index % columns
        row = index // columns
        x = column * tile_size[0]
        y = row * (tile_size[1] + label_height)
        fitted = white_composite(image)
        fitted.thumbnail((tile_size[0] - 32, tile_size[1] - 32), Image.Resampling.LANCZOS)
        px = x + (tile_size[0] - fitted.width) // 2
        py = y + label_height + (tile_size[1] - fitted.height) // 2
        sheet.paste(fitted, (px, py))
        draw.text((x + 16, y + 10), f"{region_id}: {label}", fill="black", font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def main() -> int:
    args = parse_args()
    try:
        regions = load_regions(args.regions)
        with Image.open(args.image) as opened:
            image = opened.convert("RGBA")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    contact_items: list[tuple[str, str, Image.Image]] = []
    failed = False
    for index, region in enumerate(regions):
        region_id = safe_name(str(region.get("id", f"region-{index + 1}")))
        label = str(region.get("label", region_id))
        if region_id in seen:
            print(f"error: duplicate region id: {region_id}", file=sys.stderr)
            failed = True
            continue
        seen.add(region_id)
        try:
            box = pixel_box(region, image.width, image.height)
        except ValueError as exc:
            print(f"error: {region_id}: {exc}", file=sys.stderr)
            failed = True
            continue
        crop = image.crop(box)
        output = args.output_dir / f"{region_id}.png"
        crop.save(output)
        results.append(
            {
                "id": region_id,
                "label": label,
                "box_pixels": list(box),
                "size": list(crop.size),
                "required": bool(region.get("required", True)),
                "output": str(output),
            }
        )
        contact_items.append((region_id, label, crop))
        print(f"crop: {region_id} -> {output} ({crop.width}x{crop.height})")

    if args.contact_sheet and contact_items:
        make_contact_sheet(contact_items, args.contact_sheet)
        print(f"contact sheet: {args.contact_sheet}")
    if args.report:
        lines = [
            "# Detail Crop QA Index",
            "",
            f"- Source: `{args.image}`",
            f"- Source SHA256: `{hashlib.sha256(args.image.read_bytes()).hexdigest()}`",
            f"- Regions: `{len(results)}`",
            f"- Crop generation: `{'FAIL' if failed else 'PASS'}`",
            "- Visual review: `PENDING` (generation does not inspect or accept the crops)",
            "",
            "| Region | Purpose | Pixel box | Crop | Required |",
            "|---|---|---|---|---:|",
        ]
        for item in results:
            lines.append(
                f"| `{item['id']}` | {item['label']} | `{item['box_pixels']}` | "
                f"`{item['size'][0]}x{item['size'][1]}` | `{item['required']}` |"
            )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"report: {args.report}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
