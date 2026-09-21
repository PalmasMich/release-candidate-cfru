#!/usr/bin/env python3
"""Static, ROM-free audit for Cagliari Preview 0.1.

Keeps the playable contract, encounter manifest and trainer manifest aligned before
we spend a private-ROM smoke-test cycle. This deliberately fails closed.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"


def load(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    acceptance = load("playable_acceptance.json")
    events = load("events.yml")
    encounters = load("encounters.yml")
    trainers = load("trainers.yml")
    failures: list[str] = []

    require(acceptance.get("governance", {}).get("branch") == "feature/cagliari-preview-0.1",
            "acceptance must target feature/cagliari-preview-0.1", failures)
    require(acceptance.get("governance", {}).get("pr_must_remain_draft") is True,
            "preview PR must remain Draft", failures)
    require(acceptance.get("governance", {}).get("rom_binary_must_not_be_committed") is True,
            "full ROM binaries must remain uncommitted", failures)

    flow = {item["id"]: item for item in events.get("flow", [])}
    for event_id in events.get("preview_acceptance_path", []):
        require(event_id in flow, f"missing acceptance event {event_id}", failures)
        if event_id in flow:
            require(flow[event_id].get("scope") == "preview",
                    f"{event_id} must remain preview scope", failures)
            require("implemented" in flow[event_id].get("implementation_status", ""),
                    f"{event_id} is not implemented", failures)

    grass = encounters.get("tables", {}).get("RC_PORT_CONNECTION_GRASS", encounters.get("RC_PORT_CONNECTION_GRASS", {}))
    slots = grass.get("slots", grass.get("encounters", []))
    weights: dict[str, int] = {}
    for slot in slots:
        species = slot.get("species")
        weight = slot.get("weight", slot.get("chance", 0))
        if species:
            weights[species] = weights.get(species, 0) + int(weight)
    require(weights.get("SPECIES_RC_CAGLIARI_WILD_01") == 60,
            f"Mistrillo Port Link weight must be 60, got {weights.get('SPECIES_RC_CAGLIARI_WILD_01')}", failures)
    require(weights.get("SPECIES_WINGULL") == 25,
            f"Wingull Port Link weight must be 25, got {weights.get('SPECIES_WINGULL')}", failures)
    require(weights.get("SPECIES_MEOWTH") == 15,
            f"Meowth Port Link weight must be 15, got {weights.get('SPECIES_MEOWTH')}", failures)

    rival = trainers.get("rival", {})
    matrix = rival.get("starter_matrix", {})
    expected = {
        "SPECIES_RC_TURTLE_01": "SPECIES_RC_FIREFOX_01",
        "SPECIES_RC_FROG_01": "SPECIES_RC_TURTLE_01",
        "SPECIES_RC_FIREFOX_01": "SPECIES_RC_FROG_01",
    }
    require(matrix == expected, "KPI rival starter matrix drifted from ROM patch contract", failures)
    require(rival.get("preview_level") == 5, "KPI rival must remain level 5 in Preview 0.1", failures)

    manual = acceptance.get("next_private_smoke", {})
    route = manual.get("minimum_route", [])
    require(any("guaranteed level-3 Mistrillo" in step for step in route),
            "private smoke route must include guaranteed level-3 Mistrillo", failures)
    require(manual.get("manual_only") is True,
            "private-ROM smoke must remain explicitly manual-only", failures)

    if failures:
        print("RC_PREVIEW_AUDIT=FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("RC_PREVIEW_AUDIT=PASS")
    print("RC_PREVIEW_GATES=opening_identity,starter_runtime,kpi_rival,first_field_test,preview_endpoint")
    return 0


if __name__ == "__main__":
    sys.exit(main())
