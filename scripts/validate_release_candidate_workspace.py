#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

MIN_PYTHON = (3, 8)
ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> int:
    print(f"ERROR: {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Release Candidate CFRU/DPE workspace contract.")
    parser.add_argument(
        "--dpe-path",
        required=True,
        help="Path to the release-candidate-dpe checkout.",
    )
    args = parser.parse_args()

    if sys.version_info < MIN_PYTHON:
        return fail(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required")

    cfru_make = ROOT / "scripts" / "make.py"
    if not cfru_make.exists():
        return fail(f"Missing CFRU build entrypoint: {cfru_make}")

    dpe_root = Path(args.dpe_path).expanduser().resolve()
    dpe_make = dpe_root / "scripts" / "make.py"
    if not dpe_make.exists():
        return fail(f"Missing DPE build entrypoint: {dpe_make}")

    rom = ROOT / "BPRE0.gba"
    print("Release Candidate workspace")
    print(f"CFRU: {ROOT}")
    print(f"DPE:  {dpe_root}")
    print("Insertion order: DPE -> CFRU")

    if rom.exists():
        print("ROM_STATUS=LOCAL_ROM_PRESENT")
    else:
        print("ROM_STATUS=BLOCKED_LOCAL_ROM")
        print("A legally obtained FireRed 1.0 ROM named BPRE0.gba is required only for insertion/build testing.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
