#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "content" / "cagliari_preview" / "script_specs" / "RC_DELIVERY_HUB.json"
SPECIES = ROOT / "include" / "constants" / "species.h"
LEARNSETS = ROOT / "src" / "Tables" / "level_up_learnsets.c"

STARTERS = {
    "RC_SCRIPT_STARTER_TARTREK": ("SPECIES_RC_TURTLE_01", "sRCTartrekLevelUpLearnset"),
    "RC_SCRIPT_STARTER_FROBYTE": ("SPECIES_RC_FROG_01", "sRCFrobyteLevelUpLearnset"),
    "RC_SCRIPT_STARTER_EMBERFOX": ("SPECIES_RC_FIREFOX_01", "sRCEmberfoxLevelUpLearnset"),
}

def validate() -> list[str]:
    errors = []
    hub = json.loads(HUB.read_text(encoding="utf-8"))
    scripts = {s["id"]: s for s in hub["scripts"]}
    species_text = SPECIES.read_text(encoding="utf-8")
    learnset_text = LEARNSETS.read_text(encoding="utf-8")

    ids = {}
    for script_id, (species_name, learnset_symbol) in STARTERS.items():
        script = scripts.get(script_id)
        if script is None:
            errors.append(f"missing starter script {script_id}")
            continue

        givemon = [op for op in script["ops"] if op.get("op") == "givemon"]
        if len(givemon) != 1:
            errors.append(f"{script_id} must contain exactly one givemon")
        elif givemon[0].get("species") != species_name:
            errors.append(f"{script_id} gives {givemon[0].get('species')} instead of {species_name}")

        m = re.search(rf"^#define\s+{re.escape(species_name)}\s+0x([0-9A-Fa-f]+)\s*$", species_text, re.MULTILINE)
        if not m:
            errors.append(f"missing species constant {species_name}")
        else:
            ids[species_name] = int(m.group(1), 16)

        if f"static const struct LevelUpMove {learnset_symbol}[]" not in learnset_text:
            errors.append(f"missing learnset definition {learnset_symbol}")

        active_entry = f"[{species_name}] = {learnset_symbol},"
        if active_entry not in learnset_text:
            errors.append(f"missing learnset table entry {active_entry}")

    if len(ids) == len(STARTERS):
        ordered = [ids[x[0]] for x in STARTERS.values()]
        if len(set(ordered)) != len(ordered):
            errors.append("starter species ids are not unique")
        if ordered != sorted(ordered):
            errors.append("starter species ids are not monotonically assigned")

    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Release Candidate starter runtime wiring.")
    parser.parse_args()
    errors = validate()
    if errors:
        print("RC_STARTER_RUNTIME=FAILED")
        for error in errors:
            print(f"RC_STARTER_ERROR={error}")
        return 1
    print("RC_STARTER_RUNTIME=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
