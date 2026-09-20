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

RIVAL_NAME_PROMPTS = (
    "What was his name now?",
    "Come si chiama?",
)


def audit_data(data: bytes) -> tuple[list[str], list[str]]:
    stock_text = [text for text in FORBIDDEN_OPENING_TEXT if encode_text(text) in data]
    rival_name_prompts = [text for text in RIVAL_NAME_PROMPTS if encode_text(text) in data]
    return stock_text, rival_name_prompts


def validate_opening(data: bytes) -> None:
    stock_text, rival_name_prompts = audit_data(data)
    if rival_name_prompts:
        raise RuntimeError(
            "rival-name prompt remains in the visible opening: "
            + ", ".join(rival_name_prompts)
        )
    if stock_text:
        raise RuntimeError("stock opening text remains: " + ", ".join(stock_text))


def audit_rom(path: Path) -> list[str]:
    stock_text, rival_name_prompts = audit_data(path.read_bytes())
    return stock_text + rival_name_prompts


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Release Candidate ROM for stock FireRed opening text.")
    parser.add_argument("rom", type=Path)
    args = parser.parse_args()

    if not args.rom.is_file():
        print(f"RC_OPENING_AUDIT=BLOCKED:MISSING_ROM:{args.rom}")
        return 2

    stock_text, rival_name_prompts = audit_data(args.rom.read_bytes())
    if stock_text or rival_name_prompts:
        print("RC_OPENING_AUDIT=FAILED")
        for text in stock_text:
            print(f"RC_OPENING_STOCK_TEXT={text}")
        for text in rival_name_prompts:
            print(f"RC_OPENING_RIVAL_NAME_PROMPT={text}")
        return 1

    print("RC_OPENING_AUDIT=PASS")
    print("RC_RIVAL_NAME_STRUCTURAL_BYPASS=PENDING:RUNTIME_CONFIRMATION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
