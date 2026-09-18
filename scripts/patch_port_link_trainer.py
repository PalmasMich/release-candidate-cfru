#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_PATH = ROOT / "scripts" / "discover_port_link_trainer_script.py"

TRAINER_DEFEAT_TEXT = "Please, report at MARINA PORTO."


def load_discovery():
    spec = importlib.util.spec_from_file_location("port_link_discovery", DISCOVERY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_exactly_one(data: bytes, needle: bytes, label: str) -> int:
    positions = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 1
    if len(positions) != 1:
        raise ValueError(f"Expected exactly one {label}, found {len(positions)}.")
    return positions[0]


def build_trainer_script(discovery, intro_text_offset: int, defeat_text_offset: int) -> bytes:
    # FireRed trainerbattle TRAINER_BATTLE_SINGLE:
    # opcode, type, trainer(u16), local_id(u16), intro_ptr(u32), defeat_ptr(u32)
    return (
        bytes([
            discovery.CMD_LOCK,
            discovery.CMD_FACEPLAYER,
            discovery.CMD_TRAINERBATTLE,
            discovery.TRAINER_BATTLE_SINGLE,
        ])
        + discovery.TRAINER_BOOTSTRAP_ID.to_bytes(2, "little")
        + (0).to_bytes(2, "little")
        + (discovery.GBA_ROM_BASE + intro_text_offset).to_bytes(4, "little")
        + (discovery.GBA_ROM_BASE + defeat_text_offset).to_bytes(4, "little")
        + bytes([
            discovery.CMD_RELEASE,
            discovery.CMD_END,
        ])
    )


def patch_bytes(data: bytes) -> tuple[bytes, dict]:
    discovery = load_discovery()
    report = discovery.analyze_rom(data)
    if not report["safe_to_patch"]:
        raise ValueError("Port Link script discovery is not uniquely safe to patch.")

    candidates = [
        context
        for context in report["candidate_contexts"]
        if context["classification"] == "event_dialogue_script"
    ]
    if len(candidates) != 1:
        raise ValueError(f"Expected one classified Port Link event script, found {len(candidates)}.")

    context = candidates[0]
    plan = context["patch_plan"]
    if plan is None:
        raise ValueError("Classified Port Link event script has no guarded patch plan.")

    script_start = plan["script_start_candidate"]
    signature = bytes.fromhex(plan["verification_signature_hex"])
    if data[script_start:script_start + len(signature)] != signature:
        raise ValueError("Port Link script verification signature mismatch.")

    intro_offsets = report["patched_text"]["text_offsets"]
    if len(intro_offsets) != 1:
        raise ValueError("Expected exactly one patched Port Link intro text.")

    defeat_text = discovery.encode_text(TRAINER_DEFEAT_TEXT)
    defeat_offset = find_exactly_one(data, defeat_text, "Port Link trainer defeat text")

    replacement = build_trainer_script(
        discovery,
        intro_text_offset=intro_offsets[0],
        defeat_text_offset=defeat_offset,
    )

    if len(replacement) > len(signature):
        raise ValueError(
            "Trainer bootstrap script is larger than the guarded replacement signature "
            f"({len(replacement)} > {len(signature)})."
        )

    patched = bytearray(data)
    patched[script_start:script_start + len(replacement)] = replacement

    evidence = {
        "script_start": script_start,
        "signature_length": len(signature),
        "replacement_length": len(replacement),
        "trainer_id": discovery.TRAINER_BOOTSTRAP_ID,
        "intro_text_offset": intro_offsets[0],
        "defeat_text_offset": defeat_offset,
    }
    return bytes(patched), evidence


def patch_rom(source: Path, output: Path) -> Path:
    if not source.is_file():
        raise FileNotFoundError(f"Input ROM not found: {source}")

    original = source.read_bytes()
    patched, evidence = patch_bytes(original)

    if len(patched) != len(original):
        raise RuntimeError("Port Link trainer patch changed ROM size unexpectedly.")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patched)

    print("PORT_LINK_TRAINER_PATCH=BOOTSTRAP")
    print(f"PORT_LINK_TRAINER_ID={evidence['trainer_id']}")
    print(f"PORT_LINK_SCRIPT_OFFSET=0x{evidence['script_start']:X}")
    print(f"PORT_LINK_INTRO_OFFSET=0x{evidence['intro_text_offset']:X}")
    print(f"PORT_LINK_DEFEAT_OFFSET=0x{evidence['defeat_text_offset']:X}")
    print(f"PORT_LINK_TRAINER_OUTPUT={output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply the guarded Port Link trainer bootstrap patch to a private RC ROM."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        patch_rom(args.source, args.output)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
