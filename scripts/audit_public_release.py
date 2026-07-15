#!/usr/bin/env python3
"""Audit an open-source skill checkout for private paths, media, and secrets."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


DISALLOWED_SUFFIXES = {
    ".blend",
    ".blend1",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp4",
    ".pdf",
    ".png",
    ".tif",
    ".tiff",
}
TEXT_SUFFIXES = {
    "",
    ".csv",
    ".json",
    ".md",
    ".py",
    ".svg",
    ".txt",
    ".yaml",
    ".yml",
}
PATTERNS = {
    "macOS user path": re.compile("/" + r"Users/[^/\s]+/"),
    "mounted private path": re.compile("/" + r"Volumes/[^/\s]+/"),
    "Windows user path": re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\s]+\\\\"),
    "WeChat identifier": re.compile(r"wxid_[a-zA-Z0-9_]+"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "generic bearer token": re.compile(r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._-]{16,}"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return [root / value.decode("utf-8") for value in result.stdout.split(b"\0") if value]
    return [path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    findings: list[str] = []
    files = tracked_files(root)
    for path in files:
        relative = path.relative_to(root)
        if path.is_symlink():
            target = path.resolve(strict=False)
            try:
                target.relative_to(root)
            except ValueError:
                findings.append(f"symlink points outside repository: {relative} -> {target}")
                continue
        suffix = path.suffix.lower()
        if suffix in DISALLOWED_SUFFIXES:
            findings.append(f"disallowed binary/project asset: {relative}")
        try:
            size = path.stat().st_size
        except OSError as exc:
            findings.append(f"cannot inspect {relative}: {exc}")
            continue
        if size > args.max_bytes:
            findings.append(f"file exceeds {args.max_bytes} bytes: {relative} ({size})")
        if suffix not in TEXT_SUFFIXES or size > args.max_bytes:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(content):
                findings.append(f"{label} found in {relative}")

    print(f"audited files: {len(files)}")
    if findings:
        for message in findings:
            print(f"ERROR: {message}")
        return 1
    print("PASS: no private paths, disallowed project media, oversized files, or common secrets detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
