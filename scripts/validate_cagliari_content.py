#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"

REQUIRED_FILES = [
    "maps.yml",
    "events.yml",
    "dialogue.yml",
    "encounters.yml",
    "trainers.yml",
]

REQUIRED_MAPS = {
    "RC_CAGLIARI_ARRIVAL",
    "RC_DELIVERY_HUB",
    "RC_CAGLIARI_MARINA",
    "RC_PORT_CONNECTION",
    "RC_CASTELLO_ASCENT",
    "RC_DEPLOY_DISTRICT",
    "RC_DEPLOY_ROOM_01",
}

REQUIRED_PREVIEW_FLAGS = {
    "RC_FLAG_ARRIVAL_DONE",
    "RC_FLAG_STARTER_CHOSEN",
    "RC_FLAG_RIVAL_INTRO_DONE",
    "RC_FLAG_WILD_TUTORIAL_DONE",
    "RC_FLAG_PORT_TRAINER_DONE",
    "RC_FLAG_DEPLOY_TEASER_SEEN",
}

REQUIRED_CHAPTER_FLAGS = {
    "RC_FLAG_SCOPE_CHANGE_REVEALED",
    "RC_FLAG_CASTELLO_UNLOCKED",
    "RC_FLAG_GO_NO_GO_STARTED",
    "RC_FLAG_RELEASE_MANAGER_DEFEATED",
    "RC_FLAG_DEPLOY_01_COMPLETE",
}

STARTERS = {
    "SPECIES_RC_TURTLE_01",
    "SPECIES_RC_FROG_01",
    "SPECIES_RC_FIREFOX_01",
}


def load(name: str):
    path = CONTENT / name
    if not path.exists():
        raise ValueError(f"missing content file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON-compatible YAML in {path}: {exc}") from exc


def require_unique(values, label: str):
    values = list(values)
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}: {values}")


def validate() -> None:
    for name in REQUIRED_FILES:
        if not (CONTENT / name).exists():
            raise ValueError(f"missing required file: {name}")

    maps = load("maps.yml")
    if maps.get("chapter", {}).get("id") != "RC_CHAPTER_01_CAGLIARI":
        raise ValueError("maps must belong to RC_CHAPTER_01_CAGLIARI")

    map_ids = [item["id"] for item in maps["maps"]]
    require_unique(map_ids, "map id")
    missing_maps = REQUIRED_MAPS - set(map_ids)
    if missing_maps:
        raise ValueError(f"missing required maps: {sorted(missing_maps)}")

    bootstrap_maps = [item for item in maps["maps"] if item.get("status") == "bootstrap_replacement_pending"]
    if not bootstrap_maps:
        raise ValueError("at least one current bootstrap map must be explicitly tagged")
    for item in bootstrap_maps:
        if not item.get("bootstrap_source"):
            raise ValueError(f"bootstrap map {item['id']} must declare bootstrap_source")

    permanent_maps = [item for item in maps["maps"] if item.get("status") == "permanent"]
    if len(permanent_maps) < 5:
        raise ValueError("Chapter 1 must define permanent custom-world areas, not only bootstrap maps")

    dialogue = load("dialogue.yml")
    dialogue_ids = [scene["id"] for scene in dialogue["scenes"]]
    require_unique(dialogue_ids, "dialogue id")
    dialogue_id_set = set(dialogue_ids)
    all_lines = [line for scene in dialogue["scenes"] for line in scene["lines"]]
    opening = "Benvenuto a Cagliari. Il progetto era già iniziato quando sei arrivato."
    if opening not in all_lines:
        raise ValueError("approved opening line is missing")

    encounters = load("encounters.yml")
    encounter_ids = [table["id"] for table in encounters["tables"]]
    require_unique(encounter_ids, "encounter table id")
    encounter_id_set = set(encounter_ids)
    for table in encounters["tables"]:
        if table["map"] not in map_ids:
            raise ValueError(f"encounter table {table['id']} references unknown map {table['map']}")
        total_weight = sum(slot["weight"] for slot in table["slots"])
        if total_weight != 100:
            raise ValueError(f"encounter table {table['id']} weight must total 100, got {total_weight}")
        for slot in table["slots"]:
            if slot["min_level"] > slot["max_level"]:
                raise ValueError(f"invalid level range for {slot['species']}")

    encounter_species = {
        slot["species"]
        for table in encounters["tables"]
        for slot in table["slots"]
    }
    if "SPECIES_RC_CAGLIARI_WILD_01" not in encounter_species:
        raise ValueError("mandatory original Cagliari wild species is absent")

    trainers = load("trainers.yml")
    matrix = trainers["rival"]["starter_matrix"]
    if set(matrix) != STARTERS:
        raise ValueError("rival starter matrix must have exactly the three RC starters as keys")
    if set(matrix.values()) != STARTERS:
        raise ValueError("rival starter matrix must map to the three RC starters")
    for player_starter, rival_starter in matrix.items():
        if player_starter == rival_starter:
            raise ValueError("rival cannot use the player's chosen starter")

    trainer_ids = [trainers["rival"]["id"], trainers["route_trainer"]["id"]]
    require_unique(trainer_ids, "trainer id")
    trainer_id_set = set(trainer_ids)

    rival_intro = trainers["rival"].get("intro_dialogue")
    if rival_intro not in dialogue_id_set:
        raise ValueError(f"rival references unknown dialogue {rival_intro}")

    route_trainer = trainers["route_trainer"]
    if not route_trainer.get("party"):
        raise ValueError("route trainer must have a non-empty party")
    for mon in route_trainer["party"]:
        if not 1 <= mon["level"] <= 100:
            raise ValueError(f"invalid trainer level for {mon['species']}: {mon['level']}")
    for key in ("intro_dialogue", "outro_dialogue"):
        dialogue_id = route_trainer.get(key)
        if dialogue_id not in dialogue_id_set:
            raise ValueError(f"route trainer references unknown dialogue {dialogue_id}")

    events = load("events.yml")
    if events.get("chapter") != "RC_CHAPTER_01_CAGLIARI":
        raise ValueError("events must belong to RC_CHAPTER_01_CAGLIARI")

    flags = list(events["flags"])
    require_unique(flags, "story flag")
    required_flags = REQUIRED_PREVIEW_FLAGS | REQUIRED_CHAPTER_FLAGS
    missing_flags = required_flags - set(flags)
    if missing_flags:
        raise ValueError(f"missing required story flags: {sorted(missing_flags)}")

    event_ids = [event["id"] for event in events["flow"]]
    require_unique(event_ids, "event id")

    produced_flags = set()
    for event in events["flow"]:
        if event["map"] not in map_ids:
            raise ValueError(f"event {event['id']} references unknown map {event['map']}")

        if event.get("scope") not in {"preview", "chapter_01"}:
            raise ValueError(f"event {event['id']} must declare preview or chapter_01 scope")

        for flag in event.get("requires", []) + event.get("sets", []):
            if flag not in flags:
                raise ValueError(f"event {event['id']} references unknown flag {flag}")

        missing_prereqs = set(event.get("requires", [])) - produced_flags
        if missing_prereqs:
            raise ValueError(
                f"event {event['id']} requires flags not produced earlier in flow: "
                f"{sorted(missing_prereqs)}"
            )

        dialogue_id = event.get("dialogue")
        if dialogue_id is not None and dialogue_id not in dialogue_id_set:
            raise ValueError(f"event {event['id']} references unknown dialogue {dialogue_id}")

        encounter_id = event.get("encounter_table")
        if encounter_id is not None and encounter_id not in encounter_id_set:
            raise ValueError(f"event {event['id']} references unknown encounter table {encounter_id}")

        trainer_id = event.get("trainer")
        if trainer_id is not None and trainer_id not in trainer_id_set:
            raise ValueError(f"event {event['id']} references unknown trainer {trainer_id}")

        produced_flags.update(event.get("sets", []))

    missing_producers = required_flags - produced_flags
    if missing_producers:
        raise ValueError(f"required story flags are never produced: {sorted(missing_producers)}")

    if "RC_FLAG_DEPLOY_01_COMPLETE" not in produced_flags:
        raise ValueError("Chapter 1 must terminate in Deploy 01 completion")


if __name__ == "__main__":
    try:
        validate()
    except ValueError as exc:
        print(f"CAGLIARI_CONTENT_INVALID: {exc}")
        raise SystemExit(1)
    print("CAGLIARI_CONTENT_VALID")
