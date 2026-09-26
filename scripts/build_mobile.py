#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DPE_ROOT = ROOT.parent / "release-candidate-dpe"
CFRU_BRANCH = "feature/cagliari-preview-0.2-rebuild"
DPE_BRANCH = "feature/cagliari-preview-0.1"
DPE_REMOTE = "https://github.com/PalmasMich/release-candidate-dpe.git"
CANONICAL_OUTPUT = ROOT / "release_candidate_test.gba"


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hashed_output_path(path: Path, digest: str) -> Path:
    return path.with_name(f"release_candidate_{digest[:8]}.gba")


def sync_commands(branch: str) -> list[list[str]]:
    return [
        ["git", "fetch", "origin", branch],
        ["git", "switch", branch],
        ["git", "merge", "--ff-only", f"origin/{branch}"],
    ]


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def ensure_dpe_checkout() -> None:
    if (DPE_ROOT / ".git").exists():
        return
    run(
        ["git", "clone", "--branch", DPE_BRANCH, "--single-branch", DPE_REMOTE, str(DPE_ROOT)],
        ROOT.parent,
    )


def sync_checkout(root: Path, branch: str) -> None:
    for command in sync_commands(branch):
        run(command, root)


def run_tests() -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], DPE_ROOT)
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT)


def build() -> Path:
    run(
        [sys.executable, "scripts/build_release_candidate.py", "--dpe-path", str(DPE_ROOT)],
        ROOT,
    )
    if not CANONICAL_OUTPUT.is_file():
        raise RuntimeError("Build succeeded without release_candidate_test.gba")
    digest = sha1_file(CANONICAL_OUTPUT)
    destination = hashed_output_path(CANONICAL_OUTPUT, digest)
    if destination.exists():
        destination.unlink()
    shutil.move(str(CANONICAL_OUTPUT), str(destination))
    print(f"MOBILE_OUTPUT={destination}")
    print(f"MOBILE_SHA1={digest}")
    print("MOBILE_BUILD_STATUS=SUCCESS")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Update, test, and build Release Candidate from a phone-friendly command.")
    parser.add_argument("--skip-sync", action="store_true", help="Build current local feature branches without fetching remotes.")
    args = parser.parse_args()
    try:
        ensure_dpe_checkout()
        if not args.skip_sync:
            sync_checkout(ROOT, CFRU_BRANCH)
            sync_checkout(DPE_ROOT, DPE_BRANCH)
        run_tests()
        build()
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("MOBILE_BUILD_STATUS=BLOCKED", file=sys.stderr)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
