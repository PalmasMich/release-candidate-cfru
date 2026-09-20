#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"

MAP_COMPILER_PATH = ROOT / "scripts" / "compile_rc_map.py"
CELL_COMPILER_PATH = ROOT / "scripts" / "compile_rc_map_cells.py"
EVENTS_COMPILER_PATH = ROOT / "scripts" / "compile_rc_map_events.py"
SCRIPT_COMPILER_PATH = ROOT / "scripts" / "compile_rc_event_scripts.py"
DIALOGUE_COMPILER_PATH = ROOT / "scripts" / "compile_rc_dialogue.py"
PAYLOAD_COMPILER_PATH = ROOT / "scripts" / "compile_rc_map_payload.py"
TILESET_VALIDATOR_PATH = ROOT / "scripts" / "validate_rc_tileset_pipeline.py"
CONTENT_VALIDATOR_PATH = ROOT / "scripts" / "validate_cagliari_content.py"

MAPS = (
    ("RC_DELIVERY_HUB", "RC_DELIVERY_HUB.json", "RC_DELIVERY_HUB.json"),
    ("RC_CAGLIARI_MARINA", "RC_CAGLIARI_MARINA.json", "RC_CAGLIARI_MARINA.json"),
    ("RC_PORT_CONNECTION", "RC_PORT_CONNECTION.json", "RC_PORT_CONNECTION.json"),
    ("RC_CASTELLO_ASCENT", "RC_CASTELLO_ASCENT.json", "RC_CASTELLO_ASCENT.json"),
    ("RC_DEPLOY_DISTRICT", "RC_DEPLOY_DISTRICT.json", "RC_DEPLOY_DISTRICT.json"),
    ("RC_DEPLOY_ROOM", "RC_DEPLOY_ROOM.json", "RC_DEPLOY_ROOM.json"),
)

DUMMY_PRIMARY_TILESET = 0x08100000
DUMMY_SECONDARY_TILESET = 0x08110000
DUMMY_BASE_START = 0x08900000
DUMMY_BASE_STEP = 0x00020000


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_warp_contracts(map_specs: dict[str, dict]) -> None:
    for source_id, source in map_specs.items():
        for warp in source.get("warps", []):
            target_id = warp["target_map"]
            if target_id not in map_specs:
                raise ValueError(f"{source_id}: warp {warp['id']} targets unknown map {target_id}")
            target_warps = map_specs[target_id].get("warps", [])
            target_index = int(warp["warp_id"])
            if not 0 <= target_index < len(target_warps):
                raise ValueError(
                    f"{source_id}: warp {warp['id']} target warp index {target_index} "
                    f"is invalid for {target_id} ({len(target_warps)} warp(s))"
                )
            actual_anchor = target_warps[target_index]["anchor"]
            declared_anchor = warp["target_anchor"]
            if actual_anchor != declared_anchor:
                raise ValueError(
                    f"{source_id}: warp {warp['id']} target anchor {declared_anchor} "
                    f"does not match {target_id} warp {target_index} anchor {actual_anchor}"
                )


def main() -> int:
    map_comp = load_module(MAP_COMPILER_PATH, "rc_map_preflight")
    cell_comp = load_module(CELL_COMPILER_PATH, "rc_cells_preflight")
    events_comp = load_module(EVENTS_COMPILER_PATH, "rc_events_preflight")
    script_comp = load_module(SCRIPT_COMPILER_PATH, "rc_scripts_preflight")
    dialogue_comp = load_module(DIALOGUE_COMPILER_PATH, "rc_dialogue_preflight")
    payload_comp = load_module(PAYLOAD_COMPILER_PATH, "rc_payload_preflight")
    tileset_validator = load_module(TILESET_VALIDATOR_PATH, "rc_tileset_preflight")
    content_validator = load_module(CONTENT_VALIDATOR_PATH, "rc_content_preflight")

    content_validator.validate()

    tileset_manifest = tileset_validator.load_manifest()
    tileset_errors = tileset_validator.validate(tileset_manifest)
    if tileset_errors:
        raise ValueError(f"invalid tileset art contract: {'; '.join(tileset_errors)}")
    tileset_status = tileset_validator.overall_status(tileset_manifest)

    slots = json.loads((CONTENT / "map_slots.json").read_text(encoding="utf-8"))["slots"]
    slot_by_id = {slot["rc_map"]: slot for slot in slots}
    if len(slot_by_id) != len(slots):
        raise ValueError("duplicate RC map slot ids")

    map_ids = events_comp.load_map_ids()
    dialogue_ir = dialogue_comp.compile_file()
    dialogue_ids = {scene["id"] for scene in dialogue_ir["scenes"]}

    map_specs = {
        map_id: json.loads((CONTENT / "map_specs" / map_name).read_text(encoding="utf-8"))
        for map_id, map_name, _ in MAPS
    }
    validate_warp_contracts(map_specs)

    compiled = []
    all_script_ids = set()
    script_irs = {}

    for index, (map_id, map_name, script_name) in enumerate(MAPS):
        map_path = CONTENT / "map_specs" / map_name
        script_path = CONTENT / "script_specs" / script_name

        if map_id not in slot_by_id:
            raise ValueError(f"{map_id}: missing reserved map slot")

        map_ir = map_comp.compile_file(map_path)
        if map_ir["id"] != map_id:
            raise ValueError(f"{map_id}: map spec id mismatch: {map_ir['id']}")

        cell_ir = cell_comp.compile_file(map_path)
        event_ir = events_comp.compile_file(map_path)
        scripts_ir = script_comp.compile_file(script_path)

        local_script_ids = {script["id"] for script in scripts_ir["scripts"]}
        duplicates = all_script_ids & local_script_ids
        if duplicates:
            raise ValueError(f"duplicate RC script ids across maps: {sorted(duplicates)}")
        all_script_ids |= local_script_ids
        script_irs[map_id] = scripts_ir

        bound_scripts = {
            item["script"]
            for item in (
                map_ir["objects"]
                + map_ir["interactions"]
                + json.loads(map_path.read_text(encoding="utf-8")).get("coord_events", [])
            )
            if item.get("script")
        }
        missing_bound = bound_scripts - local_script_ids
        if missing_bound:
            raise ValueError(f"{map_id}: map binds missing scripts {sorted(missing_bound)}")

        referenced_dialogues = {
            relocation["symbol"]
            for script in scripts_ir["scripts"]
            for relocation in script["relocations"]
            if relocation["kind"] == "dialogue"
        }
        missing_dialogue = referenced_dialogues - dialogue_ids
        if missing_dialogue:
            raise ValueError(f"{map_id}: missing dialogue {sorted(missing_dialogue)}")

        for script in scripts_ir["scripts"]:
            for relocation in script["relocations"]:
                if relocation["kind"] == "map_id" and relocation["symbol"] not in map_ids:
                    raise ValueError(
                        f"{map_id}: script {script['id']} targets unreserved map "
                        f"{relocation['symbol']}"
                    )

        for block_name in ("warp_events",):
            for relocation in event_ir[block_name]["relocations"]:
                if relocation["kind"] == "map_id" and relocation["symbol"] not in map_ids:
                    raise ValueError(
                        f"{map_id}: {block_name} targets unreserved map {relocation['symbol']}"
                    )

        payload = payload_comp.compile_payload(
            map_spec_path=map_path,
            script_spec_path=script_path,
            base_address=DUMMY_BASE_START + index * DUMMY_BASE_STEP,
            primary_tileset_ptr=DUMMY_PRIMARY_TILESET,
            secondary_tileset_ptr=DUMMY_SECONDARY_TILESET,
        )

        if payload["map"] != map_id:
            raise ValueError(f"{map_id}: payload id mismatch")
        if payload["size"] <= cell_ir["map_bytes"]:
            raise ValueError(f"{map_id}: payload unexpectedly smaller than map cells")

        compiled.append({
            "map": map_id,
            "group": int(slot_by_id[map_id]["map_group"]),
            "num": int(slot_by_id[map_id]["map_num"]),
            "dimensions": map_ir["dimensions"],
            "payload_bytes": payload["size"],
            "scripts": len(scripts_ir["scripts"]),
            "objects": event_ir["object_events"]["count"],
            "warps": event_ir["warp_events"]["count"],
            "coord_events": event_ir["coord_events"]["count"],
            "bg_events": event_ir["bg_events"]["count"],
        })

    expected_path = [
        "RC_DELIVERY_HUB",
        "RC_CAGLIARI_MARINA",
        "RC_PORT_CONNECTION",
        "RC_CASTELLO_ASCENT",
        "RC_DEPLOY_DISTRICT",
        "RC_DEPLOY_ROOM",
    ]
    if [item["map"] for item in compiled] != expected_path:
        raise ValueError("Chapter 1 map order changed unexpectedly")

    total_payload = sum(item["payload_bytes"] for item in compiled)
    print("RC_CHAPTER1_PREFLIGHT=PASS")
    print(f"RC_CHAPTER1_MAP_COUNT={len(compiled)}")
    print(f"RC_CHAPTER1_SCRIPT_COUNT={len(all_script_ids)}")
    print(f"RC_CHAPTER1_PAYLOAD_BYTES={total_payload}")
    print("RC_CONTENT_GRAPH=PASS")
    print(f"RC_TILESET_ART_STATUS={tileset_status}")
    for item in compiled:
        print(
            "RC_CHAPTER1_MAP="
            f"{item['map']}:{item['group']}/{item['num']}:"
            f"{item['dimensions']['width']}x{item['dimensions']['height']}:"
            f"{item['payload_bytes']}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"RC_CHAPTER1_PREFLIGHT=FAIL:{exc}")
        raise SystemExit(1)
