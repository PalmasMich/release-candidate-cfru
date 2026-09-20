# Release Candidate — private build from mobile / Codespaces

This runbook is for a private, legally obtained FireRed 1.0 ROM only.

The ROM must **never** be committed, pushed, attached to a PR, or stored in repository history.

## Target branch

Use:

`feature/cagliari-preview-0.2-rebuild`

Do not build from `master` for the current Chapter 1 smoke test.

## Cloud workspace

GitHub Codespaces can open the repository in a browser-based VS Code environment. Create the codespace from the CFRU repository while the branch selector is on `feature/cagliari-preview-0.2-rebuild`.

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

The high-level build sequence is:

`CHAPTER1_PREFLIGHT -> DPE -> RC_STARTER_RUNTIME -> CFRU -> RC_PREVIEW_PATCH -> RC_OPENING_AUDIT -> PORT_LINK_DISCOVERY -> PORT_LINK_TRAINER_PATCH -> DELIVERY_HUB_MAP_PLAN -> RC_CUSTOM_MAPS_PATCH`

The default private output is:

`release_candidate_test.gba`

The script restores the pristine CFRU `BPRE0.gba` contents after the build and deletes disposable DPE/CFRU intermediate ROMs.

## Expected high-value statuses

For the Chapter 1 candidate, look for:

- `RC_CHAPTER1_PREFLIGHT=PASS`
- `RC_CONTENT_GRAPH=PASS`
- `RC_TILESET_ART_STATUS=BOOTSTRAP` until reviewed original tilesets replace the technical profiles
- `DPE_RC_PREVIEW_SYMBOLS=OK`
- `RC_STARTER_RUNTIME=PASS`
- `RC_OPENING_AUDIT=PASS` only after a uniquely validated structural rival-name bypass exists; the current source checkpoint deliberately reports `BLOCKED:STRUCTURAL_BYPASS_UNVERIFIED`
- `PORT_LINK_DISCOVERY_STATUS=READY` or a documented legacy-bootstrap pending status
- `DELIVERY_HUB_MAP_PLAN_STATUS=READY`
- `RC_CUSTOM_MAPS_STATUS=APPLIED`
- `BUILD_STATUS=SUCCESS`

The V0.2 command fails unless the map plan succeeds, all six custom maps are installed, and an output exists. It must never emit `BUILD_STATUS=SUCCESS` for a fallback map path.

## Smoke-test order

After a successful custom-map install, test this exact order:

1. start New Game with a clean save;
2. confirm Release Candidate onboarding and badge/workspace naming, with no rival-name prompt;
3. enter Delivery Hub and choose one starter;
4. confirm the party opens and save/reload works;
5. repeat steps 1–4 independently for all three starters;
6. continue with KPI Rival;
7. Marina;
8. Port Link tutorial;
9. wild encounter;
10. Consulente Junior;
11. back to Marina;
12. Deploy blocked;
13. scope change;
14. Castello unlock;
15. Castello ascent;
16. Deploy District;
17. Go/No-Go trigger;
18. Deploy Room;
19. Release Manager;
20. Deploy 01 complete;
21. repeat Release Manager interaction;
22. return warp;
23. representative save/reload checks.

Do not retire the fallback bootstrap until this complete loop passes on the private ROM.
