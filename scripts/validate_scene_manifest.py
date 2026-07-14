#!/usr/bin/env python3
"""Validate component, port, and connection truth in a scene manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
OPACITY = {"opaque", "transparent", "translucent", "mixed", "not-applicable"}
DIRECTIONS = {"in", "out", "bidirectional", "none"}
CONFIDENCE = {"verified", "inferred", "schematic", "unknown"}
RESOLUTION_KINDS = {
    "user-confirmed",
    "authoritative-source",
    "intentionally-omitted",
    "schematic-placeholder",
}
PATH_STYLES = {
    "straight",
    "ray",
    "guided",
    "flexible",
    "flow",
    "polyline",
    "field",
    "contact",
    "surface",
    "envelope",
    "abstract",
}
TIMING = {"continuous", "simultaneous", "sequential", "pulsed", "schematic"}
TURN_CAPS = {"reflect", "route", "bend", "guide", "split", "merge", "switch", "couple"}
JUNCTION_CAPS = {"split", "merge", "bus", "hub", "manifold", "switch", "couple"}
RESIZE_CAPS = {"focus", "resize", "expand", "reduce", "taper", "aperture", "lens", "nozzle"}
REPRESENTATIONS = {"physical", "field", "logical", "temporal", "contact", "motion-envelope", "containment"}
SCALE_LEVELS = {"environment", "system", "subsystem", "device", "component", "microstructure", "anatomical"}
SCALE_RANK = {"environment": 0, "system": 1, "subsystem": 2, "device": 3, "component": 4, "microstructure": 5}
MOBILITIES = {"fixed", "mobile", "articulated", "deformable", "wearable", "implantable", "flowing", "not-applicable"}
ASSEMBLY_RELATIONS = {"mounted", "contained", "integrated", "laminated", "embedded", "attached", "contacting"}
VIEW_TYPES = {"architecture", "physical-setup", "component-sheet", "mechanism", "detail", "cross-section", "exploded"}
VIEW_REPRESENTATIONS = {"physical", "logical", "hybrid", "mechanism"}
STATE_DISPLAYS = {"single", "sequence", "comparison", "exploded"}
MEDIUM_BEHAVIORS = {"transmit", "block", "attenuate", "couple", "guide", "contain", "convert"}
SEQUENCE_MODES = {"sequential", "cyclic", "state-comparison"}
MOTION_TYPES = {"translation", "rotation", "articulation", "deformation", "flight", "scan", "toolpath"}
INTERFACE_CLASSES = {"anatomical", "thermal", "mechanical", "adhesive", "sterile", "electrical", "optical"}
FIELD_MEDIA_HINTS = {"wireless", "rf-field", "magnetic-field", "electric-field", "acoustic-field", "ultrasound-field", "radiative"}
FLUID_MEDIA_HINTS = {"fluid", "liquid", "gas", "air", "coolant", "reagent", "sample", "waste", "vacuum"}


@dataclass
class Finding:
    severity: str
    code: str
    location: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def add(findings: list[Finding], severity: str, code: str, location: str, message: str) -> None:
    findings.append(Finding(severity, code, location, message))


def endpoint_text(endpoint: Any) -> str:
    if not isinstance(endpoint, dict):
        return ""
    return f"{endpoint.get('component', '')}:{endpoint.get('port', '')}"


def schema_at_least(data: dict[str, Any], major: int, minor: int) -> bool:
    value = str(data.get("schema_version", "0.0"))
    try:
        current_major, current_minor = (int(part) for part in value.split(".", 1))
    except (TypeError, ValueError):
        return False
    return (current_major, current_minor) >= (major, minor)


def evidence_refs(
    findings: list[Finding],
    value: Any,
    location: str,
    known_sources: set[str],
) -> None:
    if not isinstance(value, list) or not value:
        add(findings, "warning", "E010", location, "no evidence reference")
        return
    if not known_sources:
        return
    for source_id in value:
        if source_id not in known_sources:
            add(findings, "error", "E011", location, f"unknown evidence source: {source_id}")


def detect_parent_cycle(components: dict[str, dict[str, Any]], start: str) -> bool:
    seen: set[str] = set()
    current: str | None = start
    while current:
        if current in seen:
            return True
        seen.add(current)
        parent = components.get(current, {}).get("parent")
        current = parent if isinstance(parent, str) else None
    return False


def validate(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    v11 = schema_at_least(data, 1, 1)
    v12 = schema_at_least(data, 1, 2)
    required = (
        "schema_version",
        "title",
        "domain",
        "truth_level",
        "views",
        "deliverables",
        "components",
        "connections",
        "assumptions",
        "open_questions",
        "acceptance_criteria",
    )
    for key in required:
        if key not in data:
            add(findings, "error", "M001", "$", f"missing top-level key: {key}")

    sources_raw = data.get("sources", [])
    if v11 and (not isinstance(sources_raw, list) or not sources_raw):
        add(findings, "error", "E001", "sources", "schema 1.1 requires a non-empty sources list")
        sources_raw = []
    elif not isinstance(sources_raw, list):
        add(findings, "error", "E002", "sources", "sources must be a list")
        sources_raw = []
    sources: set[str] = set()
    for index, source in enumerate(sources_raw):
        loc = f"sources[{index}]"
        if not isinstance(source, dict):
            add(findings, "error", "E003", loc, "source must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not ID_RE.match(source_id.lower()):
            add(findings, "error", "E004", loc, "source id must be a stable alphanumeric identifier")
            continue
        if source_id in sources:
            add(findings, "error", "E005", loc, f"duplicate source id: {source_id}")
            continue
        sources.add(source_id)
        for key in ("type", "title", "authority"):
            if not source.get(key):
                add(findings, "error", "E006", loc, f"missing {key}")
        if not source.get("locator"):
            add(findings, "warning", "E007", loc, "source has no URL, DOI, or local path locator")

    components_raw = data.get("components", [])
    connections_raw = data.get("connections", [])
    if not isinstance(components_raw, list) or not components_raw:
        add(findings, "error", "M002", "components", "components must be a non-empty list")
        components_raw = []
    if not isinstance(connections_raw, list):
        add(findings, "error", "M003", "connections", "connections must be a list")
        connections_raw = []

    components: dict[str, dict[str, Any]] = {}
    ports: dict[tuple[str, str], dict[str, Any]] = {}
    for index, component in enumerate(components_raw):
        loc = f"components[{index}]"
        if not isinstance(component, dict):
            add(findings, "error", "C001", loc, "component must be an object")
            continue
        component_id = component.get("id")
        if not isinstance(component_id, str) or not ID_RE.match(component_id):
            add(findings, "error", "C002", loc, "id must use lowercase letters, digits, dot, underscore, or hyphen")
            continue
        if component_id in components:
            add(findings, "error", "C003", loc, f"duplicate component id: {component_id}")
            continue
        components[component_id] = component
        cloc = f"component:{component_id}"
        for key in ("name", "category", "physical_role"):
            if not component.get(key):
                add(findings, "error", "C004", cloc, f"missing {key}")
        if v11 and component.get("scale_level") not in SCALE_LEVELS:
            add(findings, "error", "C011", cloc, f"invalid or missing scale_level: {component.get('scale_level')!r}")
        elif component.get("scale_level") is not None and component.get("scale_level") not in SCALE_LEVELS:
            add(findings, "error", "C011", cloc, f"invalid scale_level: {component.get('scale_level')!r}")
        if v11 and component.get("mobility") not in MOBILITIES:
            add(findings, "error", "C012", cloc, f"invalid or missing mobility: {component.get('mobility')!r}")
        elif component.get("mobility") is not None and component.get("mobility") not in MOBILITIES:
            add(findings, "error", "C012", cloc, f"invalid mobility: {component.get('mobility')!r}")
        if component.get("opacity") not in OPACITY:
            add(findings, "error", "C005", cloc, f"invalid opacity: {component.get('opacity')!r}")
        capabilities = component.get("capabilities", [])
        if not isinstance(capabilities, list):
            add(findings, "error", "C006", cloc, "capabilities must be a list")
            capabilities = []
        evidence_refs(findings, component.get("evidence", []), cloc, sources)
        if component.get("confidence") not in CONFIDENCE:
            add(findings, "error", "C008", cloc, f"invalid confidence: {component.get('confidence')!r}")
        elif v12 and component.get("confidence") == "unknown":
            add(findings, "error", "U001", cloc, "unknown factual component must be resolved, omitted, or moved to an explicit unresolved schematic")
        mount = component.get("mount")
        if not isinstance(mount, dict):
            add(findings, "error", "C009", cloc, "mount must be an object")
        elif mount.get("required") and (not mount.get("type") or not mount.get("attachment")):
            add(findings, "error", "C010", cloc, "required mount needs type and attachment")

        parent = component.get("parent")
        if parent is not None and not isinstance(parent, str):
            add(findings, "error", "C013", cloc, "parent must be a component id")
        if parent is not None and component.get("assembly_relation") not in ASSEMBLY_RELATIONS:
            add(findings, "error", "C014", cloc, "a child component needs a valid assembly_relation")
        medium_behavior = component.get("medium_behavior", {})
        if not isinstance(medium_behavior, dict):
            add(findings, "error", "C015", cloc, "medium_behavior must be an object")
        else:
            for medium, behavior in medium_behavior.items():
                if not isinstance(medium, str) or not medium:
                    add(findings, "error", "C016", cloc, "medium_behavior keys must be non-empty strings")
                if behavior not in MEDIUM_BEHAVIORS:
                    add(findings, "error", "C017", cloc, f"invalid medium behavior {behavior!r} for {medium}")

        states = component.get("states", [])
        if not isinstance(states, list):
            add(findings, "error", "C018", cloc, "states must be a list")
            states = []
        seen_states: set[str] = set()
        for sindex, state in enumerate(states):
            sloc = f"{cloc}.states[{sindex}]"
            if not isinstance(state, dict) or not isinstance(state.get("id"), str):
                add(findings, "error", "C019", sloc, "state must be an object with an id")
                continue
            if state["id"] in seen_states:
                add(findings, "error", "C020", sloc, f"duplicate state id: {state['id']}")
            seen_states.add(state["id"])
        if component.get("mobility") == "deformable" and not states:
            add(findings, "warning", "C021", cloc, "deformable component has no declared reference/deformed states")

        port_list = component.get("ports", [])
        ports_required = component.get("ports_required", True)
        if not isinstance(port_list, list) or (not port_list and ports_required):
            add(findings, "warning", "P001", cloc, "component declares no ports")
            continue
        seen_ports: set[str] = set()
        for pindex, port in enumerate(port_list):
            ploc = f"{cloc}.ports[{pindex}]"
            if not isinstance(port, dict):
                add(findings, "error", "P002", ploc, "port must be an object")
                continue
            port_id = port.get("id")
            if not isinstance(port_id, str) or not ID_RE.match(port_id):
                add(findings, "error", "P003", ploc, "invalid port id")
                continue
            if port_id in seen_ports:
                add(findings, "error", "P004", ploc, f"duplicate port id: {port_id}")
                continue
            seen_ports.add(port_id)
            ports[(component_id, port_id)] = port
            if port.get("direction") not in DIRECTIONS:
                add(findings, "error", "P005", ploc, f"invalid direction: {port.get('direction')!r}")
            media = port.get("media", [])
            if not isinstance(media, list) or not media:
                add(findings, "error", "P006", ploc, "media must be a non-empty list")
            if not port.get("face"):
                add(findings, "warning", "P007", ploc, "port has no local face/orientation label")

    for component_id, component in components.items():
        parent = component.get("parent")
        if component.get("scale_level") == "microstructure" and not parent:
            add(findings, "error", "H003", f"component:{component_id}", "microstructure must be tied to a parent device or component")
        if parent is None:
            continue
        if parent not in components:
            add(findings, "error", "H001", f"component:{component_id}", f"unknown parent component: {parent}")
        elif parent == component_id or detect_parent_cycle(components, component_id):
            add(findings, "error", "H002", f"component:{component_id}", "component hierarchy contains a parent cycle")
        else:
            child_scale = component.get("scale_level")
            parent_scale = components[parent].get("scale_level")
            if child_scale in SCALE_RANK and parent_scale in SCALE_RANK and SCALE_RANK[child_scale] <= SCALE_RANK[parent_scale]:
                add(findings, "warning", "H004", f"component:{component_id}", f"child scale {child_scale} is not finer than parent {parent} scale {parent_scale}")

    connections: dict[str, dict[str, Any]] = {}
    connection_endpoints: dict[str, dict[str, tuple[str, str] | None]] = {}
    anatomical_contact_components: set[str] = set()
    endpoint_use: Counter[tuple[str, str]] = Counter()
    for index, connection in enumerate(connections_raw):
        loc = f"connections[{index}]"
        if not isinstance(connection, dict):
            add(findings, "error", "N001", loc, "connection must be an object")
            continue
        connection_id = connection.get("id")
        if not isinstance(connection_id, str) or not ID_RE.match(connection_id):
            add(findings, "error", "N002", loc, "invalid connection id")
            continue
        if connection_id in connections:
            add(findings, "error", "N003", loc, f"duplicate connection id: {connection_id}")
            continue
        connections[connection_id] = connection
        nloc = f"connection:{connection_id}"
        representation = connection.get("representation", "physical" if not v11 else None)
        if representation not in REPRESENTATIONS:
            add(findings, "error", "N029", nloc, f"invalid or missing representation: {representation!r}")
        medium = connection.get("medium")
        if not isinstance(medium, str) or not medium:
            add(findings, "error", "N004", nloc, "connection needs a medium")

        endpoint_values: dict[str, tuple[str, str] | None] = {}
        for endpoint_name in ("source", "target"):
            endpoint = connection.get(endpoint_name)
            if not isinstance(endpoint, dict):
                add(findings, "error", "N005", nloc, f"{endpoint_name} must be an object")
                endpoint_values[endpoint_name] = None
                continue
            key = (endpoint.get("component"), endpoint.get("port"))
            if key not in ports:
                add(findings, "error", "N006", nloc, f"unknown {endpoint_name} endpoint: {endpoint_text(endpoint)}")
                endpoint_values[endpoint_name] = None
                continue
            endpoint_values[endpoint_name] = key
            endpoint_use[key] += 1
            port = ports[key]
            direction = port.get("direction")
            if endpoint_name == "source" and direction not in {"out", "bidirectional"}:
                add(findings, "error", "N007", nloc, f"source port has incompatible direction: {direction}")
            if endpoint_name == "target" and direction not in {"in", "bidirectional"}:
                add(findings, "error", "N008", nloc, f"target port has incompatible direction: {direction}")
            if medium and medium not in port.get("media", []):
                add(findings, "error", "N009", nloc, f"medium {medium!r} is not accepted by {endpoint_text(endpoint)}")

        connection_endpoints[connection_id] = endpoint_values
        interface_class = connection.get("interface_class")
        if representation == "contact" and v11 and interface_class not in INTERFACE_CLASSES:
            add(findings, "error", "R008", nloc, f"contact connection needs a valid interface_class: {interface_class!r}")
        if representation != "contact" and interface_class is not None:
            add(findings, "warning", "R009", nloc, "interface_class is only meaningful for contact connections")
        if representation == "contact" and interface_class == "anatomical":
            for value in endpoint_values.values():
                if value:
                    anatomical_contact_components.add(value[0])

        if endpoint_values.get("source") and endpoint_values.get("source") == endpoint_values.get("target"):
            add(findings, "warning", "N010", nloc, "source and target are the same port")

        path = connection.get("path")
        if not isinstance(path, dict):
            add(findings, "error", "N011", nloc, "path must be an object")
            path = {}
        style = path.get("style")
        if style not in PATH_STYLES:
            add(findings, "error", "N012", nloc, f"invalid path style: {style!r}")
        if representation == "logical" and style != "abstract":
            add(findings, "error", "R001", nloc, "logical connections must use an abstract path, not physical routing")
        if representation == "temporal" and (style != "abstract" or connection.get("timing") not in {"sequential", "pulsed"}):
            add(findings, "error", "R002", nloc, "temporal connections must be abstract and sequential or pulsed")
        if representation == "field" and style not in {"field", "ray", "abstract"}:
            add(findings, "error", "R003", nloc, "wireless or field coupling must not be drawn as a cable, tube, or guided path")
        if representation == "contact" and style not in {"contact", "surface"}:
            add(findings, "error", "R004", nloc, "contact interfaces must use contact or surface path style")
        if representation == "motion-envelope" and style != "envelope":
            add(findings, "error", "R005", nloc, "motion-envelope connections must use envelope path style")
        if representation == "physical" and isinstance(medium, str) and (
            medium in FIELD_MEDIA_HINTS or medium.endswith("-field")
        ):
            add(findings, "error", "R006", nloc, "field medium is declared as a literal physical connection")
        bends_at = path.get("bends_at", [])
        if not isinstance(bends_at, list):
            add(findings, "error", "N013", nloc, "bends_at must be a list")
            bends_at = []
        if style == "straight" and bends_at:
            add(findings, "error", "N014", nloc, "straight path cannot declare bends")
        for component_id in bends_at:
            component = components.get(component_id)
            if component is None:
                add(findings, "error", "N015", nloc, f"bend references unknown component: {component_id}")
            elif not (set(component.get("capabilities", [])) & TURN_CAPS):
                add(findings, "error", "N016", nloc, f"{component_id} bends the path but has no turning capability")
        passes = path.get("passes_through", [])
        if not isinstance(passes, list):
            add(findings, "error", "N017", nloc, "passes_through must be a list")
            passes = []
        for component_id in passes:
            component = components.get(component_id)
            if component is None:
                add(findings, "error", "N018", nloc, f"pass-through references unknown component: {component_id}")
                continue
            behavior = component.get("medium_behavior", {}).get(medium)
            if behavior == "block":
                add(findings, "error", "N019", nloc, f"{medium} is blocked by component: {component_id}")
            elif representation == "field":
                if behavior not in {"transmit", "attenuate", "couple"}:
                    add(findings, "warning", "N030", nloc, f"field pass-through lacks transmission evidence for: {component_id}")
            elif behavior not in {"transmit", "guide", "contain", "couple"} and component.get("opacity") == "opaque":
                add(findings, "error", "N019", nloc, f"path passes through opaque component: {component_id}")
            elif behavior is None and component.get("opacity") == "mixed":
                add(findings, "warning", "N020", nloc, f"verify pass-through uses the functional region of: {component_id}")

        profile = connection.get("profile", [])
        if profile and not isinstance(profile, list):
            add(findings, "error", "N021", nloc, "profile must be a list")
            profile = []
        last_width: float | None = None
        for pindex, station in enumerate(profile):
            sloc = f"{nloc}.profile[{pindex}]"
            if not isinstance(station, dict):
                add(findings, "error", "N022", sloc, "profile station must be an object")
                continue
            width = station.get("width")
            if not isinstance(width, (int, float)) or width <= 0:
                add(findings, "error", "N023", sloc, "width must be positive")
                continue
            if last_width is not None and abs(float(width) - last_width) > 1e-9:
                cause = station.get("cause_component")
                component = components.get(cause)
                if not cause:
                    add(findings, "error", "N024", sloc, "width changes without cause_component")
                elif component is None:
                    add(findings, "error", "N025", sloc, f"width-change cause is unknown: {cause}")
                elif not (set(component.get("capabilities", [])) & RESIZE_CAPS):
                    add(findings, "error", "N026", sloc, f"{cause} changes width but has no resize/focus capability")
            last_width = float(width)
        if representation in {"logical", "temporal", "contact", "motion-envelope", "containment"} and profile:
            add(findings, "error", "R007", nloc, f"{representation} connection must not encode a physical width profile")
        if connection.get("timing") not in TIMING:
            add(findings, "error", "N027", nloc, f"invalid timing: {connection.get('timing')!r}")
        evidence_refs(findings, connection.get("evidence", []), nloc, sources)

    for key, count in endpoint_use.items():
        if count <= 1:
            continue
        component_id, port_id = key
        port = ports[key]
        component = components[component_id]
        if not port.get("allows_multiple") and not (set(component.get("capabilities", [])) & JUNCTION_CAPS):
            add(
                findings,
                "error",
                "T001",
                f"port:{component_id}:{port_id}",
                f"port is used by {count} connections without a declared splitter, hub, bus, manifold, or switch capability",
            )

    for key in sorted(set(ports) - set(endpoint_use)):
        component_id, port_id = key
        if ports[key].get("direction") != "none":
            add(findings, "warning", "T002", f"port:{component_id}:{port_id}", "declared port is unconnected")

    for component_id, component in components.items():
        if component.get("requires_body_interface") and component_id not in anatomical_contact_components:
            add(findings, "error", "B001", f"component:{component_id}", "wearable or implantable device lacks a declared body/contact interface")

    views_raw = data.get("views", [])
    if not views_raw:
        add(findings, "error", "V001", "views", "at least one view is required")
        views_raw = []
    elif not isinstance(views_raw, list):
        add(findings, "error", "V005", "views", "views must be a list")
        views_raw = []
    views: dict[str, dict[str, Any]] = {}
    for index, view in enumerate(views_raw):
        loc = f"views[{index}]"
        if not isinstance(view, dict):
            add(findings, "error", "V006", loc, "view must be an object")
            continue
        view_id = view.get("id")
        if not isinstance(view_id, str) or not ID_RE.match(view_id):
            add(findings, "error", "V007", loc, "invalid view id")
            continue
        if view_id in views:
            add(findings, "error", "V008", loc, f"duplicate view id: {view_id}")
            continue
        views[view_id] = view
        if view.get("type") not in VIEW_TYPES:
            add(findings, "error", "V009", loc, f"invalid view type: {view.get('type')!r}")
        if v11 and view.get("representation") not in VIEW_REPRESENTATIONS:
            add(findings, "error", "V010", loc, f"invalid or missing representation: {view.get('representation')!r}")
        if v11 and view.get("scale_level") not in SCALE_LEVELS:
            add(findings, "error", "V011", loc, f"invalid or missing scale_level: {view.get('scale_level')!r}")
        if v11 and view.get("state_display") not in STATE_DISPLAYS:
            add(findings, "error", "V012", loc, f"invalid or missing state_display: {view.get('state_display')!r}")
        shown = view.get("shows_components", [])
        if shown and not isinstance(shown, list):
            add(findings, "error", "V013", loc, "shows_components must be a list")
        elif isinstance(shown, list):
            for component_id in shown:
                if component_id not in components:
                    add(findings, "error", "V014", loc, f"view references unknown component: {component_id}")
        parent_view = view.get("parent_view")
        if parent_view is not None and not isinstance(parent_view, str):
            add(findings, "error", "V015", loc, "parent_view must be a view id")

    for view_id, view in views.items():
        parent_view = view.get("parent_view")
        if parent_view and parent_view not in views:
            add(findings, "error", "V016", f"view:{view_id}", f"unknown parent_view: {parent_view}")
        elif parent_view:
            child_scale = view.get("scale_level")
            parent_scale = views[parent_view].get("scale_level")
            if child_scale in SCALE_RANK and parent_scale in SCALE_RANK and SCALE_RANK[child_scale] <= SCALE_RANK[parent_scale]:
                add(findings, "warning", "V018", f"view:{view_id}", f"detail view scale {child_scale} is not finer than parent view scale {parent_scale}")
        if view.get("state_display") == "exploded" and view.get("representation") not in {"physical", "hybrid"}:
            add(findings, "error", "V017", f"view:{view_id}", "exploded state display needs a physical or hybrid view")

    sequences_raw = data.get("sequences", [])
    if not isinstance(sequences_raw, list):
        add(findings, "error", "S001", "sequences", "sequences must be a list")
        sequences_raw = []
    for index, sequence in enumerate(sequences_raw):
        loc = f"sequences[{index}]"
        if not isinstance(sequence, dict) or not isinstance(sequence.get("id"), str):
            add(findings, "error", "S002", loc, "sequence must be an object with an id")
            continue
        if sequence.get("mode") not in SEQUENCE_MODES:
            add(findings, "error", "S003", loc, f"invalid sequence mode: {sequence.get('mode')!r}")
        steps = sequence.get("steps", [])
        if not isinstance(steps, list) or len(steps) < 2:
            add(findings, "error", "S004", loc, "sequence needs at least two ordered steps")
            steps = []
        for sindex, step in enumerate(steps):
            sloc = f"{loc}.steps[{sindex}]"
            if not isinstance(step, dict):
                add(findings, "error", "S005", sloc, "step must be an object")
                continue
            component_id = step.get("component")
            state_id = step.get("state")
            component = components.get(component_id)
            if component is None:
                add(findings, "error", "S006", sloc, f"unknown sequence component: {component_id}")
                continue
            known_states = {state.get("id") for state in component.get("states", []) if isinstance(state, dict)}
            if state_id not in known_states:
                add(findings, "error", "S007", sloc, f"unknown state {state_id!r} for component {component_id}")
        reused = sequence.get("reused_components", [])
        if not isinstance(reused, list) or not reused:
            add(findings, "warning", "S008", loc, "sequence does not identify reused hardware")
        else:
            for component_id in reused:
                if component_id not in components:
                    add(findings, "error", "S009", loc, f"unknown reused component: {component_id}")
                    continue
                appearances = sum(1 for step in steps if isinstance(step, dict) and step.get("component") == component_id)
                if appearances < 2:
                    add(findings, "error", "S010", loc, f"reused component {component_id} appears in only {appearances} sequence step(s)")
        evidence_refs(findings, sequence.get("evidence", []), loc, sources)

    routes_raw = data.get("routes", [])
    if not isinstance(routes_raw, list):
        add(findings, "error", "F001", "routes", "routes must be a list")
        routes_raw = []
    for index, route in enumerate(routes_raw):
        loc = f"routes[{index}]"
        if not isinstance(route, dict) or not isinstance(route.get("id"), str):
            add(findings, "error", "F002", loc, "route must be an object with an id")
            continue
        connection_ids = route.get("connections", [])
        if not isinstance(connection_ids, list) or not connection_ids:
            add(findings, "error", "F003", loc, "route needs at least one ordered connection")
            connection_ids = []
        route_connections: list[dict[str, tuple[str, str] | None]] = []
        for connection_id in connection_ids:
            if connection_id not in connections:
                add(findings, "error", "F004", loc, f"unknown route connection: {connection_id}")
                continue
            if route.get("medium") != connections[connection_id].get("medium"):
                add(findings, "error", "F005", loc, f"connection {connection_id} uses a different medium")
            route_connections.append(connection_endpoints[connection_id])
        for cindex in range(len(route_connections) - 1):
            current_target = route_connections[cindex].get("target")
            next_source = route_connections[cindex + 1].get("source")
            if current_target and next_source and current_target[0] != next_source[0]:
                add(findings, "error", "F006", loc, f"route is discontinuous between positions {cindex} and {cindex + 1}")
        if not isinstance(route.get("open"), bool):
            add(findings, "error", "F007", loc, "route must declare whether it is open")
        if route.get("open") and route_connections:
            first_source = route_connections[0].get("source")
            final_target = route_connections[-1].get("target")
            if first_source and route.get("source_boundary") != first_source[0]:
                add(findings, "error", "F010", loc, "source_boundary does not match the first route component")
            if final_target and route.get("sink_boundary") != final_target[0]:
                add(findings, "error", "F011", loc, "sink_boundary does not match the final route component")
        medium = str(route.get("medium", ""))
        if any(token in medium for token in FLUID_MEDIA_HINTS):
            driver = route.get("driver_component")
            if driver not in components:
                add(findings, "error", "F008", loc, "fluid route needs a declared driver_component")
            elif not (set(components[driver].get("capabilities", [])) & {"pump", "circulate", "fan", "compress", "gravity-feed"}):
                add(findings, "error", "F009", loc, f"route driver {driver} has no flow-driving capability")
            else:
                route_components = {
                    endpoint[0]
                    for pair in route_connections
                    for endpoint in pair.values()
                    if endpoint
                }
                if driver not in route_components:
                    add(findings, "error", "F012", loc, f"route driver {driver} is not part of the declared route")
        evidence_refs(findings, route.get("evidence", []), loc, sources)

    loops_raw = data.get("loops", [])
    if not isinstance(loops_raw, list):
        add(findings, "error", "L001", "loops", "loops must be a list")
        loops_raw = []
    for index, loop in enumerate(loops_raw):
        loc = f"loops[{index}]"
        if not isinstance(loop, dict) or not isinstance(loop.get("id"), str):
            add(findings, "error", "L002", loc, "loop must be an object with an id")
            continue
        connection_ids = loop.get("connections", [])
        if not isinstance(connection_ids, list) or len(connection_ids) < 2:
            add(findings, "error", "L003", loc, "loop needs at least two ordered connections")
            connection_ids = []
        loop_connections: list[dict[str, tuple[str, str] | None]] = []
        for connection_id in connection_ids:
            if connection_id not in connections:
                add(findings, "error", "L004", loc, f"unknown loop connection: {connection_id}")
                continue
            if loop.get("medium") != connections[connection_id].get("medium"):
                add(findings, "error", "L005", loc, f"connection {connection_id} uses a different medium")
            loop_connections.append(connection_endpoints[connection_id])
        for cindex in range(len(loop_connections) - 1):
            current_target = loop_connections[cindex].get("target")
            next_source = loop_connections[cindex + 1].get("source")
            if current_target and next_source and current_target[0] != next_source[0]:
                add(findings, "error", "L006", loc, f"loop is discontinuous between positions {cindex} and {cindex + 1}")
        if loop.get("closed") and len(loop_connections) >= 2:
            final_target = loop_connections[-1].get("target")
            first_source = loop_connections[0].get("source")
            if final_target and first_source and final_target[0] != first_source[0]:
                add(findings, "error", "L007", loc, "closed loop does not return to its starting component")
        medium = str(loop.get("medium", ""))
        if loop.get("closed") and any(token in medium for token in FLUID_MEDIA_HINTS):
            driver = loop.get("driver_component")
            if driver not in components:
                add(findings, "error", "L008", loc, "closed fluid loop needs a declared driver_component")
            elif not (set(components[driver].get("capabilities", [])) & {"pump", "circulate", "fan", "compress"}):
                add(findings, "error", "L009", loc, f"loop driver {driver} has no pump/circulation capability")
            else:
                loop_components = {
                    endpoint[0]
                    for pair in loop_connections
                    for endpoint in pair.values()
                    if endpoint
                }
                if driver not in loop_components:
                    add(findings, "error", "L010", loc, f"loop driver {driver} is not part of the declared loop")
        evidence_refs(findings, loop.get("evidence", []), loc, sources)

    motions_raw = data.get("motions", [])
    if not isinstance(motions_raw, list):
        add(findings, "error", "O001", "motions", "motions must be a list")
        motions_raw = []
    motion_components: set[str] = set()
    for index, motion in enumerate(motions_raw):
        loc = f"motions[{index}]"
        if not isinstance(motion, dict) or not isinstance(motion.get("id"), str):
            add(findings, "error", "O002", loc, "motion must be an object with an id")
            continue
        component_id = motion.get("component")
        component = components.get(component_id)
        if component is None:
            add(findings, "error", "O003", loc, f"unknown moving component: {component_id}")
            continue
        motion_components.add(component_id)
        if component.get("mobility") not in {"mobile", "articulated", "deformable"}:
            add(findings, "error", "O004", loc, f"component {component_id} is not declared mobile, articulated, or deformable")
        if motion.get("type") not in MOTION_TYPES:
            add(findings, "error", "O005", loc, f"invalid motion type: {motion.get('type')!r}")
        envelope = motion.get("envelope_component")
        if not envelope or envelope not in components:
            add(findings, "error", "O006", loc, "motion needs a declared envelope_component")
        elif components[envelope].get("category") != "motion-envelope":
            add(findings, "error", "O007", loc, "envelope_component must use category motion-envelope")
        if not motion.get("degrees_of_freedom"):
            add(findings, "error", "O008", loc, "motion needs declared degrees_of_freedom")
        evidence_refs(findings, motion.get("evidence", []), loc, sources)

    for component_id, component in components.items():
        if component.get("mobility") in {"mobile", "articulated"} and component_id not in motion_components:
            add(findings, "warning", "O009", f"component:{component_id}", "mobile/articulated component has no motion envelope")

    if not data.get("deliverables"):
        add(findings, "warning", "V002", "deliverables", "no deliverables are declared")
    if not data.get("acceptance_criteria"):
        add(findings, "error", "V003", "acceptance_criteria", "acceptance criteria are required")
    assumptions = data.get("assumptions", [])
    if not isinstance(assumptions, list):
        add(findings, "error", "U002", "assumptions", "assumptions must be a list")
    elif v12:
        for index, assumption in enumerate(assumptions):
            loc = f"assumptions[{index}]"
            if not isinstance(assumption, dict):
                add(findings, "error", "U003", loc, "assumption must be an object")
                continue
            if assumption.get("status") != "resolved":
                add(findings, "error", "U004", loc, "open factual assumption blocks detailed modeling")
                continue
            resolution = assumption.get("resolution")
            if not isinstance(resolution, dict) or resolution.get("kind") not in RESOLUTION_KINDS:
                add(findings, "error", "U005", loc, "resolved assumption needs an allowed resolution.kind")

    open_questions = data.get("open_questions", [])
    if not isinstance(open_questions, list):
        add(findings, "error", "U006", "open_questions", "open_questions must be a list")
    elif open_questions:
        if not v12:
            add(findings, "warning", "V004", "open_questions", f"{len(open_questions)} open question(s) remain")
        for index, question in enumerate(open_questions):
            loc = f"open_questions[{index}]"
            if not v12:
                continue
            if not isinstance(question, dict) or not question.get("id") or not question.get("question"):
                add(findings, "error", "U007", loc, "schema 1.2 question needs id and question")
                continue
            status = question.get("status", "open")
            blocking = question.get("blocking", True)
            if status != "resolved":
                severity = "error" if blocking else "warning"
                add(findings, severity, "U008", loc, "unresolved question remains" + (" and blocks modeling" if blocking else ""))
                continue
            resolution = question.get("resolution")
            if not isinstance(resolution, dict) or resolution.get("kind") not in RESOLUTION_KINDS:
                add(findings, "error", "U009", loc, "resolved question needs an allowed resolution.kind")
    return findings


def write_report(path: Path, manifest: Path, findings: list[Finding]) -> None:
    counts = Counter(item.severity for item in findings)
    lines = [
        "# Scene Manifest Validation",
        "",
        f"- Manifest: `{manifest}`",
        f"- Errors: {counts['error']}",
        f"- Warnings: {counts['warning']}",
        f"- Result: {'FAIL' if counts['error'] else 'PASS'}",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("No findings.")
    else:
        for item in findings:
            lines.append(f"- **{item.severity.upper()} {item.code}** `{item.location}`: {item.message}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read manifest: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("error: manifest root must be an object", file=sys.stderr)
        return 2
    findings = validate(data)
    counts = Counter(item.severity for item in findings)
    for item in findings:
        print(f"{item.severity.upper()} {item.code} {item.location}: {item.message}")
    print(f"summary: {counts['error']} error(s), {counts['warning']} warning(s)")
    if args.report:
        write_report(args.report, args.manifest, findings)
        print(f"report: {args.report}")
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
