#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from apply_release_candidate_preview_patch import encode_text

ROM_BASE = 0x08000000
PROMPT = "What was his name now?"
SEARCH_RADIUS = 0x140


@dataclass(frozen=True)
class PointerRef:
    literal_offset: int
    target_offset: int

    @property
    def literal_address(self) -> int:
        return ROM_BASE + self.literal_offset

    @property
    def target_address(self) -> int:
        return ROM_BASE + self.target_offset


def find_all(data: bytes, needle: bytes) -> list[int]:
    hits: list[int] = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return hits
        hits.append(pos)
        start = pos + 1


def discover_prompt_pointer_refs(data: bytes) -> tuple[int, list[PointerRef]]:
    encoded = encode_text(PROMPT)
    prompts = find_all(data, encoded)
    if len(prompts) != 1:
        raise RuntimeError(
            f"expected exactly one rival-name prompt, found {len(prompts)}"
        )

    prompt_offset = prompts[0]
    prompt_address = ROM_BASE + prompt_offset
    raw_ptr = prompt_address.to_bytes(4, "little")
    refs = [
        PointerRef(offset, prompt_offset)
        for offset in find_all(data, raw_ptr)
    ]
    if not refs:
        raise RuntimeError("rival-name prompt exists but no ROM pointer references it")
    return prompt_offset, refs


def nearby_thumb_literals(data: bytes, center: int) -> list[tuple[int, int]]:
    lo = max(0, center - SEARCH_RADIUS)
    hi = min(len(data) - 3, center + SEARCH_RADIUS)
    result: list[tuple[int, int]] = []
    for offset in range(lo, hi, 4):
        value = int.from_bytes(data[offset:offset + 4], "little")
        # GBA Thumb function pointers are normally ROM addresses with bit 0 set.
        if 0x08000001 <= value <= 0x09FFFFFF and value & 1:
            result.append((offset, value))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Discover the FireRed rival-naming control-flow neighborhood "
            "without writing to the ROM."
        )
    )
    parser.add_argument("rom", type=Path)
    args = parser.parse_args()

    if not args.rom.is_file():
        print(f"RC_INTRO_BYPASS_DISCOVERY=BLOCKED:MISSING_ROM:{args.rom}")
        return 2

    data = args.rom.read_bytes()
    try:
        prompt_offset, refs = discover_prompt_pointer_refs(data)
    except RuntimeError as exc:
        print(f"RC_INTRO_BYPASS_DISCOVERY=BLOCKED:{exc}")
        return 2

    print("RC_INTRO_BYPASS_DISCOVERY=READY")
    print(f"RC_RIVAL_PROMPT_OFFSET=0x{prompt_offset:08X}")
    print(f"RC_RIVAL_PROMPT_ADDRESS=0x{ROM_BASE + prompt_offset:08X}")
    print(f"RC_RIVAL_PROMPT_POINTER_REFS={len(refs)}")

    for index, ref in enumerate(refs):
        print(f"RC_RIVAL_PROMPT_PTR_{index}=0x{ref.literal_offset:08X}")
        candidates = nearby_thumb_literals(data, ref.literal_offset)
        print(f"RC_RIVAL_NEARBY_THUMB_PTRS_{index}={len(candidates)}")
        for candidate_index, (offset, value) in enumerate(candidates[:16]):
            print(
                f"RC_RIVAL_THUMB_PTR_{index}_{candidate_index}="
                f"0x{offset:08X}->0x{value:08X}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
