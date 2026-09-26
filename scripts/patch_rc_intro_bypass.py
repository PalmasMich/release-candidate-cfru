#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from discover_rc_intro_bypass import PROMPT, ROM_BASE, discover_prompt_pointer_refs, encode_text

SOURCE_LITERAL_DELTA = -0xE4
RESHOW_LITERAL_DELTA = -0xA4
FADE_IN_ENTRY_DELTA = -0xA0
RESHOW_ENTRY_DELTA = 0x5C

SOURCE_LITERAL_OFFSET = 0x00130690
RESHOW_LITERAL_OFFSET = 0x001306D0
EXPECTED_FADE_IN_POINTER = 0x081306D5
EXPECTED_RESHOW_POINTER = 0x081307D1


def expected_layout(data: bytes) -> tuple[int, int, int, int]:
    _, refs = discover_prompt_pointer_refs(data)
    if len(refs) != 1:
        raise RuntimeError(f"expected one rival-intro text pointer, found {len(refs)}")

    anchor = refs[0].literal_offset
    source_literal = anchor + SOURCE_LITERAL_DELTA
    reshow_literal = anchor + RESHOW_LITERAL_DELTA
    fade_in_entry = anchor + FADE_IN_ENTRY_DELTA
    reshow_entry = anchor + RESHOW_ENTRY_DELTA

    expected_old = ROM_BASE + fade_in_entry + 1
    expected_new = ROM_BASE + reshow_entry + 1
    actual_old = int.from_bytes(data[source_literal:source_literal + 4], "little")
    actual_new = int.from_bytes(data[reshow_literal:reshow_literal + 4], "little")

    if actual_old != expected_old:
        raise RuntimeError(
            f"unexpected FadeOutPlayerPic continuation: expected 0x{expected_old:08X}, "
            f"found 0x{actual_old:08X}"
        )
    if actual_new != expected_new:
        raise RuntimeError(
            f"unexpected ReshowPlayersPic pointer: expected 0x{expected_new:08X}, "
            f"found 0x{actual_new:08X}"
        )

    return source_literal, reshow_literal, expected_old, expected_new


def verify_bypass(data: bytes) -> tuple[int, int]:
    source_value = int.from_bytes(
        data[SOURCE_LITERAL_OFFSET:SOURCE_LITERAL_OFFSET + 4], "little"
    )
    target_value = int.from_bytes(
        data[RESHOW_LITERAL_OFFSET:RESHOW_LITERAL_OFFSET + 4], "little"
    )
    if source_value != EXPECTED_RESHOW_POINTER or target_value != EXPECTED_RESHOW_POINTER:
        raise RuntimeError(
            "rival-name bypass is not structurally active "
            f"(source=0x{source_value:08X}, reshow=0x{target_value:08X})"
        )
    return SOURCE_LITERAL_OFFSET, EXPECTED_RESHOW_POINTER


def apply_bypass(data: bytes) -> bytes:
    source_literal, reshow_literal, expected_old, expected_new = expected_layout(data)
    if source_literal != SOURCE_LITERAL_OFFSET or reshow_literal != RESHOW_LITERAL_OFFSET:
        raise RuntimeError(
            f"unexpected rival-intro layout offsets: source=0x{source_literal:08X}, "
            f"reshow=0x{reshow_literal:08X}"
        )
    if expected_old != EXPECTED_FADE_IN_POINTER or expected_new != EXPECTED_RESHOW_POINTER:
        raise RuntimeError("unexpected rival-intro function pointers")
    patched = bytearray(data)
    patched[source_literal:source_literal + 4] = expected_new.to_bytes(4, "little")
    verify_bypass(bytes(patched))
    return bytes(patched)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if not args.source.is_file():
        return 2

    try:
        patched = apply_bypass(args.source.read_bytes())
        literal_offset, target = verify_bypass(patched)
    except RuntimeError as exc:
        print(f"RC_INTRO_BYPASS=BLOCKED:{exc}")
        return 2

    args.output.write_bytes(patched)
    print("RC_INTRO_BYPASS=APPLIED")
    print(f"RC_INTRO_BYPASS_LITERAL_OFFSET=0x{literal_offset:08X}")
    print(f"RC_INTRO_BYPASS_TARGET=0x{target:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
