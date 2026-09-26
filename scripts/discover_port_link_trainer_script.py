#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

GBA_ROM_BASE = 0x08000000

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

PORT_LINK_NPC_TEXT = "Hi!\nI work on Delivery."
PORT_LINK_NPC_SOURCE_TEXT = "Hi!\nI work at a POKéMON MART."

CMD_END = 0x02
CMD_LOADPOINTER = 0x0F
CMD_FACEPLAYER = 0x5A
CMD_TRAINERBATTLE = 0x5C
CMD_LOCK = 0x6A
CMD_RELEASE = 0x6C
CMD_CALLSTD = 0x09
CMD_CHECKFLAG = 0x2B
CMD_GOTO_IF = 0x06
# Use a real FRLG trainer entry rather than one of the RS compatibility dummy
# slots. Trainer 89 is Youngster Ben and has a valid two-mon party in vanilla.
# A later guarded party patch can replace that party with RC species without
# relying on placeholder trainer data.
TRAINER_BOOTSTRAP_ID = 89
TRAINER_BATTLE_SINGLE = 0


def encode_text(text: str) -> bytes:
    return bytes(CHARMAP[ch] for ch in text)


def find_all(data: bytes, needle: bytes) -> list[int]:
    positions = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return positions
        positions.append(pos)
        start = pos + 1


def gba_pointer_bytes(file_offset: int) -> bytes:
    return (GBA_ROM_BASE + file_offset).to_bytes(4, "little")


def discover_text_xrefs(data: bytes, encoded_text: bytes) -> dict:
    text_offsets = find_all(data, encoded_text)
    result = {"text_offsets": text_offsets, "xrefs": []}
    for text_offset in text_offsets:
        pointer = gba_pointer_bytes(text_offset)
        for xref in find_all(data, pointer):
            result["xrefs"].append({"text_offset": text_offset, "pointer_value": GBA_ROM_BASE + text_offset, "xref_offset": xref})
    result["xrefs"].sort(key=lambda item: (item["text_offset"], item["xref_offset"]))
    return result


def classify_xref_context(data: bytes, xref: dict) -> dict:
    xref_offset = xref["xref_offset"]
    window_start = max(0, xref_offset - 12)
    window_end = min(len(data), xref_offset + 12)
    window = data[window_start:window_end]
    # Vanilla Route 1 Mart employee dialogue uses loadpointer + callstd. We only
    # consider an xref patchable when the pointer is immediately preceded by
    # loadpointer 0, which keeps the bootstrap fail-closed.
    prefix = data[max(0, xref_offset - 2):xref_offset]
    classification = "event_dialogue_script" if prefix == bytes((CMD_LOADPOINTER, 0)) else "unknown"
    script_start_candidate = xref_offset - 2 if classification == "event_dialogue_script" else None
    patch_plan = None
    if script_start_candidate is not None:
        # Capture enough original script bytes to fit the replacement trainer
        # command while still verifying exact bytes before mutation.
        signature = data[script_start_candidate:script_start_candidate + 24]
        patch_plan = {"script_start_candidate": script_start_candidate, "verification_signature_hex": signature.hex(" ")}
    return {**xref, "classification": classification, "window_start": window_start, "window_hex": window.hex(" "), "patch_plan": patch_plan}


def analyze_rom(data: bytes) -> dict:
    patched = discover_text_xrefs(data, encode_text(PORT_LINK_NPC_TEXT))
    source = discover_text_xrefs(data, encode_text(PORT_LINK_NPC_SOURCE_TEXT))
    contexts = [classify_xref_context(data, xref) for xref in patched["xrefs"]]
    event_contexts = [c for c in contexts if c["classification"] == "event_dialogue_script"]
    return {
        "patched_text": patched,
        "source_text": source,
        "candidate_contexts": contexts,
        "safe_to_patch": len(patched["text_offsets"]) == 1 and len(event_contexts) == 1,
        "trainer_bootstrap_id": TRAINER_BOOTSTRAP_ID,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover the patched Route 1/Port Link Delivery NPC script in a private RC ROM.")
    parser.add_argument("rom", type=Path)
    args = parser.parse_args()
    if not args.rom.is_file():
        print(f"ERROR: ROM not found: {args.rom}")
        return 1
    report = analyze_rom(args.rom.read_bytes())
    print(json.dumps(report, indent=2))
    return 0 if report["safe_to_patch"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
