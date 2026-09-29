"""Check a skill path without modifying configuration or resolving to stale copies."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    path = args.path.expanduser()
    errors = []
    if path.is_symlink() and not path.exists():
        errors.append("broken skill symlink")
    for name in ("SKILL.md", "manifest.yaml", "scripts/audit_blender_scene.py", "references/geometry-validation.md"):
        if not (path / name).is_file():
            errors.append(f"missing {name}")
    print(json.dumps({"path": str(path), "resolved": str(path.resolve()), "errors": errors,
                      "result": "FAIL" if errors else "PASS"}, indent=2))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
