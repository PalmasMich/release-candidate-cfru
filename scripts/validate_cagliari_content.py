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
    "RC_DELIVERY_HUB",
    "RC_CAGLIARI_MARINA",
    "RC_PORT_CONNECTION",
}

REQUIRED_FLAGS = {
    "RC_FLAG_STARTER_CHOSEN",
    "RC_FLAG_RIVAL_INTRO_DONE",
    "RC_FLAG_WILD_TUTORIAL_DONE",
    "RC_FLAG_RIVAL_BATTLE_DONE",
    "RC_FLAG_DEPLOY_TEASER_SEEN",
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
    map_ids = [item["id"] for item in maps["maps"]]
    require_unique(map_ids, "map id")
    missing_maps = REQUIRED_MAPS - set(map_ids)
    if missing_maps:
        raise ValueError(f"missing required maps: {sorted(missing_maps)}")

    events = load("events.yml")
    flags = list(events["flags"])
    require_unique(flags, "story flag")
    missing_flags = REQUIRED_FLAGS - set(flags)
    if missing_flags:
        raise ValueError(f"missing required story flags: {sorted(missing_flags)}")

    event_ids = [event["id"] for event in events["flow"]]
    require_unique(event_ids, "event id")
    for event in events["flow"]:
        if event["map"] not in map_ids:
            raise ValueError(f"event {event['id']} references unknown map {event['map']}")
        for flag in event.get("requires", []) + event.get("sets", []):
            if flag not in flags:
                raise ValueError(f"event {event['id']} references unknown flag {flag}")

    dialogue = load("dialogue.yml")
    dialogue_ids = [scene["id"] for scene in dialogue["scenes"]]
    require_unique(dialogue_ids, "dialogue id")
    all_lines = [line for scene in dialogue["scenes"] for line in scene["lines"]]
    opening = "Benvenuto a Cagliari. Il progetto era già iniziato quando sei arrivato."
    if opening not in all_lines:
        raise ValueError("approved opening line is missing")

    encounters = load("encounters.yml")
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


if __name__ == "__main__":
    try:
        validate()
    except ValueError as exc:
        print(f"CAGLIARI_CONTENT_INVALID: {exc}")
        raise SystemExit(1)
    print("CAGLIARI_CONTENT_VALID")
