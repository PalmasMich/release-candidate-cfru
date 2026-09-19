#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "content" / "cagliari_preview" / "script_specs" / "RC_DELIVERY_HUB.json"
SPECIES = ROOT / "include" / "constants" / "species.h"
LEARNSETS = ROOT / "src" / "Tables" / "level_up_learnsets.c"
DEFAULT_DPE_ROOT = ROOT.parent / "release-candidate-dpe"

STARTERS = {
    "RC_SCRIPT_STARTER_TARTREK": ("SPECIES_RC_TURTLE_01", "sRCTartrekLevelUpLearnset"),
    "RC_SCRIPT_STARTER_FROBYTE": ("SPECIES_RC_FROG_01", "sRCFrobyteLevelUpLearnset"),
    "RC_SCRIPT_STARTER_EMBERFOX": ("SPECIES_RC_FIREFOX_01", "sRCEmberfoxLevelUpLearnset"),
}

RC_SPECIES_IDS = {
    "SPECIES_RC_TURTLE_01": 0x050E,
    "SPECIES_RC_FROG_01": 0x050F,
    "SPECIES_RC_FIREFOX_01": 0x0510,
    "SPECIES_RC_CAGLIARI_WILD_01": 0x0511,
}


def load_dpe_overlay(dpe_root: Path):
    path = dpe_root / "scripts" / "apply_release_candidate_overlay.py"
    spec = importlib.util.spec_from_file_location("rc_dpe_overlay_validator", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load DPE overlay module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_dpe_contract(dpe_root: Path) -> list[str]:
    errors = []
    dpe_root = Path(dpe_root).resolve()
    required = (
        dpe_root / "release_candidate" / "preview_species.json",
        dpe_root / "include" / "release_candidate_species.h",
        dpe_root / "include" / "pokedex.h",
        dpe_root / "scripts" / "apply_release_candidate_overlay.py",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        return ["missing DPE runtime contract file " + path for path in missing]

    try:
        overlay = load_dpe_overlay(dpe_root)
        species = overlay.load_species()
    except (ImportError, OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot load DPE runtime contract: {exc}"]

    by_symbol = {item.get("id"): item for item in species}
    if set(by_symbol) != set(RC_SPECIES_IDS):
        errors.append("DPE active RC species set does not match CFRU runtime contract")

    dpe_species_header = required[1].read_text(encoding="utf-8")
    dpe_pokedex_header = required[2].read_text(encoding="utf-8")
    dex_values = []
    for symbol, expected_id in RC_SPECIES_IDS.items():
        item = by_symbol.get(symbol)
        if item is None:
            continue
        species_match = re.search(
            rf"^#define\s+{re.escape(symbol)}\s+0x([0-9A-Fa-f]+)\s*$",
            dpe_species_header,
            re.MULTILINE,
        )
        if species_match is None or int(species_match.group(1), 16) != expected_id:
            errors.append(f"DPE species id mismatch for {symbol}")

        dex_id = item.get("national_dex")
        dex_symbol = item.get("national_dex_symbol")
        if not isinstance(dex_id, int) or dex_id <= 0 or not dex_symbol:
            errors.append(f"missing National Dex mapping for {symbol}")
            continue
        dex_values.append(dex_id)
        dex_match = re.search(
            rf"^#define\s+{re.escape(dex_symbol)}\s+(\d+)\s*$",
            dpe_species_header,
            re.MULTILINE,
        )
        if dex_match is None or int(dex_match.group(1)) != dex_id:
            errors.append(f"DPE National Dex constant mismatch for {symbol}")

        pokedex = item.get("pokedex")
        if not isinstance(pokedex, dict) or not all(
            pokedex.get(key) for key in ("category", "height", "weight", "description_symbol", "description")
        ):
            errors.append(f"missing Pokédex record for {symbol}")

    if len(dex_values) != len(set(dex_values)):
        errors.append("National Dex ids are not unique")

    if "#define FINAL_DEX_ENTRY NATIONAL_DEX_RC_MISTRILLO" not in re.sub(r"\s+", " ", dpe_pokedex_header):
        errors.append("DPE FINAL_DEX_ENTRY does not include active RC species")

    try:
        rendered_mapping = overlay.render_species_to_pokedex(species)
        rendered_data = overlay.render_pokedex_data(species)
        rendered_strings = overlay.render_pokedex_strings(species)
        required_targets = {
            overlay.SPECIES_TO_POKEDEX,
            overlay.POKEDEX_DATA,
            overlay.POKEDEX_STRINGS,
        }
        if not required_targets.issubset(set(overlay.TARGETS)):
            errors.append("DPE overlay does not back up every custom Pokédex target")
        for item in species:
            if item.get("national_dex_symbol") and item.get("id"):
                expected = f"[{item['id']} - 1] = {item['national_dex_symbol']}"
                if expected not in rendered_mapping:
                    errors.append(f"missing rendered Species -> National Dex entry for {item['id']}")
            pokedex = item.get("pokedex", {})
            description_symbol = pokedex.get("description_symbol")
            if item.get("national_dex_symbol") and f"[{item['national_dex_symbol']}] =" not in rendered_data:
                errors.append(f"missing rendered Pokédex data for {item.get('id')}")
            if description_symbol and f"#org @{description_symbol}" not in rendered_strings:
                errors.append(f"missing rendered Pokédex description for {item.get('id')}")
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        errors.append(f"incomplete DPE Pokédex overlay: {exc}")

    return errors

def validate(dpe_root: Path = DEFAULT_DPE_ROOT) -> list[str]:
    errors = []
    hub = json.loads(HUB.read_text(encoding="utf-8"))
    scripts = {s["id"]: s for s in hub["scripts"]}
    species_text = SPECIES.read_text(encoding="utf-8")
    learnset_text = LEARNSETS.read_text(encoding="utf-8")
    active_learnset_text = re.sub(r"/\\*.*?\\*/", "", learnset_text, flags=re.DOTALL)

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
        if active_entry not in active_learnset_text:
            errors.append(f"missing active learnset table entry {active_entry}")

    if len(ids) == len(STARTERS):
        ordered = [ids[x[0]] for x in STARTERS.values()]
        if len(set(ordered)) != len(ordered):
            errors.append("starter species ids are not unique")
        if ordered != sorted(ordered):
            errors.append("starter species ids are not monotonically assigned")

    errors.extend(validate_dpe_contract(dpe_root))
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Release Candidate starter runtime wiring.")
    parser.add_argument("--dpe-path", type=Path, default=DEFAULT_DPE_ROOT)
    args = parser.parse_args()
    errors = validate(args.dpe_path)
    if errors:
        print("RC_STARTER_RUNTIME=FAILED")
        for error in errors:
            print(f"RC_STARTER_ERROR={error}")
        return 1
    print("RC_STARTER_RUNTIME=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
