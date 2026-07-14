#!/usr/bin/env python3
"""Create a reproducible scientific-system render package."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = SKILL_DIR / "assets"


VIEW_DEFAULTS = {
    "architecture": {
        "purpose": "Show functional modules and major flows",
        "camera": "vector-layout",
        "representation": "logical",
        "scale_level": "system",
        "state_display": "single",
    },
    "physical-setup": {
        "purpose": "Show buildable devices, ports, supports, and physical paths",
        "camera": "orthographic-isometric",
        "representation": "physical",
        "scale_level": "system",
        "state_display": "single",
    },
    "component-sheet": {
        "purpose": "Show product-faithful bodies, active areas, ports, and mounts",
        "camera": "orthographic-multiview",
        "representation": "physical",
        "scale_level": "device",
        "state_display": "exploded",
    },
    "mechanism": {
        "purpose": "Show internal stages, timing, state changes, or multiplexing",
        "camera": "vector-inset",
        "representation": "mechanism",
        "scale_level": "component",
        "state_display": "sequence",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--domain", default="general")
    parser.add_argument(
        "--views",
        default="physical-setup",
        help="Comma-separated: architecture,physical-setup,component-sheet,mechanism",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow initialization in a non-empty directory; existing files are preserved",
    )
    return parser.parse_args()


def write_new(path: Path, text: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def copy_new(source: Path, target: Path) -> bool:
    if target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
        print(f"error: output directory is not empty: {output_dir}", file=sys.stderr)
        print("use --force to preserve existing files and add only missing templates", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    for directory in ("final", "engineering", "intermediate", "references", "qa"):
        (output_dir / directory).mkdir(exist_ok=True)

    requested_views = [value.strip() for value in args.views.split(",") if value.strip()]
    unknown = sorted(set(requested_views) - set(VIEW_DEFAULTS))
    if unknown:
        print(f"error: unsupported views: {', '.join(unknown)}", file=sys.stderr)
        return 2

    created: list[Path] = []
    manifest_path = output_dir / "scene_manifest.json"
    if not manifest_path.exists():
        manifest = json.loads((ASSETS_DIR / "scene_manifest.template.json").read_text(encoding="utf-8"))
        manifest["title"] = args.title
        manifest["domain"] = args.domain
        manifest["views"] = [
            {
                "id": view,
                "type": view,
                "representation": VIEW_DEFAULTS[view]["representation"],
                "scale_level": VIEW_DEFAULTS[view]["scale_level"],
                "state_display": VIEW_DEFAULTS[view]["state_display"],
                "purpose": VIEW_DEFAULTS[view]["purpose"],
                "camera": VIEW_DEFAULTS[view]["camera"],
                "shows_components": [component["id"] for component in manifest["components"]],
            }
            for view in requested_views
        ]
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        created.append(manifest_path)

    build_path = output_dir / "engineering" / "build_scene.py"
    if copy_new(ASSETS_DIR / "build_scene.template.py", build_path):
        created.append(build_path)

    overlay_path = output_dir / "final" / "system_annotated.svg"
    if copy_new(ASSETS_DIR / "annotation_overlay.template.svg", overlay_path):
        created.append(overlay_path)

    ledger_path = output_dir / "references" / "source_ledger.csv"
    if not ledger_path.exists():
        with ledger_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "source_id",
                    "component_id",
                    "claim",
                    "source_type",
                    "title_or_model",
                    "url_or_path",
                    "publisher_or_manufacturer",
                    "accessed_date",
                    "license_or_usage_note",
                    "confidence",
                    "notes",
                ]
            )
            writer.writerow(
                [
                    "S1",
                    "source;sink",
                    "Starter topology only; replace with project evidence",
                    "schematic-assumption",
                    "Starter template",
                    "",
                    "",
                    datetime.now().astimezone().date().isoformat(),
                    "Original template",
                    "schematic",
                    "Do not present starter geometry as verified hardware",
                ]
            )
        created.append(ledger_path)

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    worklog = f"""# Render Work Log

## Project

- Title: {args.title}
- Domain: {args.domain}
- Views: {', '.join(requested_views)}
- Initialized: {timestamp}

## Status

- [ ] Evidence ledger completed
- [ ] Scene manifest validated
- [ ] Engineering storyboard approved
- [ ] Gray-box scene inspected
- [ ] Component fidelity inspected
- [ ] Physical paths inspected
- [ ] No-text master rendered
- [ ] Editable annotation layer completed
- [ ] QA accepted

## Decisions and Results

Record important assumptions, model changes, render settings, accepted results, and output paths here.
"""
    worklog_path = output_dir / "WORKLOG.md"
    if write_new(worklog_path, worklog):
        created.append(worklog_path)

    qa_log = f"""# Render QA Log

## Round 1 - Gray-box topology

- Date: {timestamp}
- Artifact:
- Result: pending
- Evidence inspected:
- Issues:
- Required corrections:

## Round 2 - Corrected physical render

- Date:
- Artifact:
- Result: pending
- Evidence inspected:
- Issues:
- Corrections made:
- Remaining uncertainty:
"""
    qa_path = output_dir / "qa" / "qa_log.md"
    if write_new(qa_path, qa_log):
        created.append(qa_path)

    print(f"initialized: {output_dir}")
    for path in created:
        print(f"created: {path.relative_to(output_dir)}")
    skipped = 5 - len([p for p in created if p.name in {"scene_manifest.json", "build_scene.py", "system_annotated.svg", "WORKLOG.md", "qa_log.md"}])
    if args.force and skipped:
        print("existing files were preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
