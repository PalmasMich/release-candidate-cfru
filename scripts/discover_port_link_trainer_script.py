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
CMD_LOCK = 0x69
CMD_RELEASE = 0x6B
CMD_MSGBOX_NORMAL = 0xCB


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
    result = {
        "text_offsets": text_offsets,
        "xrefs": [],
    }

    for text_offset in text_offsets:
        pointer = gba_pointer_bytes(text_offset)
        for xref in find_all(data, pointer):
            result["xrefs"].append(
                {
                    "text_offset": text_offset,
                    "pointer_value": GBA_ROM_BASE + text_offset,
                    "xref_offset": xref,
                }
            )

    result["xrefs"].sort(key=lambda item: (item["text_offset"], item["xref_offset"]))
    return result


def classify_script_xref(data: bytes, xref_offset: int, radius: int = 24) -> dict:
    start = max(0, xref_offset - radius)
    end = min(len(data), xref_offset + 4 + radius)
    window = data[start:end]
    rel = xref_offset - start

    loadpointer_prefix = (
        rel >= 2
        and window[rel - 2] == CMD_LOADPOINTER
        and window[rel - 1] == 0x00
    )

    before = window[:rel]
    after = window[rel + 4:]

    markers = {
        "loadpointer_prefix": loadpointer_prefix,
        "has_lock_before": bytes([CMD_LOCK]) in before,
        "has_faceplayer_before": bytes([CMD_FACEPLAYER]) in before,
        "has_trainerbattle_nearby": bytes([CMD_TRAINERBATTLE]) in window,
        "has_msgbox_after": bytes([CMD_MSGBOX_NORMAL]) in after,
        "has_release_after": bytes([CMD_RELEASE]) in after,
        "has_end_after": bytes([CMD_END]) in after,
    }

    score = 0
    score += 4 if markers["loadpointer_prefix"] else 0
    score += 1 if markers["has_lock_before"] else 0
    score += 1 if markers["has_faceplayer_before"] else 0
    score += 1 if markers["has_msgbox_after"] else 0
    score += 1 if markers["has_release_after"] else 0
    score += 1 if markers["has_end_after"] else 0

    if markers["loadpointer_prefix"] and score >= 5:
        classification = "event_dialogue_script"
    elif markers["loadpointer_prefix"]:
        classification = "possible_event_script"
    else:
        classification = "data_or_unknown_reference"

    return {
        "classification": classification,
        "score": score,
        "markers": markers,
    }


def script_context(data: bytes, xref_offset: int, radius: int = 24) -> dict:
    start = max(0, xref_offset - radius)
    end = min(len(data), xref_offset + 4 + radius)
    return {
        "start": start,
        "end": end,
        "xref_offset": xref_offset,
        "xref_index": xref_offset - start,
        "hex": data[start:end].hex(" "),
        **classify_script_xref(data, xref_offset, radius),
    }


def analyze_rom(data: bytes) -> dict:
    patched = discover_text_xrefs(data, encode_text(PORT_LINK_NPC_TEXT))
    source = discover_text_xrefs(data, encode_text(PORT_LINK_NPC_SOURCE_TEXT))

    chosen_label = None
    chosen = None
    if patched["text_offsets"]:
        chosen_label = "patched_port_link_delivery_npc"
        chosen = patched
    elif source["text_offsets"]:
        chosen_label = "source_route1_mart_npc"
        chosen = source

    contexts = []
    if chosen:
        contexts = [
            script_context(data, item["xref_offset"])
            for item in chosen["xrefs"]
        ]

    classified_script_xrefs = sum(
        1
        for context in contexts
        if context["classification"] == "event_dialogue_script"
    )

    return {
        "target": chosen_label,
        "patched_text": patched,
        "source_text": source,
        "candidate_contexts": contexts,
        "classified_script_xrefs": classified_script_xrefs,
        "safe_to_patch": bool(
            chosen
            and len(chosen["text_offsets"]) == 1
            and len(chosen["xrefs"]) >= 1
            and classified_script_xrefs == 1
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Discover and classify deterministic ROM references to the "
            "Route 1/Port Link NPC without modifying the ROM."
        )
    )
    parser.add_argument("rom", type=Path, help="Private local CFRU/RC ROM")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path for the discovery report",
    )
    args = parser.parse_args()

    if not args.rom.is_file():
        print(f"ERROR: ROM not found: {args.rom}")
        return 1

    report = analyze_rom(args.rom.read_bytes())
    rendered = json.dumps(report, indent=2)

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")

    print(rendered)

    if report["target"] is None:
        print("PORT_LINK_DISCOVERY=NOT_FOUND")
        return 2

    if not report["safe_to_patch"]:
        print("PORT_LINK_DISCOVERY=AMBIGUOUS_OR_UNCLASSIFIED")
        return 3

    print("PORT_LINK_DISCOVERY=READY_FOR_TRAINER_PATCH_PLAN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
