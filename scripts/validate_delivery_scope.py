#!/usr/bin/env python3
"""Check declared delivery scope, not scientific evidence or rendered visibility."""
import argparse
import json
from pathlib import Path

VIEW_ALIASES = {
    "architecture": "architecture", "architecture_overview": "architecture",
    "physical-setup": "physical-setup", "physical_setup": "physical-setup",
    "component-sheet": "component-sheet", "component_sheet": "component-sheet",
    "mechanism": "mechanism", "mechanism_inset": "mechanism",
    "hybrid-figure": "hybrid-figure", "hybrid_figure": "hybrid-figure",
}
SYSTEM_VIEWS = {"architecture", "physical-setup"}
KINDS = {"physical", "field", "logical", "contact", "mechanical"}


def strings(value):
    return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)


def relationship_matches(required, actual):
    if (required["source"] != actual["source"]["component"] or
            required["target"] != actual["target"]["component"] or
            required["representation"] != actual.get("representation")):
        return False
    for key in ("id", "medium"):
        if key in required and required[key] != actual.get(key):
            return False
    return all(required[key] == actual[side].get("port")
               for key, side in (("source_port", "source"), ("target_port", "target"))
               if key in required)


def validate(contract, manifest):
    errors = []
    if not isinstance(contract, dict) or not isinstance(manifest, dict):
        return ["Contract and manifest must be JSON objects"]
    requested = contract.get("requested_views", contract.get("views", []))
    if not strings(requested) or not requested or any(v not in VIEW_ALIASES for v in requested):
        return ["Original requested views must be a nonempty list of supported view names"]
    requested = {VIEW_ALIASES[v] for v in requested}
    views = manifest.get("views", [])
    if not isinstance(views, list) or any(not isinstance(v, dict) or
            not isinstance(v.get("type"), str) or v["type"] not in VIEW_ALIASES for v in views):
        return ["Delivered views must be a list of supported view objects"]
    delivered = {VIEW_ALIASES[v["type"]] for v in views}
    for missing in sorted(requested - delivered):
        errors.append("Missing requested view: " + missing)
    if not requested & SYSTEM_VIEWS:
        return errors
    boundary = contract.get("system_boundary", "")
    if not isinstance(boundary, str) or boundary.strip().lower() in {"", "unresolved", "unknown", "pending"}:
        errors.append("System boundary is unresolved")
    nodes = contract.get("required_components", [])
    required_edges = contract.get("required_relationships", [])
    paths = contract.get("required_paths", [])
    if not strings(nodes) or not nodes or len(nodes) != len(set(nodes)):
        return errors + ["Required components must be a nonempty list of unique IDs"]
    nodes = set(nodes)
    if not isinstance(required_edges, list) or not required_edges:
        return errors + ["Required relationships must be a nonempty list"]
    allowed = {"source", "target", "representation", "id", "medium", "source_port", "target_port"}
    for e in required_edges:
        if (not isinstance(e, dict) or set(e) - allowed or
                not all(isinstance(e.get(k), str) and e[k].strip() for k in e) or
                not {"source", "target", "representation"} <= e.keys()):
            return errors + ["Invalid required relationship; use source/target component IDs, representation, and optional id/medium/source_port/target_port"]
        if e["source"] not in nodes or e["target"] not in nodes:
            errors.append("Required relationship endpoint is absent from required components")
        if e["representation"] not in KINDS:
            errors.append("Unknown required relationship representation")
    if not isinstance(paths, list) or not paths or not all(strings(p) for p in paths):
        return errors + ["Required paths must be a nonempty list of node-ID lists"]
    components = manifest.get("components", [])
    if not isinstance(components, list) or any(not isinstance(c, dict) or
            not isinstance(c.get("id"), str) or not c["id"].strip() for c in components):
        return errors + ["Components must have nonempty string IDs"]
    defined = {c["id"] for c in components}
    if len(defined) != len(components):
        errors.append("Duplicate component IDs")
    # A system must be traceable in one view, not spread over unrelated device sheets.
    for kind in sorted(requested & SYSTEM_VIEWS):
        complete = [v for v in views if VIEW_ALIASES[v["type"]] == kind and
                    strings(v.get("shows_components")) and
                    nodes <= set(v["shows_components"]) & defined]
        if not complete:
            errors.append("No " + kind + " view contains all required components")
    connections = manifest.get("connections", [])
    if not isinstance(connections, list):
        return errors + ["Connections must be a list"]
    for e in connections:
        if not isinstance(e, dict) or any(not isinstance(e.get(side), dict) or
                not isinstance(e[side].get("component"), str) for side in ("source", "target")):
            return errors + ["Connection endpoints must declare component IDs"]
        if any(e[side]["component"] not in defined for side in ("source", "target")):
            errors.append("Connection has an undefined endpoint")
    # One-to-one matching preserves parallel branches and optional identity constraints.
    assigned = {}

    def match(index, seen):
        for j, actual in enumerate(connections):
            if j not in seen and relationship_matches(required_edges[index], actual):
                seen.add(j)
                if j not in assigned or match(assigned[j], seen):
                    assigned[j] = index
                    return True
        return False

    for i, e in enumerate(required_edges):
        if not match(i, set()):
            errors.append("Missing distinct required relationship: " + str(e))
    adjacency = {}
    for e in required_edges:
        adjacency.setdefault(e["source"], set()).add(e["target"])
    for path in paths:
        if len(set(path)) < 2 or not set(path) <= nodes or any(a == b for a, b in zip(path, path[1:])):
            errors.append("Required path must contain at least two distinct required nodes without consecutive self-loops")
            continue
        for a, b in zip(path, path[1:]):
            if b not in adjacency.get(a, set()):
                errors.append(f"Functional path segment is not locked: {a} -> {b}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(json.loads(args.contract.read_text()), json.loads(args.manifest.read_text()))
    except (OSError, ValueError) as exc:
        errors = ["Cannot read scope inputs: " + str(exc)]
    report = {"status": "FAIL" if errors else "PASS", "errors": errors,
              "coverage": "Declared scope only; visual and evidence review required"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
