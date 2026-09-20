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
- Port Link contains the guarded **Consulente Junior** trainer bootstrap and associated corporate dialogue.
- Marina Porto currently closes the playable route with the **DEPLOY BLOCKED - CHECK SCOPE** teaser.
- The private-ROM pipeline applies DPE, CFRU, identity/text, encounter, trainer and custom-map stages in order and runs a final preview identity gate.

## Source-of-truth manifests

- `dialogue.yml`: Chapter 1 dialogue beats and corporate flavor.
- `encounters.yml`: Port Link wild encounter contract.
- `trainers.yml`: KPI rival, Port Link trainer and later Release Manager intent.
- map/event manifests in this directory: Cagliari/Delivery Hub/Port Link layout and progression contract.

The manifests describe intent; the build scripts under `scripts/` are responsible for safely discovering and applying equivalent changes to the private FireRed/CFRU build. Late ROM patches are fail-closed: ambiguous signatures or incomplete required stages must not be reported as a successful playable preview.

## Governance

- Do not commit or distribute a full ROM binary.
- Keep development on `feature/cagliari-preview-0.1` and the PR in Draft until explicit approval.
- Do not merge or modify `master`/`main` as part of preview iteration.
- Private-ROM smoke testing is intentionally deferred until the automated preview contract is thick enough to justify another device pass.

## Next technical gate

Before requesting another manual smoke test, keep the build deterministic and preserve the visible Chapter 1 contract through the final validator. The remaining private-ROM-only validation is to prove the complete sequence on-device: opening -> Delivery Hub -> starter selection -> KPI rival -> Port Link -> Mistrillo encounter -> Consulente Junior -> Marina Porto teaser.
