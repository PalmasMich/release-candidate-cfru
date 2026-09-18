#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_COMPILER_PATH = ROOT / "scripts" / "compile_rc_map.py"
SLOT_DISCOVERY_PATH = ROOT / "scripts" / "discover_delivery_hub_map_slot.py"
EVENT_COMPILER_PATH = ROOT / "scripts" / "compile_rc_event_scripts.py"
DIALOGUE_COMPILER_PATH = ROOT / "scripts" / "compile_rc_dialogue.py"
MAP_EVENTS_COMPILER_PATH = ROOT / "scripts" / "compile_rc_map_events.py"
DELIVERY_HUB_SPEC = ROOT / "content" / "cagliari_preview" / "map_specs" / "RC_DELIVERY_HUB.json"
DELIVERY_HUB_SCRIPT_SPEC = ROOT / "content" / "cagliari_preview" / "script_specs" / "RC_DELIVERY_HUB.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_plan(rom_data: bytes) -> dict:
    compiler = load_module(MAP_COMPILER_PATH, "rc_map_compiler")
    discovery = load_module(SLOT_DISCOVERY_PATH, "delivery_hub_slot_discovery")
    event_compiler = load_module(EVENT_COMPILER_PATH, "rc_event_compiler")
    dialogue_compiler = load_module(DIALOGUE_COMPILER_PATH, "rc_dialogue_compiler")
    map_events_compiler = load_module(MAP_EVENTS_COMPILER_PATH, "rc_map_events_compiler")

    map_spec = compiler.load_json(DELIVERY_HUB_SPEC)
    ir = compiler.compile_spec(map_spec)
    event_ir = event_compiler.compile_file(DELIVERY_HUB_SCRIPT_SPEC)
    dialogue_ir = dialogue_compiler.compile_file()
    map_events_ir = map_events_compiler.compile_file(DELIVERY_HUB_SPEC)
    slot = discovery.analyze_rom(rom_data)

    if not slot["safe_to_repoint"]:
        raise ValueError(
            "Delivery Hub map slot is not uniquely safe to repoint: "
            f"{slot['candidate_count']} candidate(s)."
        )

    header = slot["candidates"][0]

    compiled_script_ids = {script["id"] for script in event_ir["scripts"]}
    bound_script_ids = {
        item["script"]
        for item in ir["objects"] + ir["interactions"]
    }
    missing_scripts = sorted(bound_script_ids - compiled_script_ids)
    if missing_scripts:
        raise ValueError(f"Delivery Hub map references uncompiled scripts: {missing_scripts}")

    dialogue_by_id = {scene["id"]: scene for scene in dialogue_ir["scenes"]}
    referenced_dialogues = sorted({
        relocation["symbol"]
        for script in event_ir["scripts"]
        for relocation in script["relocations"]
        if relocation["kind"] == "dialogue"
    })
    missing_dialogues = [dialogue_id for dialogue_id in referenced_dialogues if dialogue_id not in dialogue_by_id]
    if missing_dialogues:
        raise ValueError(f"Delivery Hub scripts reference missing dialogue: {missing_dialogues}")

    map_cell_bytes = ir["dimensions"]["width"] * ir["dimensions"]["height"] * 2
    script_bytes = sum(script["size"] for script in event_ir["scripts"])
    dialogue_bytes = sum(dialogue_by_id[dialogue_id]["size"] for dialogue_id in referenced_dialogues)
    map_events_bytes = map_events_ir["total_bytes"]

    return {
        "format": "RC_MAP_PATCH_PLAN_V1",
        "map_id": ir["id"],
        "source_sha256": ir["source_sha256"],
        "slot": {
            "vanilla_map": slot["slot"],
            "map_group": slot["map_group"],
            "map_num": slot["map_num"],
            "map_header_offset": header["offset"],
            "original_layout_ptr": header["layout_ptr"],
            "original_events_ptr": header["events_ptr"],
            "original_scripts_ptr": header["scripts_ptr"],
            "original_connections_ptr": header["connections_ptr"],
            "original_layout": header["layout"],
        },
        "new_map": {
            "dimensions": ir["dimensions"],
            "anchors": ir["anchors"],
            "objects": ir["objects"],
            "interactions": ir["interactions"],
            "warps": ir["warps"],
            "tileset_contract": ir["tileset_contract"],
        },
        "compiled_content": {
            "event_script_format": event_ir["format"],
            "event_script_count": len(event_ir["scripts"]),
            "bound_script_ids": sorted(bound_script_ids),
            "event_script_bytes": script_bytes,
            "event_relocation_count": sum(len(script["relocations"]) for script in event_ir["scripts"]),
            "dialogue_format": dialogue_ir["format"],
            "referenced_dialogues": referenced_dialogues,
            "dialogue_bytes": dialogue_bytes,
            "map_cell_bytes": map_cell_bytes,
            "map_events_format": map_events_ir["format"],
            "map_events_bytes": map_events_bytes,
            "map_event_relocation_count": (
                len(map_events_ir["map_events_header"]["relocations"])
                + len(map_events_ir["object_events"]["relocations"])
                + len(map_events_ir["warp_events"]["relocations"])
                + len(map_events_ir["bg_events"]["relocations"])
            ),
            "minimum_payload_bytes": map_cell_bytes + map_events_bytes + script_bytes + dialogue_bytes,
        },
        "mutation_allowed": False,
        "required_before_mutation": [
            "resolve custom RC_TILESET_CAGLIARI_INTERIORS_01 asset insertion or explicitly approve temporary House2 bootstrap tilesets",
            "resolve metatile ids for every semantic Delivery Hub role against the selected tileset pair",
            "allocate aligned free space for MapLayout, map cells, MapEvents, scripts and dialogue blobs",
            "link compiled event-script relocations after final ROM addresses are allocated",
            "link compiled MapEvents/ObjectEventTemplate/BgEvent/WarpEvent relocations after final ROM addresses are allocated",
            "verify destination Marina map slot and warp target",
            "write all new data first, then repoint the unused MapHeader last",
        ],
        "rollback": {
            "strategy": "restore_original_map_header_pointers",
            "header_offset": header["offset"],
            "layout_ptr": header["layout_ptr"],
            "events_ptr": header["events_ptr"],
            "scripts_ptr": header["scripts_ptr"],
            "connections_ptr": header["connections_ptr"],
            "original_layout_ptr": header["layout_ptr"],
            "original_primary_tileset_ptr": header["layout"]["primary_tileset_ptr"],
            "original_secondary_tileset_ptr": header["layout"]["secondary_tileset_ptr"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare, but do not apply, the permanent Delivery Hub map repoint plan."
    )
    parser.add_argument("rom", type=Path)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    if not args.rom.is_file():
        print(f"ERROR: ROM not found: {args.rom}")
        return 1

    try:
        plan = build_plan(args.rom.read_bytes())
    except ValueError as exc:
        print(f"RC_DELIVERY_HUB_PLAN=BLOCKED: {exc}")
        return 2

    rendered = json.dumps(plan, indent=2)
    print(rendered)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")

    print("RC_DELIVERY_HUB_PLAN=READY")
    print("RC_DELIVERY_HUB_MUTATION_ALLOWED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
