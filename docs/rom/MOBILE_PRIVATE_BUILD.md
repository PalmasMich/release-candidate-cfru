# Release Candidate — private build from mobile / Codespaces

This runbook is for a private, legally obtained FireRed 1.0 ROM only.

The ROM must **never** be committed, pushed, attached to a PR, or stored in repository history.

## Target branch

Use:

`feature/cagliari-preview-0.1`

Do not build from `master` for the current Chapter 1 smoke test.

## Cloud workspace

GitHub Codespaces can open the repository in a browser-based VS Code environment. Create the codespace from the CFRU repository while the branch selector is on `feature/cagliari-preview-0.1`.

The DPE repository must be available beside the CFRU checkout as:

`../release-candidate-dpe`

and must use:

`feature/cagliari-preview-0.1`

The CFRU and DPE build toolchains must be installed as required by their upstream READMEs before running the private build.

## Private ROM

Place the legally obtained FireRed 1.0 ROM in the CFRU repository root **inside the private codespace only** and name it:

`BPRE0.gba`

The build verifies this SHA-1 before doing any ROM work:

`41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc`

`*.gba` is git-ignored by the project. Still verify Source Control before any commit and make sure no ROM appears as a tracked file.

## Source-only gate

Before spending time on DPE/CFRU compilation, run:

```bash
python3 scripts/preflight_chapter1.py
```

Expected first line:

`RC_CHAPTER1_PREFLIGHT=PASS`

The preflight compiles and cross-links all six Chapter 1 maps:

1. Delivery Hub
2. Marina
3. Port Link
4. Castello
5. Deploy District
6. Deploy Room

It also checks story scripts, dialogue references, symbolic map targets, event records and complete relocatable map payloads.

## Full private build

From the CFRU repository root:

```bash
python3 scripts/build_release_candidate.py --dpe-path ../release-candidate-dpe
```

The build sequence is:

`CHAPTER1_PREFLIGHT -> DPE -> CFRU -> RC_PREVIEW_PATCH -> PORT_LINK_DISCOVERY -> PORT_LINK_TRAINER_PATCH -> DELIVERY_HUB_MAP_PLAN -> RC_CUSTOM_MAPS_PATCH`

The default private output is:

`release_candidate_test.gba`

The script restores the pristine CFRU `BPRE0.gba` contents after the build and deletes disposable DPE/CFRU intermediate ROMs.

## Expected high-value statuses

For the Chapter 1 candidate, look for:

- `RC_CHAPTER1_PREFLIGHT=PASS`
- `DPE_RC_PREVIEW_SYMBOLS=OK`
- `PORT_LINK_DISCOVERY_STATUS=READY` or a documented legacy-bootstrap pending status
- `DELIVERY_HUB_MAP_PLAN_STATUS=READY`
- `RC_CUSTOM_MAPS_STATUS=APPLIED`
- `BUILD_STATUS=SUCCESS`

If `RC_CUSTOM_MAPS_STATUS` is pending, do **not** treat the Chapter 1 source implementation as runtime-verified. Keep the fallback preview and record the exact failure output.

## Smoke-test order

After a successful custom-map install, test this exact order:

1. enter Delivery Hub;
2. choose a starter;
3. KPI Rival;
4. Marina;
5. Port Link tutorial;
6. wild encounter;
7. Consulente Junior;
8. back to Marina;
9. Deploy blocked;
10. scope change;
11. Castello unlock;
12. Castello ascent;
13. Deploy District;
14. Go/No-Go trigger;
15. Deploy Room;
16. Release Manager;
17. Deploy 01 complete;
18. repeat Release Manager interaction;
19. return warp;
20. representative save/reload checks.

Do not retire the fallback bootstrap until this complete loop passes on the private ROM.
