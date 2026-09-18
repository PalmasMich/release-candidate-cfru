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
DPE_BRANCH = "feature/cagliari-preview-0.1"
PIPELINE = ("DPE", "CFRU", "RC_PREVIEW_PATCH", "PORT_LINK_DISCOVERY")


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


def sync_dpe_checkout(dpe_root: Path) -> None:
    print("\n== Sync DPE preview branch ==")
    subprocess.run(
        ["git", "-c", f"safe.directory={dpe_root}", "fetch", "origin", DPE_BRANCH],
        cwd=dpe_root,
        check=True,
    )
    subprocess.run(
        ["git", "-c", f"safe.directory={dpe_root}", "checkout", DPE_BRANCH],
        cwd=dpe_root,
        check=True,
    )
    subprocess.run(
        ["git", "-c", f"safe.directory={dpe_root}", "merge", "--ff-only", f"origin/{DPE_BRANCH}"],
        cwd=dpe_root,
        check=True,
    )


def verify_dpe_tartrek_symbols(dpe_root: Path) -> None:
    offsets = Path(dpe_root) / "offsets.ini"
    if not offsets.is_file():
        raise RuntimeError("DPE build did not produce offsets.ini for Tartrek verification.")

    text = offsets.read_text(encoding="utf-8")
    required = (
        "gFrontSprite1294RCTartrekTiles",
        "gBackShinySprite1294RCTartrekTiles",
        "gIconSprite1294RCTartrekTiles",
        "gFrontSprite1294RCTartrekPal",
        "gBackShinySprite1294RCTartrekPal",
        "gFrontSprite1295RCFrobyteTiles",
        "gBackShinySprite1295RCFrobyteTiles",
        "gIconSprite1295RCFrobyteTiles",
        "gFrontSprite1295RCFrobytePal",
        "gBackShinySprite1295RCFrobytePal",
        "gFrontSprite1296RCEmberfoxTiles",
        "gBackShinySprite1296RCEmberfoxTiles",
        "gIconSprite1296RCEmberfoxTiles",
        "gFrontSprite1296RCEmberfoxPal",
        "gBackShinySprite1296RCEmberfoxPal",
        "gFrontSprite1297RCMistrilloTiles",
        "gBackShinySprite1297RCMistrilloTiles",
        "gIconSprite1297RCMistrilloTiles",
        "gFrontSprite1297RCMistrilloPal",
        "gBackShinySprite1297RCMistrilloPal",
    )
    missing = [symbol for symbol in required if symbol not in text]
    if missing:
        raise RuntimeError(
            "DPE build is missing Tartrek sprite symbols: " + ", ".join(missing)
        )
    print("DPE_RC_PREVIEW_SYMBOLS=OK")


def default_run_build(label: str, cwd: Path) -> None:
    print(f"\n== {label} build ==")
    subprocess.run(
        [sys.executable, "scripts/make.py"],
        cwd=cwd,
        check=True,
    )


def default_apply_preview_patch(source: Path, output: Path) -> None:
    print("\n== Release Candidate preview patch ==")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "apply_release_candidate_preview_patch.py"),
            str(source),
            str(output),
        ],
        cwd=ROOT,
        check=True,
    )


def run_pipeline(
    *,
    cfru_root: Path,
    dpe_root: Path,
    output_path: Path,
    run_build=default_run_build,
    verify_rom=verify_pristine_rom,
    sync_dpe=sync_dpe_checkout,
    verify_dpe_symbols=verify_dpe_tartrek_symbols,
    apply_preview_patch=default_apply_preview_patch,
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

    sync_dpe(dpe_root)

    try:
        for path in (dpe_rom, dpe_output, cfru_output):
            if path.exists():
                path.unlink()

        shutil.copy2(cfru_rom, dpe_rom)
        pristine_hash = sha1_file(dpe_rom)
        run_build("DPE", dpe_root)
        verify_dpe_symbols(dpe_root)

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

        if output_path.exists():
            output_path.unlink()
        apply_preview_patch(cfru_output, output_path)
        if not output_path.exists():
            raise RuntimeError("Release Candidate preview patch did not produce an output ROM")
        output_hash = sha1_file(output_path)
        if output_hash == cfru_hash:
            raise RuntimeError("Preview output is identical to the CFRU input")

        print(f"\nDPE_SHA1={dpe_hash}")
        print(f"CFRU_SHA1={cfru_hash}")
        print(f"OUTPUT={output_path}")
        print(f"OUTPUT_SHA1={output_hash}")
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
    print("PIPELINE=DPE -> CFRU -> RC_PREVIEW_PATCH -> PORT_LINK_DISCOVERY")
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
