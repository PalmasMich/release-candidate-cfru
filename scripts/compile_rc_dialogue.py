#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIALOGUE_PATH = ROOT / "content" / "cagliari_preview" / "dialogue.yml"

# Verified against pret/pokefirered charmap.txt.
CHARMAP = {
    **{chr(ord("A") + i): 0xBB + i for i in range(26)},
    **{chr(ord("a") + i): 0xD5 + i for i in range(26)},
    **{str(i): 0xA1 + i for i in range(10)},
    " ": 0x00,
    "À": 0x01, "È": 0x05, "É": 0x06, "Ì": 0x09, "Ò": 0x0D, "Ù": 0x11,
    "à": 0x16, "è": 0x1A, "é": 0x1B, "ì": 0x1E, "ò": 0x22, "ù": 0x26,
    "&": 0x2D, "+": 0x2E, "=": 0x35, ";": 0x36,
    "%": 0x5B, "(": 0x5C, ")": 0x5D,
    "!": 0xAB, "?": 0xAC, ".": 0xAD, "-": 0xAE,
    "'": 0xB4, "’": 0xB4, ",": 0xB8, "/": 0xBA, ":": 0xF0,
}
NEWLINE = 0xFE
EOS = 0xFF


def load_dialogue(path: Path = DIALOGUE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def encode_text(text: str) -> bytes:
    output = bytearray()
    for ch in text:
        if ch == "\n":
            output.append(NEWLINE)
            continue
        if ch not in CHARMAP:
            raise ValueError(f"unsupported FireRed text character: {ch!r}")
        output.append(CHARMAP[ch])
    return bytes(output)


def compile_scene(scene: dict) -> dict:
    lines = scene["lines"]
    if not lines:
        raise ValueError(f"{scene['id']}: dialogue scene has no lines")

    blob = bytearray()
    for index, line in enumerate(lines):
        blob.extend(encode_text(line))
        if index != len(lines) - 1:
            blob.append(NEWLINE)
    blob.append(EOS)

    return {
        "id": scene["id"],
        "speaker": scene.get("speaker"),
        "size": len(blob),
        "bytes_hex": blob.hex(" "),
    }


def compile_dialogue(data: dict) -> dict:
    scenes = [compile_scene(scene) for scene in data["scenes"]]
    ids = [scene["id"] for scene in scenes]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate dialogue ids")
    return {
        "format": "RC_DIALOGUE_IR_V1",
        "scenes": scenes,
    }


def compile_file(source: Path = DIALOGUE_PATH, output: Path | None = None) -> dict:
    ir = compile_dialogue(load_dialogue(source))
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(ir, indent=2) + "\n", encoding="utf-8")
    return ir


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile Release Candidate dialogue into FireRed text blobs.")
    parser.add_argument("source", nargs="?", type=Path, default=DIALOGUE_PATH)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        ir = compile_file(args.source, args.output)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"RC_DIALOGUE_INVALID: {exc}")
        return 1

    print(f"RC_DIALOGUE_VALID={len(ir['scenes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
