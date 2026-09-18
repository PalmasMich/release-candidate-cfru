#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

TARTREK_SPECIES_ID = 0x050E
MISTRILLO_SPECIES_ID = 0x0511

# FireRed USA 1.0 Oak's Lab starter script sequence:
# setvar 0x4001, 0x0000          (starter choice index)
# setvar 0x4002, 0x0001          (player species: Bulbasaur)
# setvar 0x4003, 0x0004          (rival species: Charmander)
# setvar 0x4004, 0x0007          (ball/object id)
#
# CFRU leaves this script region intact in the current Preview build.
BULBASAUR_STARTER_SIGNATURE = bytes.fromhex(
    "16 01 40 00 00 "
    "16 02 40 01 00 "
    "16 03 40 04 00 "
    "16 04 40 07 00"
)
PLAYER_SPECIES_VALUE_OFFSET = 8

ROUTE1_WILD_SIGNATURE = bytes.fromhex(
    "03 03 10 00 "
    "03 03 13 00 "
    "03 03 10 00 "
    "03 03 13 00 "
    "02 02 10 00 "
    "02 02 13 00 "
    "03 03 10 00 "
    "03 03 13 00 "
    "04 04 10 00 "
    "04 04 13 00 "
    "05 05 10 00 "
    "04 04 13 00"
)
ROUTE1_PIDGEY_RECORDS = (0, 2, 4, 6, 8, 10)

CHARMAP = {
    **{chr(ord("A") + i): 0xBB + i for i in range(26)},
    **{chr(ord("a") + i): 0xD5 + i for i in range(26)},
    " ": 0x00,
    "!": 0xAB,
    "?": 0xAC,
    ".": 0xAD,
    "-": 0xAE,
    ",": 0xB8,
    ":": 0xF0,
    "'": 0xB4,
    "é": 0x1B,
    "\n": 0xFE,
}


def encode_text(text: str) -> bytes:
    return bytes(CHARMAP[ch] for ch in text)


VISIBLE_TEXT_REPLACEMENTS = (
    (
        encode_text("Welcome to the world of POKéMON!"),
        encode_text("Welcome to Release Candidate!"),
    ),
    (
        encode_text("My name is OAK."),
        encode_text("I'm your Lead."),
    ),
    (
        encode_text("People affectionately refer to me"),
        encode_text("They call me Delivery Lead"),
    ),
    (
        encode_text("as the POKéMON PROFESSOR."),
        encode_text("on this project."),
    ),
    (
        encode_text("I see! BULBASAUR is your choice."),
        encode_text("TARTREK is your new partner!"),
    ),
    (
        encode_text("It's very easy to raise."),
        encode_text("First task starts now!"),
    ),
    (
        encode_text("Come on, I'll take you on!"),
        encode_text("KPI check: show velocity!"),
    ),
    (
        encode_text("PALLET TOWN\nShades of your journey await!"),
        encode_text("CAGLIARI\nFirst sprint starts here!"),
    ),
    (
        encode_text("ROUTE 1\nPALLET TOWN - VIRIDIAN CITY"),
        encode_text("PORT LINK\nCAGLIARI - MARINA PORTO"),
    ),
)

MAP_NAME_REPLACEMENT = (
    encode_text("PALLET TOWN") + b"\xFF" + encode_text("VIRIDIAN CITY") + b"\xFF",
    encode_text("CAGLIARI") + b"\xFF" + (b"\x00" * 3) + encode_text("MARINA PORTO") + b"\x00\xFF",
)

LAB_SIGN_REPLACEMENT = (
    b"\xCA\xC9\xC5\x1B\xC7\xC9\xC8\x00\xCC\xBF\xCD\xBF\xBB\xCC\xBD\xC2\x00\xC6\xBB\xBC",
    encode_text("DELIVERY HUB"),
)


def patch_tartrek_starter(data: bytearray) -> tuple[bytearray, int]:
    occurrences = []
    start = 0
    while True:
        pos = data.find(BULBASAUR_STARTER_SIGNATURE, start)
        if pos < 0:
            break
        occurrences.append(pos)
        start = pos + 1

    if len(occurrences) != 1:
        raise ValueError(
            "Expected exactly one FireRed Bulbasaur starter script signature, "
            f"found {len(occurrences)}."
        )

    pos = occurrences[0]
    species_bytes = TARTREK_SPECIES_ID.to_bytes(2, "little")
    value_pos = pos + PLAYER_SPECIES_VALUE_OFFSET
    data[value_pos:value_pos + 2] = species_bytes
    return data, 1


def _replace_size_preserving(data: bytearray, old: bytes, new: bytes, *, expected: int | None = None) -> int:
    if len(new) > len(old):
        raise ValueError("Replacement text cannot exceed the source byte length.")

    positions = []
    start = 0
    while True:
        pos = data.find(old, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 1

    if expected is not None and len(positions) != expected:
        raise ValueError(f"Expected {expected} occurrence(s), found {len(positions)}.")

    replacement = new + (b"\x00" * (len(old) - len(new)))
    for pos in positions:
        data[pos:pos + len(old)] = replacement
    return len(positions)


def patch_route1_wild_encounters(data: bytearray) -> bytearray:
    positions = []
    start = 0
    while True:
        pos = data.find(ROUTE1_WILD_SIGNATURE, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 1

    if len(positions) != 1:
        raise ValueError(
            "Expected exactly one FireRed Route 1 wild encounter signature, "
            f"found {len(positions)}."
        )

    base = positions[0]
    species_bytes = MISTRILLO_SPECIES_ID.to_bytes(2, "little")
    for record in ROUTE1_PIDGEY_RECORDS:
        species_pos = base + (record * 4) + 2
        data[species_pos:species_pos + 2] = species_bytes
    return data


def patch_visible_preview_text(data: bytearray) -> bytearray:
    for old, new in VISIBLE_TEXT_REPLACEMENTS:
        _replace_size_preserving(data, old, new, expected=1)

    old_city, new_city = MAP_NAME_REPLACEMENT
    if len(old_city) != len(new_city):
        raise ValueError("Map-name replacement must preserve byte length.")
    _replace_size_preserving(data, old_city, new_city, expected=1)

    old_lab, new_lab = LAB_SIGN_REPLACEMENT
    # The phrase appears in a few places; only the first occurrence is the
    # exterior lab sign in the base FireRed text block.
    positions = []
    start = 0
    while True:
        pos = data.find(old_lab, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 1
    if not positions:
        raise ValueError("Delivery Hub source label not found.")
    pos = positions[0]
    replacement = new_lab + (b"\x00" * (len(old_lab) - len(new_lab)))
    data[pos:pos + len(old_lab)] = replacement
    return data


def patch_rom(source: Path, output: Path) -> Path:
    source = Path(source)
    output = Path(output)

    if not source.is_file():
        raise FileNotFoundError(f"Input ROM not found: {source}")

    original = source.read_bytes()
    patched, count = patch_tartrek_starter(bytearray(original))
    if count != 1:
        raise RuntimeError("Tartrek starter patch was not applied exactly once.")
    patched = patch_visible_preview_text(patched)
    patched = patch_route1_wild_encounters(patched)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patched)

    if output.stat().st_size != source.stat().st_size:
        raise RuntimeError("Preview patch changed ROM size unexpectedly.")

    print("RC_PREVIEW_PATCH=TARTREK_STARTER+CAGLIARI_LABELS+MISTRILLO_ROUTE1")
    print(f"RC_PREVIEW_SPECIES_ID=0x{TARTREK_SPECIES_ID:04X}")
    print(f"RC_PREVIEW_WILD_SPECIES_ID=0x{MISTRILLO_SPECIES_ID:04X}")
    print(f"RC_PREVIEW_OUTPUT={output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply the first visible Release Candidate preview patch to a private CFRU ROM."
    )
    parser.add_argument("source", type=Path, help="CFRU-built private ROM")
    parser.add_argument("output", type=Path, help="Patched private ROM output")
    args = parser.parse_args()

    try:
        patch_rom(args.source, args.output)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
