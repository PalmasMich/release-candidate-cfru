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

MAPS = (
    ("RC_DELIVERY_HUB", "RC_DELIVERY_HUB.json", "RC_DELIVERY_HUB.json"),
    ("RC_CAGLIARI_MARINA", "RC_CAGLIARI_MARINA.json", "RC_CAGLIARI_MARINA.json"),
    ("RC_PORT_CONNECTION", "RC_PORT_CONNECTION.json", "RC_PORT_CONNECTION.json"),
    ("RC_CASTELLO_ASCENT", "RC_CASTELLO_ASCENT.json", "RC_CASTELLO_ASCENT.json"),
    ("RC_DEPLOY_DISTRICT", "RC_DEPLOY_DISTRICT.json", "RC_DEPLOY_DISTRICT.json"),
    ("RC_DEPLOY_ROOM", "RC_DEPLOY_ROOM.json", "RC_DEPLOY_ROOM.json"),
)

EXPECTED_PROGRESSION = (
    ("RC_DELIVERY_HUB", "RC_CAGLIARI_MARINA"),
    ("RC_CAGLIARI_MARINA", "RC_PORT_CONNECTION"),
    ("RC_CAGLIARI_MARINA", "RC_CASTELLO_ASCENT"),
    ("RC_CASTELLO_ASCENT", "RC_DEPLOY_DISTRICT"),
    ("RC_DEPLOY_DISTRICT", "RC_DEPLOY_ROOM"),
)

# These checks make the source preflight prove the preview's first playable loop,
# not merely that each JSON file compiles in isolation.
PREVIEW_REQUIRED_SCRIPTS = {
    "RC_DELIVERY_HUB": {
        "RC_SCRIPT_STARTER_TARTREK",
        "RC_SCRIPT_STARTER_FROBYTE",
        "RC_SCRIPT_STARTER_EMBERFOX",
        "RC_SCRIPT_KPI_RIVAL",
    },
    "RC_CAGLIARI_MARINA": {
        "RC_SCRIPT_MARINA_DELIVERY_LEAD",
        "RC_SCRIPT_CASTELLO_GATE",
    },
    "RC_PORT_CONNECTION": {
        "RC_SCRIPT_WILD_TUTORIAL_TRIGGER",
        "RC_SCRIPT_PORT_TRAINER",
    },
}
PREVIEW_REQUIRED_DIALOGUES = {
    "RC_DIALOGUE_STARTER",
    "RC_DIALOGUE_STARTER_TARTREK_CONFIRM",
    "RC_DIALOGUE_STARTER_FROBYTE_CONFIRM",
    "RC_DIALOGUE_STARTER_EMBERFOX_CONFIRM",
    "RC_DIALOGUE_RIVAL_INTRO",
    "RC_DIALOGUE_WILD_TUTORIAL_TRIGGER",
    "RC_DIALOGUE_PORT_TRAINER_INTRO",
    "RC_DIALOGUE_PORT_TRAINER_OUTRO",
    "RC_DIALOGUE_DEPLOY_TEASER",
}
PREVIEW_REQUIRED_FLAGS = {
    "RC_FLAG_STARTER_CHOSEN",
    "RC_FLAG_RIVAL_INTRO_DONE",
    "RC_FLAG_WILD_TUTORIAL_DONE",
    "RC_FLAG_PORT_TRAINER_DONE",
    "RC_FLAG_DEPLOY_TEASER_SEEN",
}
PREVIEW_REQUIRED_OPS = {
    "RC_SCRIPT_STARTER_TARTREK": {"givemon", "trainerbattle_single", "setflag"},
    "RC_SCRIPT_STARTER_FROBYTE": {"givemon", "trainerbattle_single", "setflag"},
    "RC_SCRIPT_STARTER_EMBERFOX": {"givemon", "trainerbattle_single", "setflag"},
    "RC_SCRIPT_WILD_TUTORIAL_TRIGGER": {"setwildbattle", "dowildbattle", "setflag"},
    "RC_SCRIPT_PORT_TRAINER": {"trainerbattle_single", "setflag"},
}

DUMMY_PRIMARY_TILESET = 0x08100000
DUMMY_SECONDARY_TILESET = 0x08110000
DUMMY_BASE_START = 0x08900000
DUMMY_BASE_STEP = 0x00020000


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_preview_contract(dialogue_ids: set[str], raw_scripts_by_map: dict[str, dict]) -> None:
    missing_dialogue = PREVIEW_REQUIRED_DIALOGUES - dialogue_ids
    if missing_dialogue:
        raise ValueError(f"playable preview dialogue missing: {sorted(missing_dialogue)}")

    flags = json.loads((CONTENT / "flags.json").read_text(encoding="utf-8"))["flags"]
    missing_flags = PREVIEW_REQUIRED_FLAGS - set(flags)
    if missing_flags:
        raise ValueError(f"playable preview flags missing: {sorted(missing_flags)}")

    for map_id, required_ids in PREVIEW_REQUIRED_SCRIPTS.items():
        spec = raw_scripts_by_map.get(map_id)
        if spec is None:
            raise ValueError(f"playable preview script spec missing for {map_id}")
        by_id = {script["id"]: script for script in spec["scripts"]}
        missing = required_ids - set(by_id)
        if missing:
            raise ValueError(f"{map_id}: playable preview scripts missing: {sorted(missing)}")
        for script_id, required_ops in PREVIEW_REQUIRED_OPS.items():
            if script_id not in by_id:
                continue
            actual_ops = {entry.get("op") for entry in by_id[script_id]["ops"] if entry.get("op")}
            missing_ops = required_ops - actual_ops
            if missing_ops:
                raise ValueError(f"{script_id}: playable preview ops missing: {sorted(missing_ops)}")

    hub = {s["id"]: s for s in raw_scripts_by_map["RC_DELIVERY_HUB"]["scripts"]}
    expected_starters = {
        "RC_SCRIPT_STARTER_TARTREK": ("SPECIES_RC_TURTLE_01", 328),
        "RC_SCRIPT_STARTER_FROBYTE": ("SPECIES_RC_FROG_01", 327),
        "RC_SCRIPT_STARTER_EMBERFOX": ("SPECIES_RC_FIREFOX_01", 326),
    }
    for script_id, (species, trainer_id) in expected_starters.items():
        ops = hub[script_id]["ops"]
        gives = [op for op in ops if op.get("op") == "givemon"]
        battles = [op for op in ops if op.get("op") == "trainerbattle_single"]
        flags_set = {op.get("flag") for op in ops if op.get("op") == "setflag"}
        if len(gives) != 1 or gives[0].get("species") != species or int(gives[0].get("level", 0)) != 5:
            raise ValueError(f"{script_id}: starter grant contract drifted")
        if len(battles) != 1 or int(battles[0].get("trainer_id", -1)) != trainer_id:
            raise ValueError(f"{script_id}: KPI rival matrix drifted")
        if not {"RC_FLAG_STARTER_CHOSEN", "RC_FLAG_RIVAL_INTRO_DONE"} <= flags_set:
            raise ValueError(f"{script_id}: progression flags incomplete")

    port = {s["id"]: s for s in raw_scripts_by_map["RC_PORT_CONNECTION"]["scripts"]}
    wild_ops = port["RC_SCRIPT_WILD_TUTORIAL_TRIGGER"]["ops"]
    wild = [op for op in wild_ops if op.get("op") == "setwildbattle"]
    if len(wild) != 1 or wild[0].get("species") != "SPECIES_RC_CAGLIARI_WILD_01" or int(wild[0].get("level", 0)) != 3:
        raise ValueError("Port Link first custom encounter must remain level-3 Mistrillo")
    if "RC_FLAG_WILD_TUTORIAL_DONE" not in {op.get("flag") for op in wild_ops if op.get("op") == "setflag"}:
        raise ValueError("Port Link first custom encounter does not close its tutorial flag")

    trainer_ops = port["RC_SCRIPT_PORT_TRAINER"]["ops"]
    battles = [op for op in trainer_ops if op.get("op") == "trainerbattle_single"]
    if len(battles) != 1 or int(battles[0].get("trainer_id", -1)) != 89:
        raise ValueError("Port Link trainer bootstrap id drifted")
    if "RC_FLAG_PORT_TRAINER_DONE" not in {op.get("flag") for op in trainer_ops if op.get("op") == "setflag"}:
        raise ValueError("Port Link trainer does not close its progression flag")

    marina = {s["id"]: s for s in raw_scripts_by_map["RC_CAGLIARI_MARINA"]["scripts"]}
    lead_ops = marina["RC_SCRIPT_MARINA_DELIVERY_LEAD"]["ops"]
    checked = {op.get("flag") for op in lead_ops if op.get("op") == "checkflag"}
    set_flags = {op.get("flag") for op in lead_ops if op.get("op") == "setflag"}
    if not {"RC_FLAG_PORT_TRAINER_DONE", "RC_FLAG_DEPLOY_TEASER_SEEN"} <= checked:
        raise ValueError("Marina lead no longer gates the deploy teaser behind Port Link")
    if "RC_FLAG_DEPLOY_TEASER_SEEN" not in set_flags:
        raise ValueError("Marina lead no longer records deploy teaser completion")


def main() -> int:
    map_comp = load_module(MAP_COMPILER_PATH, "rc_map_preflight")
    cell_comp = load_module(CELL_COMPILER_PATH, "rc_cells_preflight")
    events_comp = load_module(EVENTS_COMPILER_PATH, "rc_events_preflight")
    script_comp = load_module(SCRIPT_COMPILER_PATH, "rc_scripts_preflight")
    dialogue_comp = load_module(DIALOGUE_COMPILER_PATH, "rc_dialogue_preflight")
    payload_comp = load_module(PAYLOAD_COMPILER_PATH, "rc_payload_preflight")

    slots = json.loads((CONTENT / "map_slots.json").read_text(encoding="utf-8"))["slots"]
    slot_by_id = {slot["rc_map"]: slot for slot in slots}
    if len(slot_by_id) != len(slots):
        raise ValueError("duplicate RC map slot ids")

    map_ids = events_comp.load_map_ids()
    dialogue_ir = dialogue_comp.compile_file()
    dialogue_ids = {scene["id"] for scene in dialogue_ir["scenes"]}

    compiled = []
    all_script_ids = set()
    progression_edges = set()
    raw_scripts_by_map = {}

    for index, (map_id, map_name, script_name) in enumerate(MAPS):
        map_path = CONTENT / "map_specs" / map_name
        script_path = CONTENT / "script_specs" / script_name

        if map_id not in slot_by_id:
            raise ValueError(f"{map_id}: missing reserved map slot")

        raw_map = json.loads(map_path.read_text(encoding="utf-8"))
        raw_scripts_by_map[map_id] = json.loads(script_path.read_text(encoding="utf-8"))
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

        bound_scripts = {
            item["script"]
            for item in (map_ir["objects"] + map_ir["interactions"] + raw_map.get("coord_events", []))
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

        for warp in raw_map.get("warps", []):
            target = warp.get("target_map")
            if target:
                progression_edges.add((map_id, target))

        for script in scripts_ir["scripts"]:
            for relocation in script["relocations"]:
                if relocation["kind"] == "map_id":
                    if relocation["symbol"] not in map_ids:
                        raise ValueError(f"{map_id}: script {script['id']} targets unreserved map {relocation['symbol']}")
                    progression_edges.add((map_id, relocation["symbol"]))

        for relocation in event_ir["warp_events"]["relocations"]:
            if relocation["kind"] == "map_id" and relocation["symbol"] not in map_ids:
                raise ValueError(f"{map_id}: warp_events targets unreserved map {relocation['symbol']}")

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

    validate_preview_contract(dialogue_ids, raw_scripts_by_map)

    expected_path = [item[0] for item in MAPS]
    if [item["map"] for item in compiled] != expected_path:
        raise ValueError("Chapter 1 map order changed unexpectedly")

    missing_progression = [edge for edge in EXPECTED_PROGRESSION if edge not in progression_edges]
    if missing_progression:
        raise ValueError(f"Chapter 1 progression edge(s) missing: {missing_progression}")

    reachable = {"RC_DELIVERY_HUB"}
    changed = True
    while changed:
        changed = False
        for source, target in progression_edges:
            if source in reachable and target not in reachable:
                reachable.add(target)
                changed = True
    unreachable = set(expected_path) - reachable
    if unreachable:
        raise ValueError(f"Chapter 1 map(s) unreachable from Delivery Hub: {sorted(unreachable)}")

    total_payload = sum(item["payload_bytes"] for item in compiled)
    print("RC_CHAPTER1_PREFLIGHT=PASS")
    print("RC_PLAYABLE_PREVIEW_CONTRACT=PASS")
    print(f"RC_CHAPTER1_MAP_COUNT={len(compiled)}")
    print(f"RC_CHAPTER1_SCRIPT_COUNT={len(all_script_ids)}")
    print(f"RC_CHAPTER1_PROGRESSION_EDGES={len(progression_edges)}")
    print(f"RC_CHAPTER1_PAYLOAD_BYTES={total_payload}")
    for item in compiled:
        print("RC_CHAPTER1_MAP=" f"{item['map']}:{item['group']}/{item['num']}:" f"{item['dimensions']['width']}x{item['dimensions']['height']}:" f"{item['payload_bytes']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"RC_CHAPTER1_PREFLIGHT=FAIL:{exc}")
        raise SystemExit(1)
