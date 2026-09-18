# Release Candidate — Cagliari Preview 0.1 Build Verification

This file records source/build evidence only. No ROM bytes, save files or copyrighted binary data belong here.

## Repository checkpoint

- CFRU repository: `PalmasMich/release-candidate-cfru`
- CFRU branch: `feature/cagliari-preview-0.1`
- CFRU checkpoint before this record: `6c47e34fb06426add838cde89a23664f6c78940e`
- DPE repository: `PalmasMich/release-candidate-dpe`
- DPE branch: `feature/cagliari-preview-0.1`
- DPE checkpoint: `5328e6ea1e2b16eaaa91dd49af218079b93d52bd`
- Both pull requests remain Draft.
- Base branches remain untouched.

## Stable Release Candidate species contract

| Species | ID | Preview role |
| --- | ---: | --- |
| Tartrek | `0x050E` | Grass/Ground starter |
| Frobyte | `0x050F` | Water/Electric starter |
| Emberfox | `0x0510` | Fire/Dark starter |
| Mistrillo | `0x0511` | First Cagliari wild species |

The IDs are intentionally above CFRU's existing species range to avoid the collision found during the first Tartrek device smoke test.

## Evidence recorded so far

### Gate 0 — Toolchain

**SOURCE/PIPELINE READY**

- Private build order is defined as DPE -> CFRU -> Release Candidate preview patch.
- The build scripts preserve the pristine CFRU input and remove disposable intermediate ROMs on failure.
- No ROM binary is tracked by the preview source changes.

**MANUAL CHECK STILL REQUIRED**

- Re-run the complete private build from a clean Codespaces/device workspace at the final Preview 0.1 checkpoint.

### Gate 1 — Custom creature

**PARTIALLY VERIFIED ON DEVICE**

The earlier Tartrek smoke test proved:

- custom displayed name;
- custom front sprite;
- custom back sprite;
- Grass/Ground typing;
- HP/battle rendering;
- battle entry without a rendering crash.

That test also exposed the old species-ID collision and empty moveset behavior. The source contract has since moved Tartrek to `0x050E` and registered its CFRU starting learnset.

**MANUAL RETEST REQUIRED**

Confirm on the rebuilt current preview that Tartrek starts with:

- Tackle;
- Withdraw;
- Vine Whip;

and learns Mud-Slap at level 7 without falling back to Struggle.

### Gate 2 — Cagliari playable loop

**SOURCE CONTRACT READY / MANUAL LOOP PENDING**

The current source binds the intended flow explicitly:

1. Delivery Hub opening;
2. starter assignment;
3. KPI rival introduction;
4. Port Link wild encounter table;
5. Port Link trainer contract;
6. Marina deploy teaser.

The Port Link wild table targets the preview mix already patched into former Route 1:

- Mistrillo;
- Wingull;
- Meowth.

The event manifests now validate dialogue, encounter-table, trainer and story-flag references and require the story dependencies to be produced in order.

**IMPLEMENTATION/DEVICE WORK STILL REQUIRED**

- bind the Port Link trainer battle to a safe ROM event/script insertion point;
- verify the complete route from New Game to the deploy teaser;
- verify save/reload after starter, wild battle and trainer/rival battle.

### Gate 3 — Preview candidate

**NOT YET PASSED**

Still required before Preview 0.1 can be called a candidate:

- all three starter branches smoke-tested;
- current Tartrek learnset retested after the ID fix;
- Port Link trainer battle implemented and completed;
- full 10–15 minute run completed without blocker;
- representative save/reload checks;
- Cagliari visual pass strong enough that screenshots no longer read as stock Kanto.

## Next technical checkpoint

Implement the Port Link trainer battle using an exact, verified FireRed/CFRU script signature or event insertion point. Do not patch guessed offsets. Once the binding is deterministic, add a ROM-patcher regression test before running the next private build.
