#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

TARTREK_SPECIES_ID = 0x050E
FROBYTE_SPECIES_ID = 0x050F
EMBERFOX_SPECIES_ID = 0x0510
MISTRILLO_SPECIES_ID = 0x0511
WINGULL_SPECIES_ID = 0x0135
MEOWTH_SPECIES_ID = 0x0034

# FireRed USA 1.0 Oak's Lab starter script sequence. CFRU leaves this script
# region intact in the current Preview build, so the private-ROM patch can
# safely replace only the species variables without redistributing ROM data.
BULBASAUR_STARTER_SIGNATURE = bytes.fromhex(
    "16 01 40 00 00 16 02 40 01 00 16 03 40 04 00 16 04 40 07 00"
)
SQUIRTLE_STARTER_SIGNATURE = bytes.fromhex(
    "16 01 40 01 00 16 02 40 07 00 16 03 40 01 00"
)
CHARMANDER_STARTER_SIGNATURE = bytes.fromhex(
    "16 01 40 02 00 16 02 40 04 00 16 03 40 07 00"
)
PLAYER_SPECIES_VALUE_OFFSET = 8
RIVAL_SPECIES_VALUE_OFFSET = 13

# Vanilla Oak's Lab rival parties are three consecutive
# TrainerMonNoItemDefaultMoves structs: iv(u16), lvl(u8), pad(u8), species(u16).
OAK_LAB_RIVAL_PARTIES_SIGNATURE = bytes.fromhex(
    "00 00 05 00 07 00 00 00 05 00 01 00 00 00 05 00 04 00"
)
RIVAL_PARTY_SPECIES_OFFSETS = (4, 10, 16)

ROUTE1_WILD_SIGNATURE = bytes.fromhex(
    "03 03 10 00 03 03 13 00 03 03 10 00 03 03 13 00 "
    "02 02 10 00 02 02 13 00 03 03 10 00 03 03 13 00 "
    "04 04 10 00 04 04 13 00 05 05 10 00 04 04 13 00"
)
# FireRed grass-slot weights are 20/20/10/10/10/10/5/5/4/4/1/1.
# This ordering therefore yields exactly 60% Mistrillo, 25% Wingull,
# 15% Meowth while keeping the original encounter levels intact.
ROUTE1_PREVIEW_SPECIES = (
    MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID,
    WINGULL_SPECIES_ID, WINGULL_SPECIES_ID, WINGULL_SPECIES_ID,
    MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID,
)

CHARMAP = {
    **{chr(ord("A") + i): 0xBB + i for i in range(26)},
    **{chr(ord("a") + i): 0xD5 + i for i in range(26)},
    " ": 0x00, "!": 0xAB, "?": 0xAC, ".": 0xAD, "-": 0xAE,
    ",": 0xB8, ":": 0xF0, "'": 0xB4, "é": 0x1B, "\n": 0xFE,
}


def encode_text(text: str) -> bytes:
    return bytes(CHARMAP[ch] for ch in text)


VISIBLE_TEXT_REPLACEMENTS = (
    (encode_text("Welcome to the world of POKéMON!"), encode_text("Welcome to Release Candidate!")),
    (encode_text("My name is OAK."), encode_text("I'm your Lead.")),
    (encode_text("People affectionately refer to me"), encode_text("They call me Delivery Lead")),
    (encode_text("This is my grandson."), encode_text("Meet your teammate.")),
    (encode_text("He's been your rival since you both"), encode_text("He's tracked your KPI since day one")),
    (encode_text("were babies."), encode_text("onboarding.")),
    (encode_text("as the POKéMON PROFESSOR."), encode_text("on this project.")),
    (encode_text("I see! BULBASAUR is your choice."), encode_text("TARTREK is your new partner!")),
    (encode_text("Hm! SQUIRTLE is your choice."), encode_text("FROBYTE is your new partner!")),
    (encode_text("Ah! CHARMANDER is your choice."), encode_text("EMBERFOX is your new partner!")),
    (encode_text("It's very easy to raise."), encode_text("First task starts now!")),
    (encode_text("the GRASS POKéMON BULBASAUR?"), encode_text("the GRASS/GROUND TARTREK?")),
    (encode_text("the WATER POKéMON SQUIRTLE?"), encode_text("the WATER/ELECTRIC FROBYTE?")),
    (encode_text("FIRE POKéMON CHARMANDER?"), encode_text("FIRE/DARK EMBERFOX?")),
    (encode_text("Come on, I'll take you on!"), encode_text("KPI check: show velocity!")),
    (encode_text("PALLET TOWN\nShades of your journey await!"), encode_text("CAGLIARI\nFirst sprint starts here!")),
    (encode_text("ROUTE 1\nPALLET TOWN - VIRIDIAN CITY"), encode_text("PORT LINK\nCAGLIARI - MARINA PORTO")),
    (encode_text("There are three POKéMON here."), encode_text("Three resources are ready.")),
    (encode_text("You can have one.\nGo on, choose!"), encode_text("Pick one now.\nFirst task starts!")),
    (encode_text("Hi!\nI work at a POKéMON MART."), encode_text("Hi!\nI work on Delivery.")),
    (encode_text("Please, visit us in VIRIDIAN CITY."), encode_text("Please, report at MARINA PORTO.")),
    (encode_text("I know, I'll give you a sample.\nHere you go!"), encode_text("Quick handoff: take this.\nUse it well!")),
    (encode_text("VIRIDIAN CITY \nThe Eternally Green Paradise"), encode_text("MARINA PORTO \nDEPLOY BLOCKED - CHECK SCOPE")),
)

MAP_NAME_REPLACEMENT = (
    encode_text("PALLET TOWN") + b"\xFF" + encode_text("VIRIDIAN CITY") + b"\xFF",
    encode_text("CAGLIARI") + b"\xFF" + (b"\x00" * 3) + encode_text("MARINA PORTO") + b"\x00\xFF",
)
LAB_SIGN_REPLACEMENT = (
    b"\xCA\xC9\xC5\x1B\xC7\xC9\xC8\x00\xCC\xBF\xCD\xBF\xBB\xCC\xBD\xC2\x00\xC6\xBB\xBC",
    encode_text("DELIVERY HUB"),
)


def _find_exactly_one(data: bytearray, signature: bytes, label: str) -> int:
    positions, start = [], 0
    while True:
        pos = data.find(signature, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 1
    if len(positions) != 1:
        raise ValueError(f"Expected exactly one {label} signature, found {len(positions)}.")
    return positions[0]


def patch_preview_starters(data: bytearray) -> bytearray:
    starter_specs = (
        (BULBASAUR_STARTER_SIGNATURE, "Bulbasaur starter", TARTREK_SPECIES_ID, EMBERFOX_SPECIES_ID),
        (SQUIRTLE_STARTER_SIGNATURE, "Squirtle starter", FROBYTE_SPECIES_ID, TARTREK_SPECIES_ID),
        (CHARMANDER_STARTER_SIGNATURE, "Charmander starter", EMBERFOX_SPECIES_ID, FROBYTE_SPECIES_ID),
    )
    for signature, label, player_species, rival_species in starter_specs:
        pos = _find_exactly_one(data, signature, label)
        data[pos + PLAYER_SPECIES_VALUE_OFFSET:pos + PLAYER_SPECIES_VALUE_OFFSET + 2] = player_species.to_bytes(2, "little")
        data[pos + RIVAL_SPECIES_VALUE_OFFSET:pos + RIVAL_SPECIES_VALUE_OFFSET + 2] = rival_species.to_bytes(2, "little")
    return data


def patch_oak_lab_rival_parties(data: bytearray) -> bytearray:
    pos = _find_exactly_one(data, OAK_LAB_RIVAL_PARTIES_SIGNATURE, "Oak Lab rival party")
    for rel, species in zip(RIVAL_PARTY_SPECIES_OFFSETS, (FROBYTE_SPECIES_ID, TARTREK_SPECIES_ID, EMBERFOX_SPECIES_ID)):
        data[pos + rel:pos + rel + 2] = species.to_bytes(2, "little")
    return data


def _replace_size_preserving(data: bytearray, old: bytes, new: bytes, *, expected: int | None = None) -> int:
    if len(new) > len(old):
        raise ValueError("Replacement text cannot exceed the source byte length.")
    positions, start = [], 0
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
    base = _find_exactly_one(data, ROUTE1_WILD_SIGNATURE, "FireRed Route 1 wild encounter")
    for record, species in enumerate(ROUTE1_PREVIEW_SPECIES):
        species_pos = base + (record * 4) + 2
        data[species_pos:species_pos + 2] = species.to_bytes(2, "little")
    return data


def patch_visible_preview_text(data: bytearray) -> bytearray:
    for old, new in VISIBLE_TEXT_REPLACEMENTS:
        _replace_size_preserving(data, old, new, expected=1)
    old_city, new_city = MAP_NAME_REPLACEMENT
    if len(old_city) != len(new_city):
        raise ValueError("Map-name replacement must preserve byte length.")
    _replace_size_preserving(data, old_city, new_city, expected=1)
    old_lab, new_lab = LAB_SIGN_REPLACEMENT
    pos = data.find(old_lab)
    if pos < 0:
        raise ValueError("Delivery Hub source label not found.")
    replacement = new_lab + (b"\x00" * (len(old_lab) - len(new_lab)))
    data[pos:pos + len(old_lab)] = replacement
    return data


def validate_preview_patch(data: bytearray) -> None:
    """Fail closed if the private ROM does not contain the complete preview contract."""
    for old, new in VISIBLE_TEXT_REPLACEMENTS:
        if new not in data:
            raise RuntimeError("A required Release Candidate visible-text replacement is missing.")
    if MAP_NAME_REPLACEMENT[1] not in data or LAB_SIGN_REPLACEMENT[1] not in data:
        raise RuntimeError("Cagliari/Delivery Hub identity labels are incomplete.")
    for species in (TARTREK_SPECIES_ID, FROBYTE_SPECIES_ID, EMBERFOX_SPECIES_ID, MISTRILLO_SPECIES_ID):
        if species.to_bytes(2, "little") not in data:
            raise RuntimeError(f"Required preview species 0x{species:04X} is missing from patched ROM.")


def patch_rom(source: Path, output: Path) -> Path:
    source, output = Path(source), Path(output)
    if not source.is_file():
        raise FileNotFoundError(f"Input ROM not found: {source}")
    original = source.read_bytes()
    patched = patch_preview_starters(bytearray(original))
    patched = patch_oak_lab_rival_parties(patched)
    patched = patch_visible_preview_text(patched)
    patched = patch_route1_wild_encounters(patched)
    validate_preview_patch(patched)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patched)
    if output.stat().st_size != source.stat().st_size:
        raise RuntimeError("Preview patch changed ROM size unexpectedly.")
    print("RC_PREVIEW_PATCH=THREE_STARTERS+CAGLIARI_LABELS+KPI_RIVAL+PORT_LINK")
    print(f"RC_PREVIEW_STARTERS=0x{TARTREK_SPECIES_ID:04X},0x{FROBYTE_SPECIES_ID:04X},0x{EMBERFOX_SPECIES_ID:04X}")
    print("RC_PREVIEW_PORT_LINK=MISTRILLO_60+WINGULL_25+MEOWTH_15")
    print(f"RC_PREVIEW_OUTPUT={output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the visible Release Candidate preview patch to a private CFRU ROM.")
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
