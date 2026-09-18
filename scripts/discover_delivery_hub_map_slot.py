#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

GBA_ROM_BASE = 0x08000000
MAP_HEADER_SIZE = 0x1C

# Route19_UnusedHouse vanilla contract from pret/pokefirered:
# music MUS_ROUTE3=293, MAPSEC_ROUTE_19=119, WEATHER_NONE=0,
# MAP_TYPE_INDOOR=8, no cycling/escaping/running/map name, floor 0,
# MAP_BATTLE_SCENE_NORMAL=0.
MUSIC_ROUTE3 = 293
MAPSEC_ROUTE19 = 119
MAP_TYPE_INDOOR = 8
WEATHER_NONE = 0
BATTLE_SCENE_NORMAL = 0

TAIL_OFFSET = 0x10
TAIL_SIZE = 0x0C


def is_rom_pointer(value: int, rom_size: int) -> bool:
    if value == 0:
        return False
    if not (GBA_ROM_BASE <= value < GBA_ROM_BASE + rom_size):
        return False
    return (value - GBA_ROM_BASE) % 4 == 0


def parse_header(data: bytes, offset: int) -> dict:
    if offset < 0 or offset + MAP_HEADER_SIZE > len(data):
        raise ValueError("map header offset out of bounds")

    def u32(pos: int) -> int:
        return int.from_bytes(data[offset + pos:offset + pos + 4], "little")

    def u16(pos: int) -> int:
        return int.from_bytes(data[offset + pos:offset + pos + 2], "little")

    flags = data[offset + 0x19]
    return {
        "offset": offset,
        "layout_ptr": u32(0x00),
        "events_ptr": u32(0x04),
        "scripts_ptr": u32(0x08),
        "connections_ptr": u32(0x0C),
        "music": u16(0x10),
        "layout_id": u16(0x12),
        "mapsec": data[offset + 0x14],
        "cave": data[offset + 0x15],
        "weather": data[offset + 0x16],
        "map_type": data[offset + 0x17],
        "biking_allowed": data[offset + 0x18],
        "flags": flags,
        "allow_escaping": flags & 0x01,
        "allow_running": (flags >> 1) & 0x01,
        "show_map_name": flags >> 2,
        "floor_num": int.from_bytes(bytes([data[offset + 0x1A]]), "little", signed=True),
        "battle_type": data[offset + 0x1B],
    }


def matches_route19_unused_house(header: dict, rom_size: int) -> bool:
    return all(
        (
            is_rom_pointer(header["layout_ptr"], rom_size),
            is_rom_pointer(header["events_ptr"], rom_size),
            is_rom_pointer(header["scripts_ptr"], rom_size),
            header["connections_ptr"] == 0,
            header["music"] == MUSIC_ROUTE3,
            header["mapsec"] == MAPSEC_ROUTE19,
            header["cave"] == 0,
            header["weather"] == WEATHER_NONE,
            header["map_type"] == MAP_TYPE_INDOOR,
            header["biking_allowed"] == 0,
            header["allow_escaping"] == 0,
            header["allow_running"] == 0,
            header["show_map_name"] == 0,
            header["floor_num"] == 0,
            header["battle_type"] == BATTLE_SCENE_NORMAL,
        )
    )


def discover_candidates(data: bytes) -> list[dict]:
    candidates = []

    # Search the fixed tail first instead of parsing every aligned ROM word.
    # MapLayoutId at 0x12 is intentionally excluded because it is not needed
    # to identify this unused slot.
    fixed_tail = bytes([
        MAPSEC_ROUTE19,
        0x00,  # cave / requires flash
        WEATHER_NONE,
        MAP_TYPE_INDOOR,
        0x00,  # biking
        0x00,  # escaping/running/show-name flags
        0x00,  # floor
        BATTLE_SCENE_NORMAL,
    ])

    start = 0
    seen = set()
    while True:
        tail_pos = data.find(fixed_tail, start)
        if tail_pos < 0:
            break
        start = tail_pos + 1

        offset = tail_pos - 0x14
        if offset < 0 or offset % 4 != 0 or offset in seen:
            continue
        seen.add(offset)

        if offset + MAP_HEADER_SIZE > len(data):
            continue
        if int.from_bytes(data[offset + 0x10:offset + 0x12], "little") != MUSIC_ROUTE3:
            continue

        header = parse_header(data, offset)
        if matches_route19_unused_house(header, len(data)):
            candidates.append(header)

    return candidates


def analyze_rom(data: bytes) -> dict:
    candidates = discover_candidates(data)
    return {
        "slot": "MAP_ROUTE19_UNUSED_HOUSE",
        "map_group": 27,
        "map_num": 0,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "safe_to_repoint": len(candidates) == 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Locate the unique vanilla Route19_UnusedHouse MapHeader in a private FireRed/CFRU ROM."
    )
    parser.add_argument("rom", type=Path)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    if not args.rom.is_file():
        print(f"ERROR: ROM not found: {args.rom}")
        return 1

    report = analyze_rom(args.rom.read_bytes())
    rendered = json.dumps(report, indent=2)
    print(rendered)

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")

    if report["candidate_count"] == 0:
        print("RC_DELIVERY_HUB_SLOT=NOT_FOUND")
        return 2
    if not report["safe_to_repoint"]:
        print("RC_DELIVERY_HUB_SLOT=AMBIGUOUS")
        return 3

    header = report["candidates"][0]
    print(f"RC_DELIVERY_HUB_SLOT=READY:0x{header['offset']:X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
