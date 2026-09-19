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

BULBASAUR_STARTER_SIGNATURE = bytes.fromhex("16 01 40 00 00 16 02 40 01 00 16 03 40 04 00 16 04 40 07 00")
SQUIRTLE_STARTER_SIGNATURE = bytes.fromhex("16 01 40 01 00 16 02 40 07 00 16 03 40 01 00")
CHARMANDER_STARTER_SIGNATURE = bytes.fromhex("16 01 40 02 00 16 02 40 04 00 16 03 40 07 00")
PLAYER_SPECIES_VALUE_OFFSET = 8
RIVAL_SPECIES_VALUE_OFFSET = 13

OAK_LAB_RIVAL_PARTIES_SIGNATURE = bytes.fromhex("00 00 05 00 07 00 00 00 05 00 01 00 00 00 05 00 04 00")
RIVAL_PARTY_SPECIES_OFFSETS = (4, 10, 16)

ROUTE1_WILD_SIGNATURE = bytes.fromhex(
    "03 03 10 00 03 03 13 00 03 03 10 00 03 03 13 00 "
    "02 02 10 00 02 02 13 00 03 03 10 00 03 03 13 00 "
    "04 04 10 00 04 04 13 00 05 05 10 00 04 04 13 00"
)
GRASS_SLOT_WEIGHTS = (20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1)
# The two 20% slots plus the first two 10% slots guarantee that the first
# Port Link field test is overwhelmingly likely to showcase the custom mon,
# while preserving a small coastal mix for repeat encounters.
ROUTE1_PREVIEW_SPECIES = (
    MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID, MISTRILLO_SPECIES_ID,
    WINGULL_SPECIES_ID, WINGULL_SPECIES_ID, WINGULL_SPECIES_ID,
    MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID, MEOWTH_SPECIES_ID,
)
ROUTE1_PREVIEW_LEVELS = (
    (3, 3), (4, 4), (3, 3), (5, 5),
    (3, 3), (4, 4), (3, 3),
    (4, 4), (3, 3), (4, 4), (3, 3), (4, 4),
)

CHARMAP = {
    **{chr(ord("A") + i): 0xBB + i for i in range(26)},
    **{chr(ord("a") + i): 0xD5 + i for i in range(26)},
    **{str(i): 0xA1 + i for i in range(10)},
    " ": 0x00, "!": 0xAB, "?": 0xAC, ".": 0xAD, "-": 0xAE,
    ",": 0xB8, "/": 0xBA, ":": 0xF0, "'": 0xB4, "é": 0x1B, "\n": 0xFE,
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
    (encode_text("There are three POKéMON here."), encode_text("Three resources are ready.")),
    (encode_text("You can have one.\nGo on, choose!"), encode_text("Pick one now.\nFirst task starts!")),
    (encode_text("OAK: Now, {PLAYER}."), encode_text("LEAD: Hi, {PLAYER}.")),
    (encode_text("Which one will you choose for\nyourself?"), encode_text("Which resource joins your\nfirst sprint?")),
    (encode_text("I see! BULBASAUR is your choice."), encode_text("TARTREK is your new partner!")),
    (encode_text("Hm! SQUIRTLE is your choice."), encode_text("FROBYTE is your new partner!")),
    (encode_text("Ah! CHARMANDER is your choice."), encode_text("EMBERFOX is your new partner!")),
    (encode_text("It's very easy to raise."), encode_text("First task starts now!")),
    (encode_text("the GRASS POKéMON BULBASAUR?"), encode_text("the GRASS/GROUND TARTREK?")),
    (encode_text("the WATER POKéMON SQUIRTLE?"), encode_text("the WATER/ELECTRIC FROBYTE?")),
    (encode_text("FIRE POKéMON CHARMANDER?"), encode_text("FIRE/DARK EMBERFOX?")),
    (encode_text("{RIVAL}: My POKéMON looks a lot\ntougher than yours."), encode_text("{RIVAL}: My KPI already looks\nbetter than yours.")),
    (encode_text("Come on, I'll take you on!"), encode_text("KPI check: show velocity!")),
    (encode_text("{RIVAL}: Yeah!\nAm I great or what?"), encode_text("{RIVAL}: Yeah!\nKPI is GREEN!")),
    (encode_text("PALLET TOWN\nShades of your journey await!"), encode_text("CAGLIARI\nFirst sprint starts here!")),
    (encode_text("ROUTE 1\nPALLET TOWN - VIRIDIAN CITY"), encode_text("PORT LINK\nCAGLIARI - MARINA PORTO")),
    (encode_text("Hi!\nI work at a POKéMON MART."), encode_text("Hi!\nI work on Delivery.")),
    (encode_text("It's part of a convenient chain\nselling all sorts of items."), encode_text("I'm covering Port Link today.\nScope says five minutes.")),
    (encode_text("Please, visit us in VIRIDIAN CITY."), encode_text("Please, report at MARINA PORTO.")),
    (encode_text("I know, I'll give you a sample.\nHere you go!"), encode_text("Quick handoff: take this.\nUse it well!")),
    (encode_text("Please come see us if you need\nPOKé BALLS for catching POKéMON."), encode_text("Ping Delivery if you need\nmore field-test supplies.")),
    (encode_text("You can get back to PALLET TOWN\nquicker that way."), encode_text("You can get back to CAGLIARI\nquicker that way.")),
    (encode_text("VIRIDIAN CITY \nThe Eternally Green Paradise"), encode_text("MARINA PORTO \nDEPLOY BLOCKED - CHECK SCOPE")),
)
MAP_NAME_REPLACEMENT = (
    encode_text("PALLET TOWN") + b"\xFF" + encode_text("VIRIDIAN CITY") + b"\xFF",
    encode_text("CAGLIARI") + b"\xFF" + (b"\x00" * 3) + encode_text("MARINA PORTO") + b"\x00\xFF",
)
LAB_SIGN_REPLACEMENT = (
    b"\xCA\xC9\xC5\x1B\xC9\xC8\x00\xCC\xBF\xCD\xBF\xBB\xCC\xBD\xC2\x00\xC6\xBB\xBC",
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
    for signature, label, player_species, rival_species in (
        (BULBASAUR_STARTER_SIGNATURE, "Bulbasaur starter", TARTREK_SPECIES_ID, EMBERFOX_SPECIES_ID),
        (SQUIRTLE_STARTER_SIGNATURE, "Squirtle starter", FROBYTE_SPECIES_ID, TARTREK_SPECIES_ID),
        (CHARMANDER_STARTER_SIGNATURE, "Charmander starter", EMBERFOX_SPECIES_ID, FROBYTE_SPECIES_ID),
    ):
        pos = _find_exactly_one(data, signature, label)
        data[pos + PLAYER_SPECIES_VALUE_OFFSET:pos + PLAYER_SPECIES_VALUE_OFFSET + 2] = player_species.to_bytes(2, "little")
        data[pos + RIVAL_SPECIES_VALUE_OFFSET:pos + RIVAL_SPECIES_VALUE_OFFSET + 2] = rival_species.to_bytes(2, "little")
    return data


def patched_starter_signature(signature: bytes, player_species: int, rival_species: int) -> bytes:
    patched = bytearray(signature)
    patched[PLAYER_SPECIES_VALUE_OFFSET:PLAYER_SPECIES_VALUE_OFFSET + 2] = player_species.to_bytes(2, "little")
    patched[RIVAL_SPECIES_VALUE_OFFSET:RIVAL_SPECIES_VALUE_OFFSET + 2] = rival_species.to_bytes(2, "little")
    return bytes(patched)


def patch_oak_lab_rival_parties(data: bytearray) -> tuple[bytearray, bool]:
    positions, start = [], 0
    while True:
        pos = data.find(OAK_LAB_RIVAL_PARTIES_SIGNATURE, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 1
    if len(positions) == 0:
        print("RC_PREVIEW_KPI_RIVAL_PARTY=PENDING:LEGACY_SIGNATURE_NOT_FOUND")
        return data, False
    if len(positions) != 1:
        raise ValueError(f"Expected at most one Oak Lab rival party signature, found {len(positions)}.")
    pos = positions[0]
    for rel, species in zip(RIVAL_PARTY_SPECIES_OFFSETS, (FROBYTE_SPECIES_ID, TARTREK_SPECIES_ID, EMBERFOX_SPECIES_ID)):
        data[pos + rel:pos + rel + 2] = species.to_bytes(2, "little")
    print("RC_PREVIEW_KPI_RIVAL_PARTY=APPLIED")
    return data, True


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
    for record, (species, levels) in enumerate(zip(ROUTE1_PREVIEW_SPECIES, ROUTE1_PREVIEW_LEVELS)):
        record_pos = base + (record * 4)
        data[record_pos:record_pos + 2] = bytes(levels)
        data[record_pos + 2:record_pos + 4] = species.to_bytes(2, "little")
    return data


def patch_visible_preview_text(data: bytearray) -> tuple[bytearray, list[bytes], bool, bool]:
    applied_texts = []
    for index, (old, new) in enumerate(VISIBLE_TEXT_REPLACEMENTS):
        count = _replace_size_preserving(data, old, new, expected=None)
        if count == 0:
            print(f"RC_PREVIEW_TEXT_{index:02d}=PENDING:LEGACY_SIGNATURE_NOT_FOUND")
            continue
        if count != 1:
            raise ValueError(f"Expected at most one legacy visible-text signature {index}, found {count}.")
        applied_texts.append(new)
        print(f"RC_PREVIEW_TEXT_{index:02d}=APPLIED")
    old_city, new_city = MAP_NAME_REPLACEMENT
    if len(old_city) != len(new_city):
        raise ValueError("Map-name replacement must preserve byte length.")
    city_count = _replace_size_preserving(data, old_city, new_city, expected=None)
    if city_count == 0:
        print("RC_PREVIEW_MAP_NAMES=PENDING:LEGACY_SIGNATURE_NOT_FOUND")
        city_applied = False
    elif city_count == 1:
        print("RC_PREVIEW_MAP_NAMES=APPLIED")
        city_applied = True
    else:
        raise ValueError(f"Expected at most one legacy map-name signature, found {city_count}.")
    old_lab, new_lab = LAB_SIGN_REPLACEMENT
    positions, start = [], 0
    while True:
        pos = data.find(old_lab, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 1
    if len(positions) == 0:
        print("RC_PREVIEW_DELIVERY_HUB_LABEL=PENDING:LEGACY_SIGNATURE_NOT_FOUND")
        lab_applied = False
    elif len(positions) == 1:
        pos = positions[0]
        data[pos:pos + len(old_lab)] = new_lab + (b"\x00" * (len(old_lab) - len(new_lab)))
        print("RC_PREVIEW_DELIVERY_HUB_LABEL=APPLIED")
        lab_applied = True
    else:
        print("RC_PREVIEW_DELIVERY_HUB_LABEL=" f"PENDING:AMBIGUOUS_SIGNATURE:{len(positions)}")
        lab_applied = False
    return data, applied_texts, city_applied, lab_applied


def validate_preview_patch(data: bytearray, *, rival_party_required: bool = True, applied_texts: list[bytes] | None = None, map_names_required: bool = False, lab_label_required: bool = False) -> None:
    for new in applied_texts or []:
        if new not in data:
            raise RuntimeError("An applied Release Candidate visible-text replacement is missing.")
    if map_names_required and MAP_NAME_REPLACEMENT[1] not in data:
        raise RuntimeError("Applied Cagliari map-name replacement is missing.")
    if lab_label_required and LAB_SIGN_REPLACEMENT[1] not in data:
        raise RuntimeError("Applied Delivery Hub identity label is missing.")
    for signature, label, player_species, rival_species in (
        (BULBASAUR_STARTER_SIGNATURE, "Tartrek starter", TARTREK_SPECIES_ID, EMBERFOX_SPECIES_ID),
        (SQUIRTLE_STARTER_SIGNATURE, "Frobyte starter", FROBYTE_SPECIES_ID, TARTREK_SPECIES_ID),
        (CHARMANDER_STARTER_SIGNATURE, "Emberfox starter", EMBERFOX_SPECIES_ID, FROBYTE_SPECIES_ID),
    ):
        expected = patched_starter_signature(signature, player_species, rival_species)
        positions, start = [], 0
        while True:
            pos = data.find(expected, start)
            if pos < 0:
                break
            positions.append(pos)
            start = pos + 1
        if len(positions) != 1:
            raise RuntimeError(f"{label} wiring is incorrect: expected exactly one patched script, found {len(positions)}.")
    if rival_party_required:
        rival_party = b"".join(b"\x00\x00\x05\x00" + species.to_bytes(2, "little") for species in (FROBYTE_SPECIES_ID, TARTREK_SPECIES_ID, EMBERFOX_SPECIES_ID))
        if rival_party not in data:
            raise RuntimeError("Oak Lab KPI-rival party wiring is incomplete.")
    expected_route = bytearray(ROUTE1_WILD_SIGNATURE)
    for record, (species, levels) in enumerate(zip(ROUTE1_PREVIEW_SPECIES, ROUTE1_PREVIEW_LEVELS)):
        record_pos = record * 4
        expected_route[record_pos:record_pos + 2] = bytes(levels)
        expected_route[record_pos + 2:record_pos + 4] = species.to_bytes(2, "little")
    if bytes(expected_route) not in data:
        raise RuntimeError("Port Link custom encounter table is incomplete.")


def patch_rom(source: Path, output: Path) -> Path:
    source, output = Path(source), Path(output)
    if not source.is_file():
        raise FileNotFoundError(f"Input ROM not found: {source}")
    original = source.read_bytes()
    patched = patch_preview_starters(bytearray(original))
    patched, rival_party_patched = patch_oak_lab_rival_parties(patched)
    patched, applied_texts, city_applied, lab_applied = patch_visible_preview_text(patched)
    patched = patch_route1_wild_encounters(patched)
    validate_preview_patch(patched, rival_party_required=rival_party_patched, applied_texts=applied_texts, map_names_required=city_applied, lab_label_required=lab_applied)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patched)
    if output.stat().st_size != source.stat().st_size:
        raise RuntimeError("Preview patch changed ROM size unexpectedly.")
    print("RC_PREVIEW_PATCH=THREE_STARTERS+CAGLIARI_LABELS+KPI_RIVAL+PORT_LINK_ENCOUNTERS")
    print(f"RC_PREVIEW_STARTERS=0x{TARTREK_SPECIES_ID:04X},0x{FROBYTE_SPECIES_ID:04X},0x{EMBERFOX_SPECIES_ID:04X}")
    print(f"RC_PREVIEW_WILD_SPECIES_ID=0x{MISTRILLO_SPECIES_ID:04X}")
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
