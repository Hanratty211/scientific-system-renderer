#!/usr/bin/env python3
"""Inspect render dimensions, alpha, framing, contrast, and review composites."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat


@dataclass
class ImageResult:
    path: str
    width: int = 0
    height: int = 0
    mode: str = ""
    has_alpha: bool = False
    transparent_fraction: float = 0.0
    content_bbox: tuple[int, int, int, int] | None = None
    margins_percent: tuple[float, float, float, float] | None = None
    luminance_p01: int = 0
    luminance_p50: int = 0
    luminance_p99: int = 0
    errors: list[str] | None = None
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        self.errors = [] if self.errors is None else self.errors
        self.warnings = [] if self.warnings is None else self.warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--require-alpha", action="store_true")
    parser.add_argument("--min-width", type=int, default=0)
    parser.add_argument("--min-height", type=int, default=0)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    return parser.parse_args()


def percentile_from_histogram(histogram: list[int], percentile: float) -> int:
    total = sum(histogram)
    if total == 0:
        return 0
    threshold = total * percentile
    running = 0
    for value, count in enumerate(histogram):
        running += count
        if running >= threshold:
            return value
    return 255


def inspect_image(path: Path, args: argparse.Namespace) -> tuple[ImageResult, Image.Image | None]:
    result = ImageResult(path=str(path))
    try:
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
            result.width, result.height = opened.size
            result.mode = opened.mode
            result.has_alpha = "A" in opened.getbands()
    except Exception as exc:
        result.errors.append(f"cannot open image: {exc}")
        return result, None

    if result.width < args.min_width:
        result.errors.append(f"width {result.width} is below required {args.min_width}")
    if result.height < args.min_height:
        result.errors.append(f"height {result.height} is below required {args.min_height}")
    if args.require_alpha and not result.has_alpha:
        result.errors.append("alpha channel is required")

    sample = image.copy()
    sample.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    alpha = sample.getchannel("A")
    alpha_hist = alpha.histogram()
    transparent_pixels = sum(alpha_hist[:250])
    result.transparent_fraction = transparent_pixels / max(1, sample.width * sample.height)

    if result.has_alpha and alpha.getextrema()[0] < 250:
        mask = alpha.point(lambda value: 255 if value > 8 else 0)
        sample_bbox = mask.getbbox()
        if sample_bbox:
            sx = result.width / sample.width
            sy = result.height / sample.height
            bbox = (
                math.floor(sample_bbox[0] * sx),
                math.floor(sample_bbox[1] * sy),
                math.ceil(sample_bbox[2] * sx),
                math.ceil(sample_bbox[3] * sy),
            )
            result.content_bbox = bbox
            left = 100.0 * bbox[0] / result.width
            top = 100.0 * bbox[1] / result.height
            right = 100.0 * (result.width - bbox[2]) / result.width
            bottom = 100.0 * (result.height - bbox[3]) / result.height
            result.margins_percent = (left, top, right, bottom)
            if min(result.margins_percent) < 0.5:
                result.warnings.append("visible content is within 0.5% of at least one image edge")
        else:
            result.errors.append("alpha channel contains no visible content")
    elif args.require_alpha:
        result.warnings.append("image has an alpha channel but appears fully opaque")

    white = Image.new("RGBA", sample.size, (255, 255, 255, 255))
    white.alpha_composite(sample)
    gray = white.convert("L")
    histogram = gray.histogram()
    result.luminance_p01 = percentile_from_histogram(histogram, 0.01)
    result.luminance_p50 = percentile_from_histogram(histogram, 0.50)
    result.luminance_p99 = percentile_from_histogram(histogram, 0.99)
    if result.luminance_p99 - result.luminance_p01 < 8:
        result.errors.append("image has near-zero luminance contrast and may be blank")

    corner_size = max(1, min(sample.size) // 30)
    corners = [
        sample.crop((0, 0, corner_size, corner_size)),
        sample.crop((sample.width - corner_size, 0, sample.width, corner_size)),
        sample.crop((0, sample.height - corner_size, corner_size, sample.height)),
        sample.crop((sample.width - corner_size, sample.height - corner_size, sample.width, sample.height)),
    ]
    dark_opaque_corners = 0
    for corner in corners:
        rgba_mean = ImageStat.Stat(corner).mean
        if sum(rgba_mean[:3]) / 3 < 24 and rgba_mean[3] > 245:
            dark_opaque_corners += 1
    if dark_opaque_corners >= 3:
        result.warnings.append("most corners are opaque black; verify journal-background suitability")
    return result, image


def checkerboard(size: tuple[int, int], cell: int = 32) -> Image.Image:
    image = Image.new("RGBA", size, (238, 238, 238, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(210, 210, 210, 255))
    return image


def fit_tile(image: Image.Image, size: tuple[int, int], background: tuple[int, int, int, int] | str) -> Image.Image:
    if background == "checker":
        canvas = checkerboard(size)
    else:
        canvas = Image.new("RGBA", size, background)
    fitted = image.copy()
    fitted.thumbnail((size[0] - 24, size[1] - 24), Image.Resampling.LANCZOS)
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))
    return canvas


def make_contact_sheet(items: list[tuple[ImageResult, Image.Image]], path: Path) -> None:
    tile_size = (900, 540)
    label_height = 72
    rows: list[Image.Image] = []
    font = ImageFont.load_default(size=22)
    for result, image in items:
        row = Image.new("RGB", (tile_size[0] * 3, tile_size[1] + label_height), "white")
        draw = ImageDraw.Draw(row)
        for index, (label, background) in enumerate(
            (("checkerboard", "checker"), ("white", (255, 255, 255, 255)), ("dark", (30, 34, 40, 255)))
        ):
            tile = fit_tile(image, tile_size, background).convert("RGB")
            row.paste(tile, (index * tile_size[0], label_height))
            draw.text((index * tile_size[0] + 16, 38), label, fill="black", font=font)
        draw.text((16, 8), f"{Path(result.path).name} | {result.width} x {result.height}", fill="black", font=font)
        rows.append(row)
    sheet = Image.new("RGB", (tile_size[0] * 3, sum(row.height for row in rows)), "white")
    y = 0
    for row in rows:
        sheet.paste(row, (0, y))
        y += row.height
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def write_markdown(path: Path, results: list[ImageResult]) -> None:
    lines = ["# Render QA", ""]
    for result in results:
        lines.extend(
            [
                f"## {Path(result.path).name}",
                "",
                f"- Size: `{result.width} x {result.height}`",
                f"- Mode: `{result.mode}`",
                f"- Alpha present: `{result.has_alpha}`",
                f"- Transparent fraction: `{result.transparent_fraction:.4f}`",
                f"- Content bbox: `{result.content_bbox}`",
                f"- Margins L/T/R/B (%): `{result.margins_percent}`",
                f"- Luminance p01/p50/p99: `{result.luminance_p01}/{result.luminance_p50}/{result.luminance_p99}`",
                f"- Result: `{'FAIL' if result.errors else 'PASS'}`",
                "",
            ]
        )
        if result.errors:
            lines.append("Errors:")
            lines.extend(f"- {message}" for message in result.errors)
            lines.append("")
        if result.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {message}" for message in result.warnings)
            lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    results: list[ImageResult] = []
    images: list[tuple[ImageResult, Image.Image]] = []
    for path in args.images:
        result, image = inspect_image(path, args)
        results.append(result)
        if image is not None:
            images.append((result, image))
        print(
            f"{path}: {result.width}x{result.height}, alpha={result.has_alpha}, "
            f"errors={len(result.errors)}, warnings={len(result.warnings)}"
        )
    if args.contact_sheet and images:
        make_contact_sheet(images, args.contact_sheet)
        print(f"contact sheet: {args.contact_sheet}")
    if args.report:
        write_markdown(args.report, results)
        print(f"report: {args.report}")
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps([asdict(result) for result in results], indent=2) + "\n", encoding="utf-8")
        print(f"json: {args.json_path}")
    return 1 if any(result.errors for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
