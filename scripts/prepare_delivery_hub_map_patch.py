#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_COMPILER_PATH = ROOT / "scripts" / "compile_rc_map.py"
SLOT_DISCOVERY_PATH = ROOT / "scripts" / "discover_delivery_hub_map_slot.py"
DELIVERY_HUB_SPEC = ROOT / "content" / "cagliari_preview" / "map_specs" / "RC_DELIVERY_HUB.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_plan(rom_data: bytes) -> dict:
    compiler = load_module(MAP_COMPILER_PATH, "rc_map_compiler")
    discovery = load_module(SLOT_DISCOVERY_PATH, "delivery_hub_slot_discovery")

    map_spec = compiler.load_json(DELIVERY_HUB_SPEC)
    ir = compiler.compile_spec(map_spec)
    slot = discovery.analyze_rom(rom_data)

    if not slot["safe_to_repoint"]:
        raise ValueError(
            "Delivery Hub map slot is not uniquely safe to repoint: "
            f"{slot['candidate_count']} candidate(s)."
        )

    header = slot["candidates"][0]
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
        },
        "new_map": {
            "dimensions": ir["dimensions"],
            "anchors": ir["anchors"],
            "objects": ir["objects"],
            "interactions": ir["interactions"],
            "warps": ir["warps"],
            "tileset_contract": ir["tileset_contract"],
        },
        "mutation_allowed": False,
        "required_before_mutation": [
            "resolve RC_TILESET_CAGLIARI_INTERIORS_01 primary/secondary tileset pointers",
            "resolve metatile ids for every semantic Delivery Hub role",
            "allocate aligned free space for layout, map data, MapEvents and event scripts",
            "compile starter and rival event scripts to exact FireRed bytecode",
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
