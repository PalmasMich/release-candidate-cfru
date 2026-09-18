#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA1 = "41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc"
DEFAULT_OUTPUT_NAME = "release_candidate_test.gba"
PIPELINE = ("DPE", "CFRU")


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_pristine_rom(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Private base ROM not found: {path}")
    actual = sha1_file(path)
    if actual != EXPECTED_SHA1:
        raise ValueError(
            "BPRE0.gba SHA-1 mismatch. "
            f"Expected {EXPECTED_SHA1}, got {actual}."
        )
    return actual


def default_run_build(label: str, cwd: Path) -> None:
    print(f"\n== {label} build ==")
    subprocess.run(
        [sys.executable, "scripts/make.py"],
        cwd=cwd,
        check=True,
    )


def run_pipeline(
    *,
    cfru_root: Path,
    dpe_root: Path,
    output_path: Path,
    run_build=default_run_build,
    verify_rom=verify_pristine_rom,
) -> Path:
    cfru_root = Path(cfru_root).resolve()
    dpe_root = Path(dpe_root).resolve()
    output_path = Path(output_path).resolve()

    cfru_rom = cfru_root / "BPRE0.gba"
    dpe_rom = dpe_root / "BPRE0.gba"
    dpe_output = dpe_root / "test.gba"
    cfru_output = cfru_root / "test.gba"

    verify_rom(cfru_rom)

    if not (dpe_root / "scripts" / "make.py").is_file():
        raise FileNotFoundError(f"DPE build entrypoint not found under {dpe_root}")
    if not (cfru_root / "scripts" / "make.py").is_file():
        raise FileNotFoundError(f"CFRU build entrypoint not found under {cfru_root}")

    original = cfru_rom.read_bytes()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        for path in (dpe_rom, dpe_output, cfru_output):
            if path.exists():
                path.unlink()

        shutil.copy2(cfru_rom, dpe_rom)
        pristine_hash = sha1_file(dpe_rom)
        run_build("DPE", dpe_root)

        if not dpe_output.exists():
            raise RuntimeError("DPE build finished without test.gba")
        dpe_hash = sha1_file(dpe_output)
        if dpe_hash == pristine_hash:
            raise RuntimeError("DPE test.gba is identical to the pristine input")

        shutil.copy2(dpe_output, cfru_rom)
        run_build("CFRU", cfru_root)

        if not cfru_output.exists():
            raise RuntimeError("CFRU build finished without test.gba")
        cfru_hash = sha1_file(cfru_output)
        if cfru_hash == dpe_hash:
            raise RuntimeError("CFRU test.gba is identical to the DPE input")

        shutil.copy2(cfru_output, output_path)
        print(f"\nDPE_SHA1={dpe_hash}")
        print(f"CFRU_SHA1={cfru_hash}")
        print(f"OUTPUT={output_path}")
        print(f"OUTPUT_SHA1={sha1_file(output_path)}")
        return output_path
    finally:
        cfru_rom.write_bytes(original)
        for path in (dpe_rom, dpe_output, cfru_output):
            if path.exists():
                path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Release Candidate safely in one command: pristine FireRed -> DPE -> CFRU."
    )
    parser.add_argument(
        "--dpe-path",
        default=str(ROOT.parent / "release-candidate-dpe"),
        help="Path to the release-candidate-dpe checkout.",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / DEFAULT_OUTPUT_NAME),
        help="Private output ROM path. *.gba remains git-ignored.",
    )
    args = parser.parse_args()

    dpe_root = Path(args.dpe_path).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    print("Release Candidate one-command build")
    print(f"CFRU={ROOT}")
    print(f"DPE={dpe_root}")
    print("PIPELINE=DPE -> CFRU")
    print(f"BASE_SHA1={EXPECTED_SHA1}")

    try:
        run_pipeline(
            cfru_root=ROOT,
            dpe_root=dpe_root,
            output_path=output_path,
        )
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("BUILD_STATUS=SUCCESS")
    print("Pristine CFRU BPRE0.gba restored after build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
