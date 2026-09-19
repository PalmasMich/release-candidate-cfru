#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from apply_release_candidate_preview_patch import encode_text

# Keep this list limited to long, intro-specific signatures. Generic location
# names such as PALLET or VIRIDIAN may legitimately remain in unreachable
# vanilla data and must not make the Chapter 1 audit noisy.
FORBIDDEN_OPENING_TEXT = (
    "Welcome to the world of POKéMON!",
    "My name is OAK.",
    "People affectionately refer to me",
    "This is my grandson.",
    "He's been your rival since you both",
    "Your very own POKéMON legend is about",
    "A world of dreams and adventures",
    "with POKéMON awaits! Let's go!",
)

def audit_rom(path: Path) -> list[str]:
    data = path.read_bytes()
    remaining = []
    for text in FORBIDDEN_OPENING_TEXT:
        encoded = encode_text(text)
        if encoded in data:
            remaining.append(text)
    return remaining

def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Release Candidate ROM for stock FireRed opening text.")
    parser.add_argument("rom", type=Path)
    args = parser.parse_args()

    if not args.rom.is_file():
        print(f"RC_OPENING_AUDIT=BLOCKED:MISSING_ROM:{args.rom}")
        return 2

    remaining = audit_rom(args.rom)
    if remaining:
        print("RC_OPENING_AUDIT=FAILED")
        for text in remaining:
            print(f"RC_OPENING_STOCK_TEXT={text}")
        return 1

    print("RC_OPENING_AUDIT=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
