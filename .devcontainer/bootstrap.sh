#!/usr/bin/env bash
set -euo pipefail

CFRU_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACES_DIR="$(dirname "$CFRU_DIR")"
DPE_DIR="$WORKSPACES_DIR/release-candidate-dpe"
DPE_REPO="https://github.com/PalmasMich/release-candidate-dpe.git"
DPE_BRANCH="feature/cagliari-preview-0.1"
EXPECTED_SHA1="41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc"

printf '\n== Release Candidate Codespace bootstrap ==\n'

for command in python git arm-none-eabi-gcc grit; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "ERROR: required tool not found: $command" >&2
    exit 1
  fi
done

if [ ! -d "$DPE_DIR/.git" ]; then
  echo "Cloning DPE branch into $DPE_DIR ..."
  git clone --branch "$DPE_BRANCH" --single-branch "$DPE_REPO" "$DPE_DIR"
else
  echo "DPE workspace already present: $DPE_DIR"
fi

cd "$DPE_DIR"
git checkout "$DPE_BRANCH" >/dev/null 2>&1 || true

cd "$CFRU_DIR"
python scripts/validate_release_candidate_workspace.py --dpe-path "$DPE_DIR"

ROM="$CFRU_DIR/BPRE0.gba"
if [ -f "$ROM" ]; then
  ACTUAL_SHA1="$(sha1sum "$ROM" | awk '{print $1}')"
  if [ "$ACTUAL_SHA1" != "$EXPECTED_SHA1" ]; then
    echo "ERROR: BPRE0.gba has the wrong SHA-1." >&2
    echo "Expected: $EXPECTED_SHA1" >&2
    echo "Actual:   $ACTUAL_SHA1" >&2
    exit 1
  fi
  echo "ROM_OK: FireRed USA v1.0 SHA-1 verified."
else
  echo
  echo "BLOCKED_LOCAL_ROM: upload your verified FireRed USA v1.0 file to:"
  echo "  $ROM"
  echo "Then rerun: bash .devcontainer/bootstrap.sh"
fi

printf '\nToolchain versions:\n'
python --version
arm-none-eabi-gcc --version | head -n 1
grit --version 2>/dev/null | head -n 1 || true

printf '\nCodespace setup complete.\n'
