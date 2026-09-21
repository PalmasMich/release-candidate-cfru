#!/usr/bin/env python3
"""Fail-fast acceptance gate for the Cagliari Preview 0.1 source contract.

This does not need or inspect a private ROM. It verifies that the source-controlled
preview manifests agree with the species IDs and runtime patch contract before a
manual/private-ROM smoke test is requested.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"


def load_patcher():
    spec = importlib.util.spec_from_file_location("rc_preview_patcher", PATCHER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str):
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    p = load_patcher()
    trainers = load_json("trainers.yml")
    dialogue = load_json("dialogue.yml")
    encounters = load_json("encounters.yml")
    events = load_json("events.yml")

    rival = trainers["rival"]
    require(rival["id"] == "RC_RIVAL_KPI", "KPI rival is missing")
    require(rival["starter_matrix"] == {
        "SPECIES_RC_TURTLE_01": "SPECIES_RC_FIREFOX_01",
        "SPECIES_RC_FROG_01": "SPECIES_RC_TURTLE_01",
        "SPECIES_RC_FIREFOX_01": "SPECIES_RC_FROG_01",
    }, "KPI rival starter matrix drifted")

    scenes = {scene["id"] for scene in dialogue["scenes"]}
    for required in ("RC_DIALOGUE_OPENING", "RC_DIALOGUE_STARTER", "RC_DIALOGUE_RIVAL_INTRO", "RC_DIALOGUE_WILD_TUTORIAL_TRIGGER", "RC_DIALOGUE_DEPLOY_TEASER"):
        require(required in scenes, f"required preview dialogue missing: {required}")

    require(p.TARTREK_SPECIES_ID == 0x050E, "Tartrek runtime ID drifted")
    require(p.FROBYTE_SPECIES_ID == 0x050F, "Frobyte runtime ID drifted")
    require(p.EMBERFOX_SPECIES_ID == 0x0510, "Emberfox runtime ID drifted")
    require(p.MISTRILLO_SPECIES_ID == 0x0511, "Mistrillo runtime ID drifted")

    weighted = {}
    for species, weight in zip(p.ROUTE1_PREVIEW_SPECIES, p.GRASS_SLOT_WEIGHTS):
        weighted[species] = weighted.get(species, 0) + weight
    require(weighted[p.MISTRILLO_SPECIES_ID] == 60, "Mistrillo must own 60% of Port Link")
    require(weighted[p.WINGULL_SPECIES_ID] == 25, "Wingull must own 25% of Port Link")
    require(weighted[p.MEOWTH_SPECIES_ID] == 15, "Meowth must own 15% of Port Link")

    tables = {table["id"]: table for table in encounters["tables"]}
    port = tables.get("RC_PORT_CONNECTION_GRASS")
    require(port is not None, "Port Link encounter manifest missing")
    manifest_weights = {slot["species"]: slot["weight"] for slot in port["slots"]}
    require(manifest_weights == {"SPECIES_RC_CAGLIARI_WILD_01": 60, "SPECIES_WINGULL": 25, "SPECIES_MEOWTH": 15}, "Port Link encounter manifest drifted from runtime patch")

    by_id = {event["id"]: event for event in events["flow"]}
    expected_path = ["RC_EVENT_ARRIVAL", "RC_EVENT_STARTER_ASSIGNMENT", "RC_EVENT_RIVAL_INTRO", "RC_EVENT_FIRST_WILD", "RC_EVENT_DEPLOY_TEASER"]
    require(events.get("preview_acceptance_path") == expected_path, "Preview acceptance path drifted")
    require("RC_EVENT_PORT_TRAINER" not in expected_path, "Reserved Port trainer must not block Preview 0.1")
    produced = set()
    for event_id in expected_path:
        event = by_id[event_id]
        require(event.get("scope") == "preview", f"acceptance event left preview scope: {event_id}")
        require(set(event.get("requires", ())).issubset(produced), f"unsatisfied acceptance dependency: {event_id}")
        produced.update(event.get("sets", ()))
    require("RC_FLAG_DEPLOY_TEASER_SEEN" in produced, "Preview no longer reaches deploy teaser")
    require(by_id["RC_EVENT_PORT_TRAINER"].get("implementation_status") == "reserved_not_relocated", "Port trainer status is not fail-honest")

    print("RC_PREVIEW_CONTRACT=PASS")
    print("RC_PREVIEW_FLOW=OPENING>DELIVERY_HUB>STARTER>KPI_RIVAL>PORT_LINK>CUSTOM_WILD>MARINA_PORTO")
    print("RC_PREVIEW_OPTIONAL_TRAINER=DEFERRED_NOT_BLOCKING")
    print("RC_PREVIEW_MANUAL_TEST=DEFER_UNTIL_PRIVATE_ROM_BUILD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
