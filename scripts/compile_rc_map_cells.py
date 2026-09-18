#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "content" / "cagliari_preview" / "metatile_profiles.json"

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def encode_cell(metatile_id: int, collision: int, elevation: int) -> int:
    if not 0 <= metatile_id <= 0x3FF: raise ValueError("metatile out of range")
    if not 0 <= collision <= 3: raise ValueError("collision out of range")
    if not 0 <= elevation <= 15: raise ValueError("elevation out of range")
    return metatile_id | (collision << 10) | (elevation << 12)

def compile_cells(map_spec: dict, profile: dict) -> dict:
    roles = profile["semantic_roles"]
    legend = map_spec["legend"]
    out = bytearray()
    role_counts = {}
    for row in map_spec["layout"]:
        for ch in row:
            role = legend[ch]
            if role not in roles:
                raise ValueError(f"no metatile mapping for role {role}")
            m = roles[role]
            value = encode_cell(int(m["metatile_id"],16), int(m["collision"]), int(m["elevation"]))
            out.extend(value.to_bytes(2,"little"))
            role_counts[role] = role_counts.get(role,0)+1
    border = roles["wall"]
    border_value = encode_cell(int(border["metatile_id"],16), int(border["collision"]), int(border["elevation"]))
    border_blob = border_value.to_bytes(2,"little") * 4
    return {
      "format":"RC_MAP_CELLS_IR_V1",
      "map":map_spec["id"],
      "profile":"RC_DELIVERY_HUB_HOUSE2_BOOTSTRAP",
      "map_bytes":len(out),
      "border_bytes":len(border_blob),
      "map_hex":out.hex(" "),
      "border_hex":border_blob.hex(" "),
      "role_counts":role_counts
    }

def compile_file(source: Path, output: Path|None=None) -> dict:
    spec=load_json(source)
    profiles=load_json(PROFILE_PATH)["profiles"]
    profile_id=spec.get("metatile_profile")
    if profile_id not in profiles:
        raise ValueError(f"unknown metatile profile {profile_id}")
    ir=compile_cells(spec, profiles[profile_id])
    ir["profile"]=profile_id
    if output:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(ir,indent=2)+"\n",encoding="utf-8")
    return ir

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    try: ir=compile_file(a.source,a.output)
    except Exception as e:
        print(f"RC_MAP_CELLS_INVALID: {e}"); return 1
    print(f"RC_MAP_CELLS_VALID={ir['map']}")
    print(f"RC_MAP_CELLS_BYTES={ir['map_bytes']}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
