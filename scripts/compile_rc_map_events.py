#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_SLOTS_PATH = ROOT / "content" / "cagliari_preview" / "map_slots.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def u16(value: int) -> bytes:
    if not 0 <= value <= 0xFFFF:
        raise ValueError(f"u16 out of range: {value}")
    return value.to_bytes(2, "little")


def placeholder(buf: bytearray, relocations: list[dict], relocation: dict, size: int = 4) -> None:
    relocation = dict(relocation)
    relocation["offset"] = len(buf)
    relocation["size"] = size
    relocations.append(relocation)
    buf.extend(b"\x00" * size)


def compile_object_events(spec: dict) -> dict:
    data = bytearray()
    relocations = []

    for obj in spec.get("objects", []):
        anchor = spec["anchors"][obj["anchor"]]
        local_id = int(obj["local_id"])
        gfx = int(obj["graphics"]["id"])
        movement = int(obj["movement_type"]["id"])
        elevation = int(obj.get("elevation", 3))

        data.extend(bytes([local_id, gfx, 0x00, 0x00]))
        data.extend(u16(anchor["x"]))
        data.extend(u16(anchor["y"]))
        data.extend(bytes([elevation, movement, 0x00, 0x00]))
        data.extend(u16(0))
        data.extend(u16(0))
        placeholder(
            data,
            relocations,
            {
                "kind": "script_pointer",
                "symbol": obj["script"],
                "owner": obj["id"],
            },
        )
        data.extend(u16(0))
        data.extend(b"\x00\x00")

    return {
        "count": len(spec.get("objects", [])),
        "size": len(data),
        "bytes_hex": data.hex(" "),
        "relocations": relocations,
    }


def compile_coord_events(spec: dict) -> dict:
    data = bytearray()
    relocations = []

    for coord in spec.get("coord_events", []):
        anchor = spec["anchors"][coord["anchor"]]
        elevation = int(coord.get("elevation", 3))
        var_id_raw = coord.get("var_id", "0x4001")
        var_id = int(var_id_raw, 0) if isinstance(var_id_raw, str) else int(var_id_raw)
        var_value = int(coord.get("var_value", 0))

        data.extend(u16(anchor["x"]))
        data.extend(u16(anchor["y"]))
        data.extend(bytes([elevation, 0x00]))
        data.extend(u16(var_id))
        data.extend(u16(var_value))
        data.extend(b"\x00\x00")
        placeholder(
            data,
            relocations,
            {
                "kind": "script_pointer",
                "symbol": coord["script"],
                "owner": coord["id"],
            },
        )

    return {
        "count": len(spec.get("coord_events", [])),
        "size": len(data),
        "bytes_hex": data.hex(" "),
        "relocations": relocations,
    }


def compile_bg_events(spec: dict) -> dict:
    data = bytearray()
    relocations = []

    for interaction in spec.get("interactions", []):
        anchor = spec["anchors"][interaction["anchor"]]
        elevation = int(interaction.get("elevation", 3))
        kind = int(interaction["bg_kind"]["id"])

        data.extend(u16(anchor["x"]))
        data.extend(u16(anchor["y"]))
        data.extend(bytes([elevation, kind]))
        data.extend(b"\x00\x00")
        placeholder(
            data,
            relocations,
            {
                "kind": "script_pointer",
                "symbol": interaction["script"],
                "owner": interaction["id"],
            },
        )

    return {
        "count": len(spec.get("interactions", [])),
        "size": len(data),
        "bytes_hex": data.hex(" "),
        "relocations": relocations,
    }


def compile_warps(spec: dict) -> dict:
    data = bytearray()
    relocations = []

    for warp in spec.get("warps", []):
        anchor = spec["anchors"][warp["anchor"]]
        elevation = int(warp.get("elevation", 3))
        warp_id = int(warp.get("warp_id", 0))

        data.extend(u16(anchor["x"]))
        data.extend(u16(anchor["y"]))
        data.extend(bytes([elevation, warp_id]))
        placeholder(
            data,
            relocations,
            {
                "kind": "map_id",
                "symbol": warp["target_map"],
                "target_anchor": warp["target_anchor"],
                "owner": warp["id"],
            },
            size=2,
        )

    return {
        "count": len(spec.get("warps", [])),
        "size": len(data),
        "bytes_hex": data.hex(" "),
        "relocations": relocations,
    }


def load_map_ids() -> dict[str, tuple[int, int]]:
    slots = load_json(MAP_SLOTS_PATH)["slots"]
    return {
        slot["rc_map"]: (int(slot["map_group"]), int(slot["map_num"]))
        for slot in slots
    }


def link_map_id_relocations(block: dict, map_ids: dict[str, tuple[int, int]]) -> bytes:
    data = bytearray.fromhex(block["bytes_hex"])
    for relocation in block.get("relocations", []):
        if relocation["kind"] != "map_id":
            continue
        symbol = relocation["symbol"]
        if symbol not in map_ids:
            raise ValueError(f"missing map slot for {symbol}")
        group, num = map_ids[symbol]
        offset = relocation["offset"]
        data[offset:offset + 2] = bytes([num & 0xFF, group & 0xFF])
    return bytes(data)


def compile_map_events(spec: dict) -> dict:
    objects = compile_object_events(spec)
    warps = compile_warps(spec)
    coord = compile_coord_events(spec)
    bg = compile_bg_events(spec)

    header = bytearray([
        objects["count"],
        warps["count"],
        coord["count"],
        bg["count"],
    ])
    header_relocations = []

    for kind, block in (
        ("object_events", objects),
        ("warp_events", warps),
        ("coord_events", coord),
        ("bg_events", bg),
    ):
        if block["count"] == 0:
            header.extend(b"\x00\x00\x00\x00")
        else:
            placeholder(
                header,
                header_relocations,
                {
                    "kind": "data_pointer",
                    "symbol": kind,
                },
            )

    return {
        "format": "RC_MAP_EVENTS_IR_V1",
        "map": spec["id"],
        "map_events_header": {
            "size": len(header),
            "bytes_hex": header.hex(" "),
            "relocations": header_relocations,
        },
        "object_events": objects,
        "warp_events": warps,
        "coord_events": coord,
        "bg_events": bg,
        "total_bytes": len(header) + objects["size"] + warps["size"] + coord["size"] + bg["size"],
    }


def compile_file(source: Path, output: Path | None = None) -> dict:
    ir = compile_map_events(load_json(source))
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(ir, indent=2) + "\n", encoding="utf-8")
    return ir


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile RC custom-map event structures into relocatable FireRed IR.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        ir = compile_file(args.source, args.output)
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"RC_MAP_EVENTS_INVALID: {exc}")
        return 1

    print(f"RC_MAP_EVENTS_VALID={ir['map']}")
    print(f"RC_MAP_EVENTS_BYTES={ir['total_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
