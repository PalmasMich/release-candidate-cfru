#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"
DEFAULT_MANIFEST = CONTENT / "tileset_art_manifest.json"
MAP_SPEC_ROOT = CONTENT / "map_specs"
PROFILE_PATH = CONTENT / "metatile_profiles.json"
EXPECTED_STAGES = (
    "visual_blockout",
    "tile_sheet",
    "palette",
    "metatiles",
    "collision",
    "integration",
    "runtime_smoke",
)
ALLOWED_STATUSES = {"pending", "bootstrap", "approved"}


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict:
    return load_json(path)


def load_map_specs() -> list[dict]:
    return [load_json(path) for path in sorted(MAP_SPEC_ROOT.glob("RC_*.json"))]


def validate(manifest: dict) -> list[str]:
    errors = []
    policy = manifest.get("policy", {})
    if policy.get("required_stage_order") != list(EXPECTED_STAGES):
        errors.append("required stage order does not match the V0.2 tileset pipeline")
    if policy.get("original_art_only") is not True:
        errors.append("tileset pipeline must require original art")
    if policy.get("bootstrap_profiles_are_not_final") is not True:
        errors.append("bootstrap metatile profiles must be explicitly non-final")

    contracts = manifest.get("tilesets", [])
    by_id = {item.get("id"): item for item in contracts}
    if len(by_id) != len(contracts):
        errors.append("tileset contract ids must be unique")

    specs = load_map_specs()
    expected_maps = {spec["id"] for spec in specs}
    mapped = {}
    for item in contracts:
        for map_id in item.get("maps", []):
            if map_id in mapped:
                errors.append(f"{map_id}: assigned to multiple tileset contracts")
            mapped[map_id] = item.get("id")
    if set(mapped) != expected_maps:
        errors.append("tileset manifest map coverage does not match Chapter 1")

    profiles = load_json(PROFILE_PATH)["profiles"]
    for spec in specs:
        map_id = spec["id"]
        declared = spec["art_contract"]["tileset"]
        if mapped.get(map_id) != declared:
            errors.append(f"{map_id}: map art contract does not match tileset manifest")
        profile_id = spec.get("metatile_profile")
        if profile_id not in profiles:
            errors.append(f"{map_id}: missing metatile profile {profile_id}")

    for tileset_id, item in by_id.items():
        stages = item.get("stages", {})
        if tuple(stages) != EXPECTED_STAGES:
            errors.append(f"{tileset_id}: stages are missing or out of order")
        invalid = {status for status in stages.values() if status not in ALLOWED_STATUSES}
        if invalid:
            errors.append(f"{tileset_id}: invalid stage statuses {sorted(invalid)}")
        if not item.get("required_motifs"):
            errors.append(f"{tileset_id}: missing required visual motifs")
        if item.get("production_ready"):
            if any(status != "approved" for status in stages.values()):
                errors.append(f"{tileset_id}: production_ready requires every stage approved")
            if not item.get("review_evidence"):
                errors.append(f"{tileset_id}: production_ready requires review evidence")
            for map_id in item.get("maps", []):
                spec = next((entry for entry in specs if entry["id"] == map_id), None)
                if spec and profiles[spec["metatile_profile"]].get("status") == "bootstrap_only":
                    errors.append(f"{tileset_id}: production_ready cannot use bootstrap metatiles")
    return errors


def overall_status(manifest: dict) -> str:
    tilesets = manifest.get("tilesets", [])
    if tilesets and all(item.get("production_ready") for item in tilesets):
        return "APPROVED"
    if any("bootstrap" in item.get("stages", {}).values() for item in tilesets):
        return "BOOTSTRAP"
    return "IN_PROGRESS"


def run(path: Path = DEFAULT_MANIFEST, *, require_approved: bool = False) -> int:
    manifest = load_manifest(path)
    errors = validate(manifest)
    for error in errors:
        print(f"RC_TILESET_ART_ERROR={error}")
    if errors:
        print("RC_TILESET_ART_STATUS=INVALID")
        return 1
    status = overall_status(manifest)
    print(f"RC_TILESET_ART_STATUS={status}")
    if require_approved and status != "APPROVED":
        print("RC_TILESET_ART_APPROVAL=BLOCKED")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the V0.2 original tileset production pipeline.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--require-approved", action="store_true")
    args = parser.parse_args()
    return run(args.manifest, require_approved=args.require_approved)


if __name__ == "__main__":
    raise SystemExit(main())
