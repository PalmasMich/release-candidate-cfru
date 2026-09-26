# Cagliari Preview 0.1

This directory is the source-controlled design contract for the first playable vertical slice of **Release Candidate**.

## Current implementation status

The preview is now a deliberately thicker Chapter 1 slice rather than a thin reskin:

- Release Candidate onboarding replaces the visible vanilla opening identity.
- Cagliari is the starting location and the former lab is presented as the **Delivery Hub**.
- The three original starter slots are wired to **Tartrek**, **Frobyte** and **Emberfox**.
- All three starters have dedicated DPE front/back/icon assets and CFRU-compatible starting learnsets.
- The opening rival is the **Rivale KPI**, with a complete three-starter counter matrix and corporate/KPI dialogue.
- The first outside route is **Port Link**, leading toward **Marina Porto**.
- Port Link has the first RC custom wild encounter, **Mistrillo**, in a 60/25/15 Mistrillo/Wingull/Meowth encounter mix.
- Marina Porto closes Preview 0.1 with the **DEPLOY BLOCKED - CHECK SCOPE** / deploy-gate teaser.
- The private-ROM pipeline applies DPE, CFRU, identity/text and encounter stages in order and runs a final preview identity gate.

A Port Link trainer and later Chapter 1 events remain in the manifests as post-preview work. They are deliberately not claimed as part of the Preview 0.1 playable acceptance path until their event relocation is implemented safely.

## Source-of-truth manifests

- `dialogue.yml`: Chapter 1 dialogue beats and corporate flavor.
- `encounters.yml`: Port Link wild encounter contract.
- `trainers.yml`: KPI rival plus later trainer intent.
- `events.yml`: progression contract and explicit implemented/reserved boundaries.
- `acceptance.json`: machine-readable acceptance/handoff contract.
- `manual_smoke_checklist.md`: focused private-ROM device validation after a successful build.
- map/event manifests in this directory: Cagliari/Delivery Hub/Port Link layout and progression contract.

The manifests describe intent; the build scripts under `scripts/` are responsible for safely discovering and applying equivalent changes to the private FireRed/CFRU build. Late ROM patches are fail-closed: ambiguous signatures or incomplete required stages must not be reported as a successful playable preview.

## Governance

- Do not commit or distribute a full ROM binary.
- Keep development on `feature/cagliari-preview-0.1` and the PR in Draft until explicit approval.
- Do not merge or modify `master`/`main` as part of preview iteration.
- The ROM input and generated ROM remain private/local.

## Next technical gate

The source-controlled automated contract is thick enough for the next gate. A **fresh private-ROM build** must now succeed from a legally obtained FireRed 1.0 input; that step cannot be performed from the repository alone because the ROM is intentionally not committed. After that successful build, run `manual_smoke_checklist.md` on-device and validate the canonical sequence:

**opening -> Delivery Hub -> Tartrek -> KPI rival -> Port Link -> Mistrillo -> Marina Porto teaser**.
