#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

TARTREK_SPECIES_ID = 0x04F4

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


def patch_rom(source: Path, output: Path) -> Path:
    source = Path(source)
    output = Path(output)

    if not source.is_file():
        raise FileNotFoundError(f"Input ROM not found: {source}")

    original = source.read_bytes()
    patched, count = patch_tartrek_starter(bytearray(original))
    if count != 1:
        raise RuntimeError("Tartrek starter patch was not applied exactly once.")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patched)

    if output.stat().st_size != source.stat().st_size:
        raise RuntimeError("Preview patch changed ROM size unexpectedly.")

    print(f"RC_PREVIEW_PATCH=TARTREK_STARTER")
    print(f"RC_PREVIEW_SPECIES_ID=0x{TARTREK_SPECIES_ID:04X}")
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
