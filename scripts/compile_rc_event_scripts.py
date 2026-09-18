#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"
FLAGS_PATH = CONTENT / "flags.json"
SPECIES_HEADER = ROOT / "include" / "constants" / "species.h"

OP_END = 0x02
OP_GOTO_IF = 0x06
OP_CALLSTD = 0x09
OP_LOADWORD = 0x0F
OP_SETFLAG = 0x29
OP_CHECKFLAG = 0x2B
OP_WARP = 0x39
OP_FACEPLAYER = 0x5A
OP_TRAINERBATTLE = 0x5C
OP_LOCKALL = 0x69
OP_LOCK = 0x6A
OP_RELEASEALL = 0x6B
OP_RELEASE = 0x6C
OP_GIVEMON = 0x79

ITEM_NONE = 0
TRUE = 1
FALSE = 0


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def load_flag_ids() -> dict[str, int]:
    data = load_json(FLAGS_PATH)
    return {name: int(value, 16) for name, value in data["flags"].items()}


def load_species_ids() -> dict[str, int]:
    text = SPECIES_HEADER.read_text(encoding="utf-8")
    result = {}
    pattern = re.compile(r"^#define\s+(SPECIES_RC_[A-Z0-9_]+)\s+0x([0-9A-Fa-f]+)\s*$", re.MULTILINE)
    for name, hex_value in pattern.findall(text):
        result[name] = int(hex_value, 16)
    return result


def emit_u16(buf: bytearray, value: int) -> None:
    if not 0 <= value <= 0xFFFF:
        raise ValueError(f"u16 out of range: {value}")
    buf.extend(value.to_bytes(2, "little"))


def emit_u16_placeholder(buf: bytearray, relocations: list[dict], relocation: dict) -> None:
    relocation = dict(relocation)
    relocation["offset"] = len(buf)
    relocation["size"] = 2
    relocations.append(relocation)
    buf.extend(b"\x00\x00")


def emit_u32_placeholder(buf: bytearray, relocations: list[dict], relocation: dict) -> None:
    relocation = dict(relocation)
    relocation["offset"] = len(buf)
    relocation["size"] = 4
    relocations.append(relocation)
    buf.extend(b"\x00\x00\x00\x00")


def compile_script(script: dict, flags: dict[str, int], species: dict[str, int]) -> dict:
    buf = bytearray()
    relocations = []
    labels = {}

    for entry in script["ops"]:
        if "label" in entry:
            label = entry["label"]
            if label in labels:
                raise ValueError(f"{script['id']}: duplicate label {label}")
            labels[label] = len(buf)
            continue

        op = entry.get("op")

        if op == "end":
            buf.append(OP_END)
        elif op == "lockall":
            buf.append(OP_LOCKALL)
        elif op == "lock":
            buf.append(OP_LOCK)
        elif op == "releaseall":
            buf.append(OP_RELEASEALL)
        elif op == "release":
            buf.append(OP_RELEASE)
        elif op == "faceplayer":
            buf.append(OP_FACEPLAYER)
        elif op == "checkflag":
            name = entry["flag"]
            if name not in flags:
                raise ValueError(f"{script['id']}: unknown flag {name}")
            buf.append(OP_CHECKFLAG)
            emit_u16(buf, flags[name])
        elif op == "setflag":
            name = entry["flag"]
            if name not in flags:
                raise ValueError(f"{script['id']}: unknown flag {name}")
            buf.append(OP_SETFLAG)
            emit_u16(buf, flags[name])
        elif op == "goto_if":
            buf.append(OP_GOTO_IF)
            buf.append(TRUE if entry["condition"] else FALSE)
            emit_u32_placeholder(
                buf,
                relocations,
                {"kind": "internal_label", "label": entry["label"]},
            )
        elif op == "msgbox":
            buf.extend((OP_LOADWORD, 0x00))
            emit_u32_placeholder(
                buf,
                relocations,
                {"kind": "dialogue", "symbol": entry["dialogue"]},
            )
            buf.extend((OP_CALLSTD, int(entry.get("type", 4))))
        elif op == "warp":
            x = int(entry["x"])
            y = int(entry["y"])
            if not 0 <= x <= 0xFFFF or not 0 <= y <= 0xFFFF:
                raise ValueError(f"{script['id']}: invalid warp coordinates ({x}, {y})")
            buf.append(OP_WARP)
            emit_u16_placeholder(
                buf,
                relocations,
                {"kind": "map_id", "symbol": entry["target_map"]},
            )
            buf.append(int(entry.get("warp_id", 0xFF)) & 0xFF)
            emit_u16(buf, x)
            emit_u16(buf, y)
        elif op == "trainerbattle_single":
            trainer_id = int(entry["trainer_id"])
            local_id = int(entry.get("local_id", 0))
            if not 0 <= trainer_id <= 0xFFFF:
                raise ValueError(f"{script['id']}: invalid trainer id {trainer_id}")
            if not 0 <= local_id <= 0xFFFF:
                raise ValueError(f"{script['id']}: invalid trainer local id {local_id}")
            buf.extend((OP_TRAINERBATTLE, 0x00))
            emit_u16(buf, trainer_id)
            emit_u16(buf, local_id)
            emit_u32_placeholder(
                buf,
                relocations,
                {"kind": "dialogue", "symbol": entry["intro_dialogue"]},
            )
            emit_u32_placeholder(
                buf,
                relocations,
                {"kind": "dialogue", "symbol": entry["defeat_dialogue"]},
            )
        elif op == "givemon":
            species_name = entry["species"]
            if species_name not in species:
                raise ValueError(f"{script['id']}: unknown species {species_name}")
            level = int(entry["level"])
            if not 1 <= level <= 100:
                raise ValueError(f"{script['id']}: invalid level {level}")
            item = int(entry.get("item", ITEM_NONE))
            buf.append(OP_GIVEMON)
            emit_u16(buf, species[species_name])
            buf.append(level)
            emit_u16(buf, item)
            buf.extend(b"\x00" * 9)
        else:
            raise ValueError(f"{script['id']}: unsupported op {op}")

    for relocation in relocations:
        if relocation["kind"] == "internal_label":
            label = relocation["label"]
            if label not in labels:
                raise ValueError(f"{script['id']}: unknown label {label}")
            relocation["target_offset"] = labels[label]

    return {
        "id": script["id"],
        "size": len(buf),
        "bytes_hex": buf.hex(" "),
        "labels": labels,
        "relocations": relocations,
    }


def compile_spec(spec: dict) -> dict:
    flags = load_flag_ids()
    species = load_species_ids()

    scripts = [compile_script(script, flags, species) for script in spec["scripts"]]
    ids = [script["id"] for script in scripts]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate event-script ids")

    return {
        "format": "RC_EVENT_SCRIPT_IR_V1",
        "map": spec["map"],
        "scripts": scripts,
    }


def link_script(
    script_ir: dict,
    base_address: int,
    dialogue_addresses: dict[str, int],
    map_ids: dict[str, tuple[int, int]] | None = None,
) -> bytes:
    data = bytearray.fromhex(script_ir["bytes_hex"])

    for relocation in script_ir["relocations"]:
        offset = relocation["offset"]
        if relocation["kind"] == "internal_label":
            value = base_address + relocation["target_offset"]
        elif relocation["kind"] == "dialogue":
            symbol = relocation["symbol"]
            if symbol not in dialogue_addresses:
                raise ValueError(f"missing dialogue address for {symbol}")
            value = dialogue_addresses[symbol]
        elif relocation["kind"] == "map_id":
            symbol = relocation["symbol"]
            if map_ids is None or symbol not in map_ids:
                raise ValueError(f"missing map id for {symbol}")
            group, num = map_ids[symbol]
            data[offset:offset + 2] = bytes([group & 0xFF, num & 0xFF])
            continue
        else:
            raise ValueError(f"unsupported relocation kind {relocation['kind']}")

        data[offset:offset + 4] = int(value).to_bytes(4, "little")

    return bytes(data)


def compile_file(source: Path, output: Path | None = None) -> dict:
    ir = compile_spec(load_json(source))
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(ir, indent=2) + "\n", encoding="utf-8")
    return ir


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile RC event scripts into relocatable FireRed bytecode IR.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        ir = compile_file(args.source, args.output)
    except (FileNotFoundError, ValueError) as exc:
        print(f"RC_EVENT_SCRIPTS_INVALID: {exc}")
        return 1

    print(f"RC_EVENT_SCRIPTS_VALID={ir['map']}")
    print(f"RC_EVENT_SCRIPT_COUNT={len(ir['scripts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
