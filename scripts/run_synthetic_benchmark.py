#!/usr/bin/env python3
"""Run positive and mutation tests across original synthetic system fixtures."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = SKILL_DIR / "assets" / "synthetic_benchmark.json"
VALIDATOR_PATH = SKILL_DIR / "scripts" / "validate_scene_manifest.py"


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("ssr_manifest_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    return parser.parse_args()


def port(port_id: str, direction: str, media: list[str], face: str, *, multiple: bool = False) -> dict[str, Any]:
    return {
        "id": port_id,
        "direction": direction,
        "media": media,
        "face": face,
        "face_position": face,
        "allows_multiple": multiple,
        "evidence": ["S1"],
        "identity_confidence": "schematic",
    }


def component(
    component_id: str,
    name: str,
    category: str,
    role: str,
    *,
    ports: list[dict[str, Any]] | None = None,
    scale: str = "device",
    mobility: str = "fixed",
    opacity: str = "opaque",
    capabilities: list[str] | None = None,
    parent: str | None = None,
    relation: str | None = None,
    states: list[str] | None = None,
    medium_behavior: dict[str, str] | None = None,
    body_interface: bool = False,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "id": component_id,
        "name": name,
        "category": category,
        "physical_role": role,
        "scale_level": scale,
        "mobility": mobility,
        "opacity": opacity,
        "capabilities": capabilities or [],
        "ports": ports or [],
        "ports_required": ports is not None,
        "active_faces": [],
        "mount": {"required": False},
        "evidence": ["S1"],
        "confidence": "inferred",
        "existence_status": "schematic-placeholder",
        "existence_evidence": ["S1"],
    }
    if parent:
        value["parent"] = parent
        value["assembly_relation"] = relation or "attached"
    if states is not None:
        value["states"] = [{"id": state, "name": state.replace("-", " ")} for state in states]
    if medium_behavior:
        value["medium_behavior"] = medium_behavior
    if body_interface:
        value["requires_body_interface"] = True
    return value


def connection(
    connection_id: str,
    medium: str,
    source: tuple[str, str],
    target: tuple[str, str],
    *,
    representation: str = "physical",
    style: str = "straight",
    timing: str = "continuous",
    passes: list[str] | None = None,
    interface_class: str | None = None,
) -> dict[str, Any]:
    value = {
        "id": connection_id,
        "representation": representation,
        "medium": medium,
        "source": {"component": source[0], "port": source[1]},
        "target": {"component": target[0], "port": target[1]},
        "path": {"style": style, "bends_at": [], "passes_through": passes or []},
        "profile": [],
        "timing": timing,
        "evidence": ["S1"],
    }
    if interface_class:
        value["interface_class"] = interface_class
    return value


def view(
    view_id: str,
    view_type: str,
    representation: str,
    scale: str,
    state_display: str,
    components: list[str],
    *,
    parent: str | None = None,
) -> dict[str, Any]:
    value = {
        "id": view_id,
        "type": view_type,
        "representation": representation,
        "scale_level": scale,
        "state_display": state_display,
        "purpose": f"Synthetic {view_type} validation view",
        "camera": "controlled-technical-view",
        "shows_components": components,
    }
    if parent:
        value["parent_view"] = parent
    return value


def finish(
    case: dict[str, Any],
    components: list[dict[str, Any]],
    connections: list[dict[str, Any]],
    *,
    views: list[dict[str, Any]] | None = None,
    sequences: list[dict[str, Any]] | None = None,
    routes: list[dict[str, Any]] | None = None,
    loops: list[dict[str, Any]] | None = None,
    motions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    component_ids = [item["id"] for item in components]
    used_ports = {
        (connection[endpoint]["component"], connection[endpoint]["port"])
        for connection in connections
        for endpoint in ("source", "target")
    }
    for item in components:
        for item_port in item.get("ports", []):
            key = (item["id"], item_port["id"])
            if key in used_ports:
                item_port["connection_expectation"] = "connected"
            else:
                item_port["connection_expectation"] = "intentionally-open"
                item_port["status_reason"] = "Unused by this synthetic validation view"
                item_port["status_evidence"] = ["S1"]
    return {
        "schema_version": "1.3",
        "title": case["title"],
        "domain": case["domain_family"],
        "truth_level": "synthetic topology-faithful validation",
        "sources": [
            {
                "id": "S1",
                "type": "synthetic-test-definition",
                "title": case["title"],
                "locator": "assets/synthetic_benchmark.json",
                "authority": "scientific-system-renderer",
                "accessed": None,
            }
        ],
        "views": views
        or [view("physical-setup", "physical-setup", "physical", "system", "single", component_ids)],
        "deliverables": ["system_no_text.png", "system_annotated.svg"],
        "components": components,
        "connections": connections,
        "sequences": sequences or [],
        "routes": routes or [],
        "loops": loops or [],
        "motions": motions or [],
        "assumptions": [],
        "open_questions": [],
        "acceptance_criteria": [
            "All rendered paths are traceable to declared interfaces",
            "Physical and abstract relationships remain visually distinct",
        ],
    }


def optical_stack(case: dict[str, Any]) -> dict[str, Any]:
    components = [
        component("source", "Input field", "source", "Generate the optical field", ports=[port("out", "out", ["optical"], "front")]),
        component(
            "diffractive-layer",
            "Diffractive layer",
            "optical-layer",
            "Modulate the transmitted field",
            ports=[port("in", "in", ["optical"], "front"), port("out", "out", ["optical"], "back")],
            opacity="transparent",
            capabilities=["filter", "diffract"],
            medium_behavior={"optical": "transmit"},
        ),
        component("detector", "Detector", "detector", "Terminate and sense the optical field", ports=[port("in", "in", ["optical"], "active-face")]),
    ]
    connections = [
        connection("source-layer", "optical", ("source", "out"), ("diffractive-layer", "in"), style="ray"),
        connection("layer-detector", "optical", ("diffractive-layer", "out"), ("detector", "in"), style="ray"),
    ]
    views = [
        view("physical-stack", "physical-setup", "physical", "system", "single", [item["id"] for item in components]),
        view("network-analogy", "architecture", "logical", "system", "single", [item["id"] for item in components]),
    ]
    return finish(case, components, connections, views=views)


def chip_hierarchy(case: dict[str, Any]) -> dict[str, Any]:
    data = ["electrical-data"]
    components = [
        component("driver", "Input driver", "interface", "Drive the chip", ports=[port("out", "out", data, "right")]),
        component("chip", "Integrated chip", "chip", "Contain the computational assembly", ports=None, scale="device"),
        component(
            "core",
            "Compute core",
            "compute-core",
            "Execute the local operation",
            ports=[port("in", "in", data, "left"), port("out", "out", data, "right")],
            scale="component",
            parent="chip",
            relation="integrated",
        ),
        component(
            "memory-cell",
            "Representative memory cell",
            "memory-cell",
            "Show device-level storage",
            ports=None,
            scale="microstructure",
            parent="core",
            relation="integrated",
        ),
        component("readout", "Readout", "interface", "Receive processed data", ports=[port("in", "in", data, "left")]),
    ]
    connections = [
        connection("driver-core", data[0], ("driver", "out"), ("core", "in"), style="guided"),
        connection("core-readout", data[0], ("core", "out"), ("readout", "in"), style="guided"),
    ]
    ids = [item["id"] for item in components]
    views = [
        view("chip-system", "physical-setup", "physical", "system", "single", ids),
        view("cell-detail", "cross-section", "physical", "microstructure", "single", ["chip", "core", "memory-cell"], parent="chip-system"),
    ]
    return finish(case, components, connections, views=views)


def logical_compute(case: dict[str, Any]) -> dict[str, Any]:
    medium = "tensor-data"
    components = [
        component("input", "Input tensor", "data-source", "Provide digital input", ports=[port("out", "out", [medium], "logical")], opacity="not-applicable"),
        component(
            "compute-core",
            "Compute-in-memory core",
            "compute-core",
            "Transform the input",
            ports=[port("in", "in", [medium], "logical"), port("out", "out", [medium], "logical")],
        ),
        component("output", "Output tensor", "data-sink", "Receive digital output", ports=[port("in", "in", [medium], "logical")], opacity="not-applicable"),
    ]
    connections = [
        connection("input-core", medium, ("input", "out"), ("compute-core", "in"), representation="logical", style="abstract"),
        connection("core-output", medium, ("compute-core", "out"), ("output", "in"), representation="logical", style="abstract"),
    ]
    views = [view("dataflow", "architecture", "logical", "system", "single", [item["id"] for item in components])]
    return finish(case, components, connections, views=views)


def wearable_contact(case: dict[str, Any]) -> dict[str, Any]:
    contact_medium = "body-contact"
    signal = "electrical-data"
    components = [
        component(
            "patch",
            "Wearable patch",
            "wearable-device",
            "Acquire sensor signals at the skin",
            ports=[port("contact", "out", [contact_medium], "bottom"), port("signal", "out", [signal], "edge")],
            mobility="wearable",
            body_interface=True,
        ),
        component(
            "transducer-layer",
            "Transducer layer",
            "active-layer",
            "Show the multilayer active assembly",
            ports=None,
            scale="microstructure",
            mobility="deformable",
            parent="patch",
            relation="laminated",
            states=["relaxed", "stretched"],
        ),
        component("skin", "Skin", "anatomy", "Provide the anatomical contact surface", ports=[port("surface", "in", [contact_medium], "outer-surface")], scale="anatomical", opacity="mixed"),
        component("workstation", "Acquisition electronics", "electronics", "Receive measured signals", ports=[port("signal", "in", [signal], "front")]),
    ]
    connections = [
        connection("patch-skin", contact_medium, ("patch", "contact"), ("skin", "surface"), representation="contact", style="contact", interface_class="anatomical"),
        connection("patch-workstation", signal, ("patch", "signal"), ("workstation", "signal"), style="flexible"),
    ]
    views = [
        view("wearing-context", "physical-setup", "physical", "system", "single", ["patch", "skin", "workstation"]),
        view("patch-exploded", "component-sheet", "physical", "device", "exploded", ["patch", "transducer-layer"]),
    ]
    return finish(case, components, connections, views=views)


def wireless_wearable(case: dict[str, Any]) -> dict[str, Any]:
    body = "body-contact"
    field = "rf-field"
    components = [
        component(
            "patch",
            "Wireless wearable patch",
            "wearable-device",
            "Sense and transmit physiological data",
            ports=[port("contact", "out", [body], "bottom"), port("radio", "out", [field], "antenna")],
            mobility="wearable",
            body_interface=True,
        ),
        component("skin", "Skin", "anatomy", "Provide skin coupling", ports=[port("surface", "in", [body], "outer-surface")], scale="anatomical", opacity="mixed"),
        component("receiver", "Wireless receiver", "electronics", "Receive the transmitted data", ports=[port("radio", "in", [field], "antenna")]),
    ]
    connections = [
        connection("patch-skin", body, ("patch", "contact"), ("skin", "surface"), representation="contact", style="contact", interface_class="anatomical"),
        connection("patch-receiver", field, ("patch", "radio"), ("receiver", "radio"), representation="field", style="field"),
    ]
    return finish(case, components, connections)


def wireless_implant(case: dict[str, Any]) -> dict[str, Any]:
    field = "magnetic-field"
    contact_medium = "implant-contact"
    components = [
        component("transmitter", "External transmitter", "field-source", "Generate wireless power and data", ports=[port("field", "out", [field], "coil")], capabilities=["source", "couple"]),
        component(
            "implant",
            "Implant module",
            "implant",
            "Receive the field and stimulate tissue",
            ports=[port("field", "in", [field], "receiver"), port("contact", "out", [contact_medium], "electrode")],
            scale="component",
            mobility="implantable",
            body_interface=True,
        ),
        component(
            "tissue",
            "Tissue context",
            "anatomy",
            "Transmit the field and host the implant",
            ports=[port("contact", "in", [contact_medium], "target")],
            scale="anatomical",
            opacity="mixed",
            medium_behavior={field: "transmit"},
        ),
    ]
    connections = [
        connection("wireless-power", field, ("transmitter", "field"), ("implant", "field"), representation="field", style="field", passes=["tissue"]),
        connection("implant-tissue", contact_medium, ("implant", "contact"), ("tissue", "contact"), representation="contact", style="contact", interface_class="anatomical"),
    ]
    ids = [item["id"] for item in components]
    views = [
        view("implant-context", "physical-setup", "physical", "system", "single", ids),
        view("implant-detail", "detail", "physical", "component", "single", ["implant", "tissue"], parent="implant-context"),
    ]
    return finish(case, components, connections, views=views)


def mobile_robot(case: dict[str, Any]) -> dict[str, Any]:
    control = "control-data"
    material = "sample-or-build-material"
    components = [
        component("controller", "Controller", "control-system", "Issue task commands", ports=[port("out", "out", [control], "logical")]),
        component(
            "robot",
            "Mobile robot",
            "robot",
            "Move a tool or sample through the workspace",
            ports=[port("control", "in", [control], "logical"), port("tool", "out", [material], "end-effector")],
            scale="system",
            mobility="mobile",
            capabilities=["route", "guide"],
        ),
        component("workpiece", "Workpiece or station", "workstation", "Receive deposited material or transferred sample", ports=[port("in", "in", [material], "interaction-zone")], scale="system"),
        component("workspace-envelope", "Motion envelope", "motion-envelope", "Bound reachable collision-free motion", ports=None, scale="system", mobility="not-applicable", opacity="translucent"),
    ]
    connections = [
        connection("controller-robot", control, ("controller", "out"), ("robot", "control"), representation="logical", style="abstract"),
        connection("robot-workpiece", material, ("robot", "tool"), ("workpiece", "in"), style="flow"),
    ]
    motion_type = "flight" if "aerial" in case["domain_family"] else "translation"
    motions = [
        {
            "id": "robot-workspace",
            "component": "robot",
            "type": motion_type,
            "degrees_of_freedom": ["translate-x", "translate-y", "translate-z"],
            "envelope_component": "workspace-envelope",
            "evidence": ["S1"],
        }
    ]
    return finish(case, components, connections, motions=motions)


def lab_sequence(case: dict[str, Any]) -> dict[str, Any]:
    control = "control-data"
    components = [
        component("scheduler", "Experiment scheduler", "control-system", "Submit and update recipes", ports=[port("out", "out", [control], "logical")]),
        component(
            "transfer-robot",
            "Transfer robot",
            "robot",
            "Move samples among stations",
            ports=[port("control", "in", [control], "logical")],
            scale="system",
            mobility="articulated",
            states=["dose-transfer", "furnace-transfer", "xrd-transfer"],
        ),
        component("dosing", "Powder dosing", "workstation", "Prepare precursor powders", ports=None, scale="system"),
        component("furnace", "Heating station", "workstation", "Heat samples", ports=None, scale="system"),
        component("xrd", "XRD station", "workstation", "Characterize products", ports=None, scale="system"),
        component("robot-envelope", "Robot reach envelope", "motion-envelope", "Bound the reachable workspace", ports=None, scale="system", mobility="not-applicable", opacity="translucent"),
    ]
    connections = [connection("scheduler-robot", control, ("scheduler", "out"), ("transfer-robot", "control"), representation="logical", style="abstract")]
    sequence = {
        "id": "sample-process",
        "mode": "sequential",
        "steps": [
            {"component": "transfer-robot", "state": "dose-transfer"},
            {"component": "transfer-robot", "state": "furnace-transfer"},
            {"component": "transfer-robot", "state": "xrd-transfer"},
        ],
        "reused_components": ["transfer-robot"],
        "evidence": ["S1"],
    }
    motion = {
        "id": "transfer-workspace",
        "component": "transfer-robot",
        "type": "articulation",
        "degrees_of_freedom": ["joint-1", "joint-2", "joint-3"],
        "envelope_component": "robot-envelope",
        "evidence": ["S1"],
    }
    views = [
        view("laboratory-layout", "physical-setup", "physical", "system", "single", [item["id"] for item in components]),
        view("process-loop", "mechanism", "mechanism", "system", "sequence", ["scheduler", "transfer-robot", "dosing", "furnace", "xrd"]),
    ]
    return finish(case, components, connections, views=views, sequences=[sequence], motions=[motion])


def thermal_fluid_cycle(case: dict[str, Any]) -> dict[str, Any]:
    air = "air"
    heat = "heat"
    water = "water"
    components = [
        component("ambient-inlet", "Ambient air inlet", "environment-boundary", "Supply external air", ports=[port("out", "out", [air], "boundary")], scale="environment", opacity="not-applicable"),
        component("fan", "Intake fan", "flow-driver", "Drive external air through the device", ports=[port("in", "in", [air], "inlet"), port("out", "out", [air], "outlet")], capabilities=["fan"]),
        component(
            "capture-bed",
            "Regenerative capture bed",
            "process-bed",
            "Adsorb and desorb water",
            ports=[port("air-in", "in", [air], "inlet"), port("air-out", "out", [air], "outlet"), port("heat", "in", [heat], "thermal-interface")],
            states=["adsorption", "desorption"],
            medium_behavior={air: "contain"},
        ),
        component("condenser", "Condenser", "heat-exchanger", "Condense water from humid air", ports=[port("in", "in", [air], "inlet"), port("air-out", "out", [air], "outlet"), port("water", "out", [water], "funnel")], capabilities=["convert"]),
        component("heater", "Heater", "thermal-source", "Heat the capture bed during regeneration", ports=[port("heat", "out", [heat], "contact-face")], states=["off", "on"]),
        component("air-outlet", "Atmospheric outlet", "environment-boundary", "Release processed air", ports=[port("in", "in", [air], "boundary")], scale="environment", opacity="not-applicable"),
        component("collector", "Water collector", "reservoir", "Collect condensed liquid water", ports=[port("in", "in", [water], "top")], capabilities=["contain", "gravity-feed"]),
    ]
    connections = [
        connection("ambient-fan", air, ("ambient-inlet", "out"), ("fan", "in"), style="flow"),
        connection("fan-bed", air, ("fan", "out"), ("capture-bed", "air-in"), style="flow"),
        connection("bed-condenser", air, ("capture-bed", "air-out"), ("condenser", "in"), style="flow"),
        connection("condenser-outlet", air, ("condenser", "air-out"), ("air-outlet", "in"), style="flow"),
        connection("condensed-water", water, ("condenser", "water"), ("collector", "in"), style="flow"),
        connection("heater-bed", heat, ("heater", "heat"), ("capture-bed", "heat"), representation="contact", style="contact", interface_class="thermal"),
    ]
    sequence = {
        "id": "water-harvesting-cycle",
        "mode": "cyclic",
        "steps": [
            {"component": "capture-bed", "state": "adsorption"},
            {"component": "capture-bed", "state": "desorption"},
        ],
        "reused_components": ["capture-bed"],
        "evidence": ["S1"],
    }
    route = {
        "id": "open-air-route",
        "medium": air,
        "connections": ["ambient-fan", "fan-bed", "bed-condenser", "condenser-outlet"],
        "open": True,
        "source_boundary": "ambient-inlet",
        "sink_boundary": "air-outlet",
        "driver_component": "fan",
        "evidence": ["S1"],
    }
    return finish(case, components, connections, sequences=[sequence], routes=[route])


def deformable_sensor(case: dict[str, Any]) -> dict[str, Any]:
    signal = "electrical-data"
    components = [
        component("soft-body", "Soft robot body", "soft-structure", "Deform during operation", ports=None, scale="system", mobility="deformable", states=["neutral", "bent"]),
        component(
            "sensor-skin",
            "Stretchable sensor skin",
            "sensor-skin",
            "Measure distributed strain",
            ports=[port("signal", "out", [signal], "flex-tail")],
            scale="component",
            mobility="deformable",
            parent="soft-body",
            relation="laminated",
            states=["relaxed", "stretched"],
        ),
        component("processor", "Reconstruction processor", "compute-system", "Reconstruct body morphology", ports=[port("signal", "in", [signal], "input")]),
        component("deformation-envelope", "Deformation envelope", "motion-envelope", "Bound the shown deformations", ports=None, scale="system", mobility="not-applicable", opacity="translucent"),
    ]
    connections = [connection("skin-processor", signal, ("sensor-skin", "signal"), ("processor", "signal"), style="flexible")]
    motions = [
        {
            "id": "body-deformation",
            "component": "soft-body",
            "type": "deformation",
            "degrees_of_freedom": ["distributed-curvature"],
            "envelope_component": "deformation-envelope",
            "evidence": ["S1"],
        }
    ]
    return finish(case, components, connections, motions=motions)


def metamaterial_motion(case: dict[str, Any]) -> dict[str, Any]:
    load = "mechanical-load"
    components = [
        component("actuator", "Input actuator", "actuator", "Apply a dynamic input", ports=[port("load", "out", [load], "contact")], capabilities=["source"]),
        component(
            "metamaterial",
            "Reprogrammable metamaterial",
            "mechanical-lattice",
            "Transform and route mechanical energy",
            ports=[port("load", "in", [load], "input-edge")],
            scale="system",
            mobility="deformable",
            states=["focus", "split", "protect"],
        ),
        component("motion-envelope", "Dynamic envelope", "motion-envelope", "Bound the physical deformation", ports=None, scale="system", mobility="not-applicable", opacity="translucent"),
    ]
    connections = [connection("actuator-lattice", load, ("actuator", "load"), ("metamaterial", "load"), representation="contact", style="contact", timing="pulsed", interface_class="mechanical")]
    motion = {
        "id": "lattice-deformation",
        "component": "metamaterial",
        "type": "deformation",
        "degrees_of_freedom": ["distributed-nonlinear-displacement"],
        "envelope_component": "motion-envelope",
        "evidence": ["S1"],
    }
    return finish(case, components, connections, motions=[motion])


def microfluidic_loop(case: dict[str, Any]) -> dict[str, Any]:
    fluid = "sample-fluid"
    components = [
        component("pump", "Syringe pump", "flow-driver", "Drive controlled perfusion", ports=[port("out", "out", [fluid], "outlet"), port("in", "in", [fluid], "return")], capabilities=["pump", "circulate"]),
        component(
            "chip",
            "Microfluidic chip",
            "microfluidic-device",
            "Trap and perfuse a test construct",
            ports=[port("in", "in", [fluid], "inlet"), port("out", "out", [fluid], "outlet")],
            states=["loading", "perfusion"],
            medium_behavior={fluid: "contain"},
        ),
        component(
            "channel",
            "Serpentine channel and trap",
            "microchannel",
            "Show the internal flow path",
            ports=None,
            scale="microstructure",
            parent="chip",
            relation="contained",
            medium_behavior={fluid: "contain"},
        ),
        component("reservoir", "Medium reservoir", "reservoir", "Collect and recirculate medium", ports=[port("in", "in", [fluid], "inlet"), port("out", "out", [fluid], "outlet")], capabilities=["contain"]),
    ]
    connections = [
        connection("pump-chip", fluid, ("pump", "out"), ("chip", "in"), style="flow"),
        connection("chip-reservoir", fluid, ("chip", "out"), ("reservoir", "in"), style="flow"),
        connection("reservoir-pump", fluid, ("reservoir", "out"), ("pump", "in"), style="flow"),
    ]
    sequence = {
        "id": "chip-loading",
        "mode": "sequential",
        "steps": [{"component": "chip", "state": "loading"}, {"component": "chip", "state": "perfusion"}],
        "reused_components": ["chip"],
        "evidence": ["S1"],
    }
    loop = {
        "id": "perfusion-loop",
        "medium": fluid,
        "connections": ["pump-chip", "chip-reservoir", "reservoir-pump"],
        "closed": True,
        "driver_component": "pump",
        "evidence": ["S1"],
    }
    views = [
        view("perfusion-system", "physical-setup", "physical", "system", "single", [item["id"] for item in components]),
        view("channel-section", "cross-section", "physical", "microstructure", "single", ["chip", "channel"], parent="perfusion-system"),
    ]
    return finish(case, components, connections, views=views, sequences=[sequence], loops=[loop])


def closed_loop_implant(case: dict[str, Any]) -> dict[str, Any]:
    field = "rf-field"
    contact_medium = "body-contact"
    components = [
        component(
            "controller",
            "Skin-interfaced controller",
            "wearable-controller",
            "Sense, decide, and transmit therapy commands",
            ports=[
                port("skin", "out", [contact_medium], "bottom"),
                port("command", "out", [field], "antenna"),
                port("feedback", "in", [field], "antenna"),
            ],
            mobility="wearable",
            body_interface=True,
        ),
        component("skin", "Skin", "anatomy", "Support the external controller", ports=[port("contact", "in", [contact_medium], "surface")], scale="anatomical", opacity="mixed"),
        component(
            "implant",
            "Therapeutic implant",
            "implant",
            "Receive commands and stimulate target tissue",
            ports=[
                port("command", "in", [field], "receiver"),
                port("feedback", "out", [field], "transmitter"),
                port("target", "out", [contact_medium], "electrode"),
            ],
            scale="component",
            mobility="implantable",
            body_interface=True,
        ),
        component("target-tissue", "Target tissue", "anatomy", "Receive therapeutic stimulation", ports=[port("contact", "in", [contact_medium], "surface")], scale="anatomical", opacity="mixed"),
        component("tissue", "Tissue path", "anatomy", "Transmit the wireless field", ports=None, scale="anatomical", opacity="mixed", medium_behavior={field: "transmit"}),
    ]
    connections = [
        connection("controller-skin", contact_medium, ("controller", "skin"), ("skin", "contact"), representation="contact", style="contact", interface_class="anatomical"),
        connection("therapy-command", field, ("controller", "command"), ("implant", "command"), representation="field", style="field", passes=["tissue"]),
        connection("therapy-feedback", field, ("implant", "feedback"), ("controller", "feedback"), representation="field", style="field", passes=["tissue"]),
        connection("implant-target", contact_medium, ("implant", "target"), ("target-tissue", "contact"), representation="contact", style="contact", interface_class="anatomical"),
    ]
    loop = {
        "id": "therapy-control-loop",
        "medium": field,
        "connections": ["therapy-command", "therapy-feedback"],
        "closed": True,
        "evidence": ["S1"],
    }
    return finish(case, components, connections, loops=[loop])


BUILDERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "optical_stack": optical_stack,
    "chip_hierarchy": chip_hierarchy,
    "logical_compute": logical_compute,
    "wearable_contact": wearable_contact,
    "wireless_wearable": wireless_wearable,
    "wireless_implant": wireless_implant,
    "mobile_robot": mobile_robot,
    "lab_sequence": lab_sequence,
    "thermal_fluid_cycle": thermal_fluid_cycle,
    "deformable_sensor": deformable_sensor,
    "metamaterial_motion": metamaterial_motion,
    "microfluidic_loop": microfluidic_loop,
    "closed_loop_implant": closed_loop_implant,
}

REGRESSION_TESTS = [
    {"case_id": "integrated-chip-hierarchy", "kind": "coarse_child_scale", "expected_codes": ["H004"]},
    {"case_id": "automated-lab-sequence", "kind": "false_hardware_reuse", "expected_codes": ["S010"]},
    {"case_id": "open-thermal-fluid-route", "kind": "external_route_driver", "expected_codes": ["F012"]},
    {"case_id": "optical-transmission-stack", "kind": "missing_component_existence_evidence", "expected_codes": ["C023"]},
    {"case_id": "optical-transmission-stack", "kind": "missing_port_identity_evidence", "expected_codes": ["P008"]},
    {"case_id": "optical-transmission-stack", "kind": "silently_unconnected_port", "expected_codes": ["T003"]},
    {"case_id": "optical-transmission-stack", "kind": "unsupported_open_port", "expected_codes": ["T005", "T006"]},
    {"case_id": "optical-transmission-stack", "kind": "open_port_still_used", "expected_codes": ["T004"]},
]


def mutate(manifest: dict[str, Any], kind: str) -> None:
    if kind == "opaque_pass_through":
        manifest["connections"][0]["path"]["passes_through"] = ["detector"]
    elif kind == "orphan_microstructure":
        target = next(item for item in manifest["components"] if item.get("scale_level") == "microstructure")
        target.pop("parent", None)
    elif kind == "logical_as_physical":
        target = next(item for item in manifest["connections"] if item.get("representation") == "logical")
        target["path"]["style"] = "guided"
    elif kind == "missing_body_contact":
        manifest["connections"] = [item for item in manifest["connections"] if item.get("representation") != "contact"]
    elif kind == "wrong_contact_class":
        target = next(item for item in manifest["connections"] if item.get("representation") == "contact")
        target["interface_class"] = "thermal"
    elif kind == "field_as_cable":
        target = next(item for item in manifest["connections"] if item.get("representation") == "field")
        target["path"]["style"] = "guided"
    elif kind == "missing_motion_envelope":
        manifest["motions"][0]["envelope_component"] = None
    elif kind == "invalid_sequence_state":
        manifest["sequences"][0]["steps"][0]["state"] = "nonexistent-state"
    elif kind == "broken_loop":
        manifest["loops"][0]["connections"] = manifest["loops"][0]["connections"][:-1]
    elif kind == "missing_flow_driver":
        manifest["routes"][0]["driver_component"] = None
    elif kind == "missing_deformation_state":
        target = next(item for item in manifest["components"] if item["id"] == "sensor-skin")
        target["states"] = []
    elif kind == "coarse_child_scale":
        target = next(item for item in manifest["components"] if item.get("scale_level") == "microstructure")
        target["scale_level"] = "device"
    elif kind == "false_hardware_reuse":
        manifest["sequences"][0]["reused_components"] = ["scheduler"]
    elif kind == "external_route_driver":
        manifest["routes"][0]["driver_component"] = "collector"
    elif kind == "missing_component_existence_evidence":
        manifest["components"][0].pop("existence_evidence", None)
    elif kind == "missing_port_identity_evidence":
        manifest["components"][0]["ports"][0].pop("evidence", None)
    elif kind == "silently_unconnected_port":
        manifest["connections"] = manifest["connections"][1:]
    elif kind == "unsupported_open_port":
        target = manifest["components"][0]["ports"][0]
        target["connection_expectation"] = "intentionally-open"
        target.pop("status_reason", None)
        target.pop("status_evidence", None)
        manifest["connections"] = manifest["connections"][1:]
    elif kind == "open_port_still_used":
        target = manifest["components"][0]["ports"][0]
        target["connection_expectation"] = "intentionally-open"
        target["status_reason"] = "Synthetic contradiction"
        target["status_evidence"] = ["S1"]
    else:
        raise ValueError(f"unknown mutation kind: {kind}")


def validate_corpus(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cases = data.get("cases", [])
    if len(cases) < int(data.get("minimum_cases", 10)):
        errors.append(f"case count {len(cases)} is below the configured minimum")
    domains = {case.get("discipline_group") for case in cases}
    if len(domains) < int(data.get("minimum_domain_families", 7)):
        errors.append(f"domain-family count {len(domains)} is below the configured minimum")
    ids = [case.get("id") for case in cases]
    if len(set(ids)) != len(ids):
        errors.append("duplicate case ID in benchmark")
    required = {
        "id",
        "title",
        "domain_family",
        "discipline_group",
        "scenario",
        "archetype",
        "required_features",
        "negative_test",
    }
    for index, case in enumerate(cases):
        missing = sorted(required - set(case))
        if missing:
            errors.append(f"case[{index}] missing fields: {', '.join(missing)}")
        if case.get("archetype") not in BUILDERS:
            errors.append(f"case[{index}] uses unknown archetype {case.get('archetype')!r}")
        if not case.get("required_features"):
            errors.append(f"case[{index}] has no required feature")
    return errors


def write_markdown(
    path: Path,
    data: dict[str, Any],
    results: list[dict[str, Any]],
    regression_results: list[dict[str, Any]],
    corpus_errors: list[str],
) -> None:
    domains = sorted({case["discipline_group"] for case in data["cases"]})
    lines = [
        "# Synthetic Cross-Domain Benchmark Result",
        "",
        f"- Synthetic cases: `{len(data['cases'])}`",
        f"- Domain families: `{len(domains)}`",
        f"- Positive fixtures passed: `{sum(item['positive_pass'] for item in results)}/{len(results)}`",
        f"- Negative mutations detected: `{sum(item['negative_pass'] for item in results)}/{len(results)}`",
        f"- Additional regressions detected: `{sum(item['pass'] for item in regression_results)}/{len(regression_results)}`",
        f"- Corpus result: `{'FAIL' if corpus_errors else 'PASS'}`",
        "",
        "## Domain Coverage",
        "",
        ", ".join(f"`{domain}`" for domain in domains),
        "",
        "## Cases",
        "",
        "| Case | Domain | Positive | Mutation | Detected codes |",
        "|---|---|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result['id']} | {result['domain']} | "
            f"{'PASS' if result['positive_pass'] else 'FAIL'} | {'PASS' if result['negative_pass'] else 'FAIL'} | "
            f"{', '.join(result['negative_codes']) or '-'} |"
        )
    if corpus_errors:
        lines.extend(["", "## Corpus Errors", ""] + [f"- {message}" for message in corpus_errors])
    lines.extend(["", "## Additional Regressions", "", "| Source case | Mutation | Expected | Detected | Result |", "|---|---|---|---|---:|"])
    for result in regression_results:
        lines.append(
            f"| {result['case_id']} | {result['kind']} | {', '.join(result['expected_codes'])} | "
            f"{', '.join(result['detected_codes']) or '-'} | {'PASS' if result['pass'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A pass means the original synthetic truth model is accepted and its deliberately injected failure is detected. These fixtures test validation logic; they do not replace visual review of a completed render.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.benchmark.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read benchmark: {exc}", file=sys.stderr)
        return 2
    corpus_errors = validate_corpus(data)
    validator = load_validator()
    results: list[dict[str, Any]] = []
    for case in data.get("cases", []):
        manifest = BUILDERS[case["archetype"]](case)
        positive_findings = validator.validate(manifest)
        positive_pass = not positive_findings

        mutated = copy.deepcopy(manifest)
        mutation = case["negative_test"]
        mutate(mutated, mutation["kind"])
        negative_findings = validator.validate(mutated)
        negative_codes = sorted({item.code for item in negative_findings})
        expected = set(mutation["expected_codes"])
        negative_pass = expected.issubset(negative_codes)
        results.append(
            {
                "id": case["id"],
                "domain": case["domain_family"],
                "discipline_group": case["discipline_group"],
                "positive_pass": positive_pass,
                "positive_findings": [item.__dict__ for item in positive_findings],
                "mutation": mutation["kind"],
                "expected_codes": sorted(expected),
                "negative_codes": negative_codes,
                "negative_pass": negative_pass,
            }
        )
        status = "PASS" if positive_pass and negative_pass else "FAIL"
        print(f"{status} {case['id']}: positive={len(positive_findings)} finding(s), mutation={','.join(negative_codes) or 'none'}")

    case_by_id = {case["id"]: case for case in data.get("cases", [])}
    regression_results: list[dict[str, Any]] = []
    for test in REGRESSION_TESTS:
        case = case_by_id[test["case_id"]]
        manifest = BUILDERS[case["archetype"]](case)
        mutate(manifest, test["kind"])
        findings = validator.validate(manifest)
        codes = sorted({item.code for item in findings})
        passed = set(test["expected_codes"]).issubset(codes)
        regression_results.append(
            {
                "case_id": test["case_id"],
                "kind": test["kind"],
                "expected_codes": test["expected_codes"],
                "detected_codes": codes,
                "pass": passed,
            }
        )
        print(f"{'PASS' if passed else 'FAIL'} regression {test['kind']}: {','.join(codes) or 'none'}")

    if args.report:
        write_markdown(args.report, data, results, regression_results, corpus_errors)
        print(f"report: {args.report}")
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "benchmark": str(args.benchmark),
            "case_count": len(data.get("cases", [])),
            "domain_count": len({case.get("discipline_group") for case in data.get("cases", [])}),
            "corpus_errors": corpus_errors,
            "summary": dict(Counter("pass" if item["positive_pass"] and item["negative_pass"] else "fail" for item in results)),
            "results": results,
            "regression_results": regression_results,
        }
        args.json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"json: {args.json_path}")

    failed = (
        bool(corpus_errors)
        or any(not item["positive_pass"] or not item["negative_pass"] for item in results)
        or any(not item["pass"] for item in regression_results)
    )
    print(
        f"summary: cases={len(results)}, domains={len({item['discipline_group'] for item in results})}, "
        f"positive_pass={sum(item['positive_pass'] for item in results)}, "
        f"negative_pass={sum(item['negative_pass'] for item in results)}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
