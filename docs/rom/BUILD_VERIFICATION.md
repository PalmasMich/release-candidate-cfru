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


## Port Link trainer bootstrap implementation

Source implementation now includes a guarded bootstrap path for the Port Link trainer battle.

Current bootstrap contract:

- discovery starts from the already-patched Port Link delivery NPC text;
- the reference must classify as a FireRed event script, not merely as a raw ROM pointer;
- classification now matches the actual FireRed Route 1 Mart Clerk structure:
  - `lock`;
  - `faceplayer`;
  - `checkflag` / conditional `goto`;
  - `loadword 0, <text>`;
  - `callstd`;
- a verification signature is captured before any write;
- the trainer patch aborts if the signature, intro text or defeat text is ambiguous;
- the bootstrap script uses `TRAINER_RS_YOUNGSTER = 37`, a preserved RS dummy trainer with a single level-5 party member;
- the bootstrap defeat text reuses the already-patched Port Link text `Please, report at MARINA PORTO.`;
- trainer patching occurs on a temporary output file and replaces the preview ROM only after successful completion;
- a failed/ambiguous trainer patch leaves the normal preview ROM intact and reports a pending status.

The target manifest remains `RC_TRAINER_PORT_01` with one level-4 Meowth. The bootstrap trainer's dummy party is intentionally **not** binary-patched yet because the dummy party payload is repeated for many preserved RS trainer classes and therefore is not a unique safe signature.

### Next verification

On the next private build, expect the pipeline:

`DPE -> CFRU -> RC_PREVIEW_PATCH -> PORT_LINK_DISCOVERY -> PORT_LINK_TRAINER_PATCH`

A successful bootstrap should emit:

- `PORT_LINK_DISCOVERY_STATUS=READY`;
- `PORT_LINK_TRAINER_STATUS=APPLIED`;
- the exact Port Link script, intro-text and defeat-text ROM offsets.

Only after that device smoke test should the bootstrap party/name be promoted to the final Consulente Junior implementation.


## Custom-map pipeline checkpoint

The Chapter 1 implementation now has a guarded binary path for two permanent custom-map slots:

- `RC_DELIVERY_HUB` -> reserved unused `MAP_ROUTE19_UNUSED_HOUSE` (group 27 / map 0);
- `RC_CAGLIARI_MARINA` -> reserved prototype `MAP_PROTOTYPE_SEVII_ISLE_8` (group 3 / map 52).

Source-controlled map compilers now cover:

- semantic map layouts and collision/elevation cells;
- bootstrap metatile profiles with explicit retirement conditions;
- FireRed `MapLayout`, `MapEvents`, `ObjectEventTemplate`, `BgEvent` and `WarpEvent` structures;
- relocatable event scripts and Italian dialogue blobs;
- Chapter 1 flags in the upstream-unused 0x0AF..0x0B9 range;
- cross-map warp linking Hub <-> Marina;
- guarded trailing-ROM free-space allocation;
- atomic map installation: payloads first, map-header repoints second, Pallet/Oak-Lab entry warp repoint last.

The private build pipeline now includes `RC_CUSTOM_MAPS_PATCH`. It writes through a temporary ROM and only replaces the prior preview artifact after the complete custom-map installer succeeds.

### Next private-ROM verification gate

A real DPE -> CFRU private build must still confirm:

1. unique discovery of both reserved map headers in the current expanded ROM;
2. sufficient terminal 0xFF free space for both linked payloads plus guard bytes;
3. exactly two guarded Pallet -> Oak Lab coordinate-warp signatures;
4. successful launch into the new 18x12 Delivery Hub;
5. starter interaction and KPI-rival dialogue inside the new map;
6. Hub -> Marina (24x16) and Marina -> Hub warp round trip;
7. save/reload on the custom-map path.

Until that smoke test passes, Route 1 and the current preview remain the fallback bootstrap and no bootstrap map is retired.


## Custom Port Link checkpoint

The permanent Cagliari path now extends beyond the Delivery Hub and Marina into a third custom map:

- `RC_PORT_CONNECTION` -> reserved prototype `MAP_PROTOTYPE_SEVII_ISLE_9` (group 3 / map 53);
- custom layout: 28x12;
- semantic grass uses the verified FireRed General tileset grass metatile;
- Marina -> Port Link and Port Link -> Marina warps resolve through reserved RC map slots;
- a real FireRed `CoordEvent` on `VAR_TEMP_1 == 0` drives the one-shot wild tutorial;
- the tutorial sets `RC_FLAG_WILD_TUTORIAL_DONE`;
- the Consulente Junior lives as an ObjectEventTemplate on the custom Port Link;
- its script uses FireRed `trainerbattle_single` bytecode with trainer 37 as the current bootstrap trainer;
- after battle, the script sets `RC_FLAG_PORT_TRAINER_DONE`;
- the patched Route 1 WildPokemonHeader is deterministically moved from map 3/19 to Port Link map 3/53, preserving the already-patched Mistrillo/Wingull/Meowth encounter table;
- Route 1 remains a fallback only when the custom-map installer does not apply.

The atomic installer now treats Delivery Hub, Marina and Port Link as one unit. It writes all three payloads first, repoints all three headers second, moves the wild encounter header third, and redirects the Pallet/Oak-Lab story entry into the Delivery Hub last.

### Next private-ROM smoke path

Expected playable sequence after a successful custom-map install:

1. Pallet bootstrap transition -> `RC_DELIVERY_HUB`;
2. choose Tartrek / Frobyte / Emberfox;
3. KPI Rival dialogue;
4. Delivery Hub -> `RC_CAGLIARI_MARINA`;
5. Marina Delivery Lead sends the player toward Port Link;
6. Marina -> `RC_PORT_CONNECTION`;
7. automatic wild tutorial trigger;
8. Mistrillo / Wingull / Meowth encounters in custom Port Link grass;
9. Consulente Junior trainer battle;
10. return to Marina;
11. Deploy-blocked dialogue;
12. scope-change dialogue sets `RC_FLAG_SCOPE_CHANGE_REVEALED` and `RC_FLAG_CASTELLO_UNLOCKED`.

Until this full loop is smoke-tested on the private built ROM, all three custom map statuses remain pending verification and the legacy preview/bootstrap path remains available.


## Castello and Deploy District checkpoint

The custom Chapter 1 path now extends beyond Marina and Port Link:

- `RC_CASTELLO_ASCENT` -> reserved prototype `MAP_PROTOTYPE_SEVII_ISLE_6` (group 3 / map 50);
- `RC_DEPLOY_DISTRICT` -> reserved prototype `MAP_PROTOTYPE_SEVII_ISLE_7` (group 3 / map 51);
- both prototype source headers are discovered structurally as 1x1 route maps with live vanilla connections;
- the atomic installer explicitly clears their old `connections_ptr` values when repointing them;
- Castello uses a permanent 20x18 custom layout;
- Deploy District uses a permanent 22x16 custom layout;
- Marina exposes Castello through `RC_SCRIPT_CASTELLO_GATE`, which checks `RC_FLAG_CASTELLO_UNLOCKED` and only then executes a FireRed `warp` to map 3/50;
- Castello summit exposes Deploy District through `RC_SCRIPT_DEPLOY_DISTRICT_GATE`, linked to map 3/51;
- entering Deploy District triggers a real CoordEvent that sets `RC_FLAG_GO_NO_GO_STARTED` (0x0B7) and shows the Go/No-Go opening dialogue;
- Deploy District retains a linked return warp to Castello map 3/50.

The atomic custom-map installer now treats five maps as one install unit:
`Delivery Hub -> Marina -> Port Link -> Castello -> Deploy District`.

### Extended private-ROM smoke path

After the existing Hub/Marina/Port Link checks, verify:

13. scope change unlocks the Castello interaction;
14. the locked Castello gate refuses access before flag 0x0B6;
15. after unlock, Marina -> Castello lands at the intended 20x18 spawn;
16. Castello return warp reaches Marina correctly;
17. summit gate reaches Deploy District map 3/51;
18. Deploy District arrival fires the one-shot Go/No-Go trigger;
19. `RC_FLAG_GO_NO_GO_STARTED` is set;
20. Deploy District return warp reaches Castello;
21. save/reload remains stable on Castello and Deploy District.

These additions remain pending device verification until a private DPE -> CFRU build passes the full loop.
