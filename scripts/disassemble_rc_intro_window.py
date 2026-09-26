#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

from discover_rc_intro_bypass import ROM_BASE, discover_prompt_pointer_refs


def main() -> int:
    parser = argparse.ArgumentParser(description="Disassemble the FireRed rival-intro control-flow window.")
    parser.add_argument("rom", type=Path)
    parser.add_argument("--radius", type=lambda x: int(x, 0), default=0x180)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    _, refs = discover_prompt_pointer_refs(data)
    if len(refs) != 1:
        raise RuntimeError(f"expected one rival-intro pointer reference, found {len(refs)}")

    center = refs[0].literal_offset
    start = max(0, center - args.radius) & ~1
    end = min(len(data), center + args.radius)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print(f"RC_INTRO_DISASM_RANGE=0x{start:08X}-0x{end:08X}")
    for insn in md.disasm(data[start:end], ROM_BASE + start):
        print(f"{insn.address:08X}: {insn.mnemonic:<7} {insn.op_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
