#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = ROOT / "content" / "cagliari_preview"
MAP_SPEC_ROOT = CONTENT_ROOT / "map_specs"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_spec(spec: dict) -> None:
    map_id = spec.get("id")
    require(isinstance(map_id, str) and map_id.startswith("RC_"), "map id must be an RC_* string")
    require(spec.get("chapter") == "RC_CHAPTER_01_CAGLIARI", f"{map_id}: wrong chapter")
    require(spec.get("status") == "permanent", f"{map_id}: custom map spec must be permanent")

    dims = spec.get("dimensions", {})
    width = dims.get("width")
    height = dims.get("height")
    require(isinstance(width, int) and width > 0, f"{map_id}: invalid width")
    require(isinstance(height, int) and height > 0, f"{map_id}: invalid height")

    legend = spec.get("legend", {})
    require(legend, f"{map_id}: missing legend")
    layout = spec.get("layout", [])
    require(len(layout) == height, f"{map_id}: layout height {len(layout)} != {height}")
    for y, row in enumerate(layout):
        require(len(row) == width, f"{map_id}: row {y} width {len(row)} != {width}")
        unknown = set(row) - set(legend)
        require(not unknown, f"{map_id}: row {y} contains unknown symbols {sorted(unknown)}")

    collision = spec.get("collision", {})
    blocked = set(collision.get("blocked_roles", []))
    walkable = set(collision.get("walkable_roles", []))
    roles = set(legend.values())
    require(not (blocked & walkable), f"{map_id}: collision roles overlap")
    require(roles <= blocked | walkable, f"{map_id}: collision rules do not cover every legend role")

    anchors = spec.get("anchors", {})
    require("player_spawn" in anchors, f"{map_id}: missing player_spawn")
    anchor_positions = {}
    for name, point in anchors.items():
        x, y = point.get("x"), point.get("y")
        require(isinstance(x, int) and isinstance(y, int), f"{map_id}: anchor {name} needs integer x/y")
        require(0 <= x < width and 0 <= y < height, f"{map_id}: anchor {name} out of bounds")
        role = legend[layout[y][x]]
        require(role in walkable, f"{map_id}: anchor {name} is on blocked role {role}")
        anchor_positions[name] = (x, y)

    for obj in spec.get("objects", []):
        anchor = obj.get("anchor")
        require(anchor in anchors, f"{map_id}: object {obj.get('id')} references unknown anchor {anchor}")
        require(obj.get("script"), f"{map_id}: object {obj.get('id')} has no script")

    for interaction in spec.get("interactions", []):
        anchor = interaction.get("anchor")
        require(anchor in anchors, f"{map_id}: interaction {interaction.get('id')} has unknown anchor {anchor}")
        require(
            str(interaction.get("script", "")).startswith("RC_SCRIPT_"),
            f"{map_id}: interaction {interaction.get('id')} has no compiled script binding",
        )

    for coord in spec.get("coord_events", []):
        anchor = coord.get("anchor")
        require(anchor in anchors, f"{map_id}: coord event {coord.get('id')} has unknown anchor {anchor}")
        require(
            str(coord.get("script", "")).startswith("RC_SCRIPT_"),
            f"{map_id}: coord event {coord.get('id')} has no compiled script binding",
        )
        var_id = coord.get("var_id")
        if isinstance(var_id, str):
            var_id = int(var_id, 0)
        require(isinstance(var_id, int) and 0 <= var_id <= 0xFFFF, f"{map_id}: invalid coord-event var id")

    for warp in spec.get("warps", []):
        anchor = warp.get("anchor")
        require(anchor in anchors, f"{map_id}: warp {warp.get('id')} has unknown anchor {anchor}")
        require(warp.get("target_map", "").startswith("RC_"), f"{map_id}: warp target must be RC_*")
        require(warp.get("target_anchor"), f"{map_id}: warp {warp.get('id')} has no target anchor")

    require(
        spec.get("art_contract", {}).get("tileset", "").startswith("RC_TILESET_"),
        f"{map_id}: permanent map must declare a custom RC tileset",
    )


def compile_spec(spec: dict) -> dict:
    validate_spec(spec)

    legend = spec["legend"]
    collision = spec["collision"]
    blocked = set(collision["blocked_roles"])
    width = spec["dimensions"]["width"]
    height = spec["dimensions"]["height"]

    role_grid = [[legend[ch] for ch in row] for row in spec["layout"]]
    collision_grid = [
        [1 if role in blocked else 0 for role in row]
        for row in role_grid
    ]

    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode("utf-8")
    source_sha256 = hashlib.sha256(canonical).hexdigest()

    return {
        "format": "RC_MAP_IR_V1",
        "id": spec["id"],
        "chapter": spec["chapter"],
        "dimensions": {"width": width, "height": height},
        "role_grid": role_grid,
        "collision_grid": collision_grid,
        "anchors": spec["anchors"],
        "objects": spec.get("objects", []),
        "interactions": spec.get("interactions", []),
        "coord_events": spec.get("coord_events", []),
        "warps": spec.get("warps", []),
        "tileset_contract": spec["art_contract"]["tileset"],
        "source_sha256": source_sha256,
        "rom_ready": False,
        "rom_blockers": [
            "verified primary/secondary tileset pointers",
            "verified metatile ids for every semantic role",
            "allocated map layout/header/events/script space",
            "verified map-group/map-number insertion slot",
        ],
    }


def compile_file(source: Path, output: Path | None = None) -> dict:
    spec = load_json(source)
    ir = compile_spec(spec)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(ir, indent=2) + "\n", encoding="utf-8")
    return ir


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and compile a Release Candidate custom map spec.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        ir = compile_file(args.source, args.output)
    except (FileNotFoundError, ValueError) as exc:
        print(f"RC_MAP_INVALID: {exc}")
        return 1

    print(f"RC_MAP_VALID={ir['id']}")
    print(f"RC_MAP_FORMAT={ir['format']}")
    print(f"RC_MAP_SOURCE_SHA256={ir['source_sha256']}")
    print("RC_MAP_ROM_READY=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
