#!/usr/bin/env bash
set -euo pipefail

CFRU_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACES_DIR="$(dirname "$CFRU_DIR")"
DPE_DIR="$WORKSPACES_DIR/release-candidate-dpe"
DPE_REPO="https://github.com/PalmasMich/release-candidate-dpe.git"
DPE_BRANCH="feature/cagliari-preview-0.1"
EXPECTED_SHA1="41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc"
WAV2AGB_REPO="https://github.com/ipatix/wav2agb.git"
WAV2AGB_COMMIT="7279d3cf899e53154482bcdcd66a483f6a4572ba"
WAV2AGB_DIR="/tmp/rc-wav2agb"
MID2AGB_REPO="https://github.com/ipatix/midi2agb.git"
MID2AGB_COMMIT="19a6f83f94af9efddc764dfe0b2e3dd86bf25e96"
MID2AGB_DIR="/tmp/rc-midi2agb"

printf '\n== Release Candidate Codespace bootstrap ==\n'

for command in python git arm-none-eabi-gcc grit make g++; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "ERROR: required tool not found: $command" >&2
    exit 1
  fi
done

if ! command -v mid2agb >/dev/null 2>&1; then
  echo "Installing mid2agb Linux tool ..."
  rm -rf "$MID2AGB_DIR"
  git clone --recurse-submodules "$MID2AGB_REPO" "$MID2AGB_DIR"
  cd "$MID2AGB_DIR"
  git checkout "$MID2AGB_COMMIT"
  git submodule update --init --recursive
  make
  install -m 0755 midi2agb /usr/local/bin/mid2agb
  cd "$CFRU_DIR"
fi

if ! command -v mid2agb >/dev/null 2>&1; then
  echo "ERROR: mid2agb installation failed." >&2
  exit 1
fi

if ! command -v wav2agb >/dev/null 2>&1; then
  echo "Installing wav2agb Linux tool ..."
  rm -rf "$WAV2AGB_DIR"
  git clone "$WAV2AGB_REPO" "$WAV2AGB_DIR"
  cd "$WAV2AGB_DIR"
  git checkout "$WAV2AGB_COMMIT"
  make
  install -m 0755 wav2agb /usr/local/bin/wav2agb
  cd "$CFRU_DIR"
fi

if ! command -v wav2agb >/dev/null 2>&1; then
  echo "ERROR: wav2agb installation failed." >&2
  exit 1
fi

if [ ! -d "$DPE_DIR/.git" ]; then
  echo "Cloning DPE branch into $DPE_DIR ..."
  git clone --branch "$DPE_BRANCH" --single-branch "$DPE_REPO" "$DPE_DIR"
else
  echo "DPE workspace already present: $DPE_DIR"
fi

cd "$DPE_DIR"
git checkout "$DPE_BRANCH" --quiet
ACTIVE_DPE_BRANCH="$(git branch --show-current)"
if [ "$ACTIVE_DPE_BRANCH" != "$DPE_BRANCH" ]; then
  echo "ERROR: DPE checkout is on $ACTIVE_DPE_BRANCH, expected $DPE_BRANCH." >&2
  exit 1
fi
echo "DPE_BRANCH_OK=$ACTIVE_DPE_BRANCH"

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
  echo "NEXT: python scripts/build_release_candidate.py"
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
wav2agb --help 2>&1 | head -n 1 || true
mid2agb --help 2>&1 | head -n 1 || true

printf '\nCodespace setup complete.\n'
