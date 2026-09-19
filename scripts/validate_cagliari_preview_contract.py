#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"
LEARNSETS = ROOT / "src" / "Tables" / "level_up_learnsets.c"

REQUIRED_MAPS = {
    "RC_CAGLIARI_ARRIVAL",
    "RC_DELIVERY_HUB",
    "RC_CAGLIARI_MARINA",
    "RC_PORT_CONNECTION",
}
REQUIRED_PREVIEW_EVENTS = {
    "RC_EVENT_ARRIVAL",
    "RC_EVENT_STARTER_ASSIGNMENT",
    "RC_EVENT_RIVAL_INTRO",
    "RC_EVENT_FIRST_WILD",
    "RC_EVENT_PORT_TRAINER",
    "RC_EVENT_DEPLOY_TEASER",
}
REQUIRED_DIALOGUE = {
    "RC_DIALOGUE_OPENING",
    "RC_DIALOGUE_STARTER",
    "RC_DIALOGUE_RIVAL_INTRO",
    "RC_DIALOGUE_WILD_TUTORIAL_TRIGGER",
    "RC_DIALOGUE_PORT_TRAINER_INTRO",
    "RC_DIALOGUE_DEPLOY_TEASER",
}
REQUIRED_LEARNSET_MARKERS = {
    "SPECIES_RC_TURTLE_01": "sRCTartrekLevelUpLearnset",
    "SPECIES_RC_FROG_01": "sRCFrobyteLevelUpLearnset",
    "SPECIES_RC_FIREFOX_01": "sRCEmberfoxLevelUpLearnset",
    "SPECIES_RC_MISTRILLO": "sRCMistrilloLevelUpLearnset",
}


def load_json(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate() -> None:
    maps = load_json("maps.yml")
    events = load_json("events.yml")
    dialogue = load_json("dialogue.yml")
    trainers = load_json("trainers.yml")
    encounters = load_json("encounters.yml")
    patcher = PATCHER.read_text(encoding="utf-8")
    learnsets = LEARNSETS.read_text(encoding="utf-8")

    map_ids = {item["id"] for item in maps["maps"]}
    require(REQUIRED_MAPS <= map_ids, "Thick preview is missing a required Cagliari map contract.")

    preview_events = {item["id"] for item in events["flow"] if item.get("scope") == "preview"}
    require(REQUIRED_PREVIEW_EVENTS <= preview_events, "Thick preview event chain is incomplete.")

    dialogue_ids = {item["id"] for item in dialogue["scenes"]}
    require(REQUIRED_DIALOGUE <= dialogue_ids, "Thick preview corporate dialogue contract is incomplete.")

    rival = trainers["rival"]
    require(rival["id"] == "RC_RIVAL_KPI", "KPI rival contract is missing.")
    require(len(rival["starter_matrix"]) == 3, "KPI rival must react to all three starter choices.")

    tables = {item["id"]: item for item in encounters["tables"]}
    route = tables.get("RC_PORT_CONNECTION_GRASS")
    require(route is not None, "Port Link encounter table is missing.")
    weights = {item["species"]: item["weight"] for item in route["slots"]}
    require(weights.get("SPECIES_RC_MISTRILLO") == 60, "Mistrillo must remain the primary Port Link encounter at 60%.")
    require(sum(weights.values()) == 100, "Port Link encounter weights must total 100%.")

    for species, marker in REQUIRED_LEARNSET_MARKERS.items():
        require(marker in learnsets, f"CFRU learnset definition missing for {species}.")
        require(f"[{species}] = {marker}" in learnsets, f"CFRU learnset table registration missing for {species}.")

    for marker in (
        "Welcome to Release Candidate!",
        "DELIVERY HUB - CAGLIARI",
        "KPI check: show velocity!",
        "PORT LINK\\nCAGLIARI - MARINA PORTO",
        "MISTRILLO_SPECIES_ID",
    ):
        require(marker in patcher, f"ROM preview patch is missing visible contract marker: {marker}")

    print("RC_CAGLIARI_PREVIEW_CONTRACT=OK")
    print("RC_CAGLIARI_PREVIEW_SCOPE=HUB+THREE_STARTERS+KPI_RIVAL+PORT_LINK+MISTRILLO+MARINA_TEASER")


def main() -> int:
    try:
        validate()
    except (FileNotFoundError, KeyError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
