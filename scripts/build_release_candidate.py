#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA1 = "41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc"
DEFAULT_OUTPUT_NAME = "release_candidate_test.gba"
DPE_BRANCH = "feature/cagliari-preview-0.1"
PIPELINE = ("CHAPTER1_PREFLIGHT", "DPE", "CFRU", "RC_PREVIEW_PATCH", "RC_OPENING_AUDIT", "PORT_LINK_DISCOVERY", "PORT_LINK_TRAINER_PATCH", "DELIVERY_HUB_MAP_PLAN", "RC_CUSTOM_MAPS_PATCH")
RC_LEARNSET_TABLE = Path("src/Tables/level_up_learnsets.c")


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
        raise ValueError(f"BPRE0.gba SHA-1 mismatch. Expected {EXPECTED_SHA1}, got {actual}.")
    return actual


def sync_dpe_checkout(dpe_root: Path) -> None:
    print("\n== Sync DPE preview branch ==")
    subprocess.run(["git", "-c", f"safe.directory={dpe_root}", "fetch", "origin", DPE_BRANCH], cwd=dpe_root, check=True)
    subprocess.run(["git", "-c", f"safe.directory={dpe_root}", "checkout", DPE_BRANCH], cwd=dpe_root, check=True)
    subprocess.run(["git", "-c", f"safe.directory={dpe_root}", "merge", "--ff-only", f"origin/{DPE_BRANCH}"], cwd=dpe_root, check=True)


def verify_dpe_tartrek_symbols(dpe_root: Path) -> None:
    offsets = Path(dpe_root) / "offsets.ini"
    if not offsets.is_file():
        raise RuntimeError("DPE build did not produce offsets.ini for RC preview verification.")
    text = offsets.read_text(encoding="utf-8")
    required = (
        "gFrontSprite1294RCTartrekTiles", "gBackShinySprite1294RCTartrekTiles", "gIconSprite1294RCTartrekTiles",
        "gFrontSprite1294RCTartrekPal", "gBackShinySprite1294RCTartrekPal",
        "gFrontSprite1295RCFrobyteTiles", "gBackShinySprite1295RCFrobyteTiles", "gIconSprite1295RCFrobyteTiles",
        "gFrontSprite1295RCFrobytePal", "gBackShinySprite1295RCFrobytePal",
        "gFrontSprite1296RCEmberfoxTiles", "gBackShinySprite1296RCEmberfoxTiles", "gIconSprite1296RCEmberfoxTiles",
        "gFrontSprite1296RCEmberfoxPal", "gBackShinySprite1296RCEmberfoxPal",
        "gFrontSprite1297RCMistrilloTiles", "gBackShinySprite1297RCMistrilloTiles", "gIconSprite1297RCMistrilloTiles",
        "gFrontSprite1297RCMistrilloPal", "gBackShinySprite1297RCMistrilloPal",
    )
    missing = [symbol for symbol in required if symbol not in text]
    if missing:
        raise RuntimeError("DPE build is missing RC preview sprite symbols: " + ", ".join(missing))
    print("DPE_RC_PREVIEW_SYMBOLS=OK")


def activate_rc_learnset_pointers(cfru_root: Path) -> bytes:
    """Repair the preview-only pointer tail in the private build workspace.

    A previous source edit left Tartrek's pointer immediately before the end of
    an upstream block comment. Rather than rewriting this very large generated
    CFRU table in Git, the build makes the one-line correction transactionally
    and restores the checkout afterward.
    """
    table = Path(cfru_root) / RC_LEARNSET_TABLE
    original = table.read_bytes()
    text = original.decode("utf-8")
    active = "\t[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset,\n\t[SPECIES_RC_CAGLIARI_WILD_01]"
    if active in text:
        return original
    anchor = "\t[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset,\n};\n*/\n\t[SPECIES_RC_CAGLIARI_WILD_01]"
    replacement = "\t[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset,\n};\n*/\n\t[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset,\n\t[SPECIES_RC_CAGLIARI_WILD_01]"
    if anchor not in text:
        raise RuntimeError("Could not locate the RC learnset pointer tail; refusing an ambiguous CFRU build.")
    table.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
    print("CFRU_RC_LEARNSET_POINTERS=ACTIVE")
    return original


def default_run_preflight() -> None:
    print("\n== Chapter 1 source preflight ==")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "preflight_chapter1.py")],
        cwd=ROOT,
        check=True,
    )


def default_run_build(label: str, cwd: Path) -> None:
    print(f"\n== {label} build ==")
    subprocess.run([sys.executable, "scripts/make.py"], cwd=cwd, check=True)


def default_apply_preview_patch(source: Path, output: Path) -> None:
    print("\n== Release Candidate preview patch ==")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "apply_release_candidate_preview_patch.py"), str(source), str(output)], cwd=ROOT, check=True)


def default_audit_opening(output_path: Path) -> None:
    print("\n== Release Candidate opening audit ==")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit_rc_opening.py"), str(output_path)],
        cwd=ROOT,
        check=True,
    )


def default_discover_port_link(output_path: Path) -> int:
    print("\n== Port Link script discovery ==")
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "discover_port_link_trainer_script.py"), str(output_path)], cwd=ROOT, check=False).returncode


def default_apply_port_link_trainer(source: Path, output: Path) -> int:
    print("\n== Port Link trainer bootstrap patch ==")
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "patch_port_link_trainer.py"), str(source), str(output)], cwd=ROOT, check=False).returncode


def default_prepare_delivery_hub_map(output_path: Path) -> int:
    print("\n== Delivery Hub custom-map plan ==")
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "prepare_delivery_hub_map_patch.py"), str(output_path)], cwd=ROOT, check=False).returncode


def default_apply_custom_maps(source: Path, output: Path) -> int:
    print("\n== Release Candidate custom maps patch ==")
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "patch_rc_custom_maps.py"), str(source), str(output)],
        cwd=ROOT,
        check=False,
    ).returncode


def run_pipeline(*, cfru_root: Path, dpe_root: Path, output_path: Path,
                 run_preflight=default_run_preflight, run_build=default_run_build,
                 verify_rom=verify_pristine_rom, sync_dpe=sync_dpe_checkout,
                 verify_dpe_symbols=verify_dpe_tartrek_symbols, apply_preview_patch=default_apply_preview_patch,
                 audit_opening=default_audit_opening, discover_port_link=default_discover_port_link, apply_port_link_trainer=default_apply_port_link_trainer,
                 prepare_delivery_hub_map=default_prepare_delivery_hub_map,
                 apply_custom_maps=default_apply_custom_maps) -> Path:
    cfru_root, dpe_root, output_path = Path(cfru_root).resolve(), Path(dpe_root).resolve(), Path(output_path).resolve()
    run_preflight()
    cfru_rom, dpe_rom = cfru_root / "BPRE0.gba", dpe_root / "BPRE0.gba"
    dpe_output, cfru_output = dpe_root / "test.gba", cfru_root / "test.gba"
    learnset_table = cfru_root / RC_LEARNSET_TABLE
    verify_rom(cfru_rom)
    if not (dpe_root / "scripts" / "make.py").is_file():
        raise FileNotFoundError(f"DPE build entrypoint not found under {dpe_root}")
    if not (cfru_root / "scripts" / "make.py").is_file():
        raise FileNotFoundError(f"CFRU build entrypoint not found under {cfru_root}")
    original_rom = cfru_rom.read_bytes()
    original_learnsets = learnset_table.read_bytes()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sync_dpe(dpe_root)
    try:
        for path in (dpe_rom, dpe_output, cfru_output):
            if path.exists(): path.unlink()
        shutil.copy2(cfru_rom, dpe_rom)
        pristine_hash = sha1_file(dpe_rom)
        run_build("DPE", dpe_root)
        verify_dpe_symbols(dpe_root)
        if not dpe_output.exists(): raise RuntimeError("DPE build finished without test.gba")
        dpe_hash = sha1_file(dpe_output)
        if dpe_hash == pristine_hash: raise RuntimeError("DPE test.gba is identical to the pristine input")
        shutil.copy2(dpe_output, cfru_rom)
        activate_rc_learnset_pointers(cfru_root)
        run_build("CFRU", cfru_root)
        if not cfru_output.exists(): raise RuntimeError("CFRU build finished without test.gba")
        cfru_hash = sha1_file(cfru_output)
        if cfru_hash == dpe_hash: raise RuntimeError("CFRU test.gba is identical to the DPE input")
        if output_path.exists(): output_path.unlink()
        apply_preview_patch(cfru_output, output_path)
        if not output_path.exists(): raise RuntimeError("Release Candidate preview patch did not produce an output ROM")
        output_hash = sha1_file(output_path)
        if output_hash == cfru_hash: raise RuntimeError("Preview output is identical to the CFRU input")
        audit_opening(output_path)
        discovery_status = discover_port_link(output_path)
        if discovery_status == 0:
            print("PORT_LINK_DISCOVERY_STATUS=READY")
            trainer_output = output_path.with_name(output_path.stem + "_trainer" + output_path.suffix)
            if trainer_output.exists(): trainer_output.unlink()
            try:
                trainer_patch_status = apply_port_link_trainer(output_path, trainer_output)
                if trainer_patch_status == 0 and trainer_output.exists():
                    shutil.move(str(trainer_output), str(output_path)); output_hash = sha1_file(output_path)
                    print("PORT_LINK_TRAINER_STATUS=APPLIED")
                else: print(f"PORT_LINK_TRAINER_STATUS=PENDING:{trainer_patch_status}")
            finally:
                if trainer_output.exists(): trainer_output.unlink()
        else:
            print(f"PORT_LINK_DISCOVERY_STATUS=PENDING:{discovery_status}")
            print("PORT_LINK_TRAINER_STATUS=PENDING:DISCOVERY")
        delivery_hub_status = prepare_delivery_hub_map(output_path)
        print("DELIVERY_HUB_MAP_PLAN_STATUS=READY" if delivery_hub_status == 0 else f"DELIVERY_HUB_MAP_PLAN_STATUS=PENDING:{delivery_hub_status}")

        if delivery_hub_status == 0:
            maps_output = output_path.with_name(output_path.stem + "_custom_maps" + output_path.suffix)
            if maps_output.exists(): maps_output.unlink()
            try:
                custom_maps_status = apply_custom_maps(output_path, maps_output)
                if custom_maps_status == 0 and maps_output.exists():
                    shutil.move(str(maps_output), str(output_path))
                    output_hash = sha1_file(output_path)
                    print("RC_CUSTOM_MAPS_STATUS=APPLIED")
                else:
                    print(f"RC_CUSTOM_MAPS_STATUS=PENDING:{custom_maps_status}")
            finally:
                if maps_output.exists(): maps_output.unlink()
        else:
            print("RC_CUSTOM_MAPS_STATUS=PENDING:MAP_PLAN")

        print(f"\nDPE_SHA1={dpe_hash}\nCFRU_SHA1={cfru_hash}\nOUTPUT={output_path}\nOUTPUT_SHA1={output_hash}")
        return output_path
    finally:
        cfru_rom.write_bytes(original_rom)
        learnset_table.write_bytes(original_learnsets)
        for path in (dpe_rom, dpe_output, cfru_output):
            if path.exists(): path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Release Candidate safely in one command: pristine FireRed -> DPE -> CFRU.")
    parser.add_argument("--dpe-path", default=str(ROOT.parent / "release-candidate-dpe"), help="Path to the release-candidate-dpe checkout.")
    parser.add_argument("--output", default=str(ROOT / DEFAULT_OUTPUT_NAME), help="Private output ROM path. *.gba remains git-ignored.")
    args = parser.parse_args()
    print("Release Candidate one-command build")
    print(f"CFRU={ROOT}\nDPE={Path(args.dpe_path).expanduser().resolve()}")
    print("PIPELINE=CHAPTER1_PREFLIGHT -> DPE -> CFRU -> RC_PREVIEW_PATCH -> RC_OPENING_AUDIT -> PORT_LINK_DISCOVERY -> PORT_LINK_TRAINER_PATCH -> DELIVERY_HUB_MAP_PLAN -> RC_CUSTOM_MAPS_PATCH")
    print(f"BASE_SHA1={EXPECTED_SHA1}")
    try:
        run_pipeline(cfru_root=ROOT, dpe_root=Path(args.dpe_path).expanduser().resolve(), output_path=Path(args.output).expanduser().resolve())
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 1
    print("BUILD_STATUS=SUCCESS\nPristine CFRU BPRE0.gba and generated learnset table restored after build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
