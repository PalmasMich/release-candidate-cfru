# Release Candidate ROM Build Contract

This project uses two source repositories plus one private local ROM input.

## Repository responsibilities

- `release-candidate-dpe`: original Release Candidate species data, sprite/icon/cry integration and expanded Pokémon data.
- `release-candidate-cfru`: battle/runtime engine integration, Release Candidate manifests, validation scripts and build documentation.
- local working ROM: map/event/script edits applied only to a private disposable copy derived from a legally obtained Pokémon FireRed 1.0 ROM.

## Non-negotiable ROM rule

`BPRE0.gba`, generated `test.gba`, save files and other ROM-derived binaries must never be committed to GitHub.

The CFRU `.gitignore` already excludes `*.gba`; every release checkpoint must also verify that no ROM binary is tracked.

## Required insertion order

The supported order is:

`DPE -> CFRU`

DPE expands and repoints the Pokémon data first. CFRU is then applied to the DPE-expanded working ROM, matching the upstream DPE recommendation.

## Local build procedure

1. Obtain a lawful Pokémon FireRed 1.0 ROM locally.
2. Keep a pristine backup outside both repositories.
3. Name the private working input `BPRE0.gba`.
4. Place/copy the local input into the DPE workspace only for the build operation.
5. In `release-candidate-dpe`, run:

   ```bash
   python scripts/make.py
   ```

6. Preserve the generated DPE-expanded ROM only in the private local workspace.
7. Use that expanded ROM as the CFRU local input named `BPRE0.gba`.
8. In `release-candidate-cfru`, run:

   ```bash
   python scripts/make.py
   ```

9. Apply Cagliari map/event changes only to a disposable private working ROM, following the source-controlled manifests in `content/cagliari_preview/` once they exist.
10. Test in an emulator against the exact CFRU and DPE commit SHAs recorded in `docs/rom/BUILD_VERIFICATION.md`.

## Workspace validation

Run from the CFRU repository:

```bash
python scripts/validate_release_candidate_workspace.py --dpe-path ../release-candidate-dpe
```

The validator checks source paths and reports one of:

- `ROM_STATUS=LOCAL_ROM_PRESENT`
- `ROM_STATUS=BLOCKED_LOCAL_ROM`

`BLOCKED_LOCAL_ROM` is expected while working only from GitHub/cloud tooling and is not considered a repository defect.

## Source control strategy for binary ROM edits

CFRU/DPE are binary-insertion projects rather than a full FireRed decomp. Therefore GitHub stores the reproducible intent of binary edits rather than a ROM image:

- dialogue/event manifests;
- encounter and trainer manifests;
- original tiles/sprites/palettes;
- mapping guide and implementation IDs;
- build/tool versions and verification results;
- patch-generation metadata when distribution is approved.

The working ROM itself remains private/local.

## Distribution

Release Candidate ROM is a non-commercial fan project. If a distributable preview is later approved, distribute only a patch against the required lawful base ROM, never the complete ROM image.
