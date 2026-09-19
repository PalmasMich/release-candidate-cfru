# Cagliari Preview 0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 10–15 minute playable FireRed/CFRU preview set in a compressed real-world Cagliari, with three original starters, at least one original wild creature, a KPI-obsessed rival encounter, and a closing Deploy teaser.

**Architecture:** `release-candidate-dpe` owns original species data and battle art; `release-candidate-cfru` owns engine/runtime integration and the reproducible project contract; the legally obtained FireRed 1.0 ROM (`BPRE0.gba`) remains a local-only build input used by DPE/CFRU and binary map/event tooling. Git stores only source, original assets, manifests, scripts, checksums and patchable metadata—never ROM binaries.

**Tech Stack:** Pokémon FireRed 1.0, Complete FireRed Upgrade (CFRU), Dynamic Pokémon Expansion (DPE), devkitARM/devkitPro, Python 3, XSE-compatible event scripting, Advance Map-compatible ROM mapping, original indexed PNG sprite/tileset assets.

**Spec:** `docs/superpowers/specs/2026-09-17-cagliari-preview-0.1-design.md`

## Global Constraints

- Development branches: `feature/cagliari-preview-0.1` in both CFRU and DPE repositories.
- `master` must remain untouched until an explicit review/merge decision.
- Never commit `BPRE0.gba`, `test.gba`, `.sav`, commercial ROM dumps or other copyrighted ROM binaries.
- DPE must be applied before CFRU, matching upstream guidance.
- The preview is non-commercial and patch-oriented.
- Original creature IDs must be stable and documented identically across both repositories.
- Preview scope is Cagliari only: Delivery Hub, Marina/Porto, short connection route, starter choice, original wild encounter, rival/trainer encounter and Deploy teaser.
- Release Manager boss, full Deploy Clearance, Milano/India/Japan/Cupertino and the full 15+ creature Cagliari roster are out of scope.
- No Pokémon Unbound assets, maps, music or project-specific code may be copied; Unbound is only a quality benchmark.

---

### Task 1: Lock the reproducible two-repository build contract

**Files:**
- Create: `docs/rom/BUILD_CONTRACT.md` in CFRU
- Create: `scripts/validate_release_candidate_workspace.py` in CFRU
- Create: `tests/test_release_candidate_workspace.py` in CFRU
- Create: `docs/release_candidate_species_contract.md` in DPE

**Interfaces:**
- Consumes: upstream CFRU `scripts/make.py`, upstream DPE `scripts/make.py`, local `BPRE0.gba`.
- Produces: a machine-readable validation convention and a documented insertion order `DPE -> CFRU`.

- [ ] **Step 1: Write the failing workspace tests**

Create `tests/test_release_candidate_workspace.py` with assertions that:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rom_binary_is_git_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "*.gba" in ignore


def test_build_contract_exists():
    text = (ROOT / "docs/rom/BUILD_CONTRACT.md").read_text(encoding="utf-8")
    assert "DPE -> CFRU" in text
    assert "BPRE0.gba" in text
    assert "must never be committed" in text


def test_workspace_validator_exists():
    validator = ROOT / "scripts/validate_release_candidate_workspace.py"
    assert validator.exists()
```

- [ ] **Step 2: Run the tests and verify the expected RED state**

Run:

```bash
python -m unittest discover -s tests -p 'test_release_candidate_workspace.py'
```

Expected: FAIL because the build contract and validator do not yet exist.

- [ ] **Step 3: Implement the validator**

Create `scripts/validate_release_candidate_workspace.py` that:
- verifies Python >= 3.8;
- reports whether `BPRE0.gba` exists without copying or reading its contents;
- verifies CFRU `scripts/make.py` exists;
- accepts `--dpe-path <path>` and verifies DPE `scripts/make.py` exists;
- prints the insertion order `DPE -> CFRU`;
- exits non-zero only when a required source/tool path is absent; absence of the ROM is reported as `BLOCKED_LOCAL_ROM` rather than treated as a repository defect.

The public CLI contract is:

```bash
python scripts/validate_release_candidate_workspace.py --dpe-path ../release-candidate-dpe
```

- [ ] **Step 4: Write the build contract documentation**

`docs/rom/BUILD_CONTRACT.md` must define:
1. obtain a legal FireRed 1.0 ROM locally and name it `BPRE0.gba`;
2. keep a pristine backup outside the repos;
3. copy the local ROM into the DPE workspace;
4. run DPE `python scripts/make.py`;
5. use the resulting expanded ROM as the local input to CFRU;
6. run CFRU `python scripts/make.py`;
7. apply map/event edits only to a disposable working copy;
8. distribute only a legal patch artifact when/if distribution is approved.

- [ ] **Step 5: Add the DPE species contract document**

Create `docs/release_candidate_species_contract.md` in DPE defining the initial stable symbolic IDs:

```text
SPECIES_RC_TURTLE_01
SPECIES_RC_FROG_01
SPECIES_RC_FIREFOX_01
SPECIES_RC_CAGLIARI_WILD_01
SPECIES_RC_CAGLIARI_WILD_02
```

The document must state that the rival uses one of the two unchosen starters in Preview 0.1 and does not require a sixth species.

- [ ] **Step 6: Run tests GREEN**

Run the same unittest command and expect PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/rom/BUILD_CONTRACT.md scripts/validate_release_candidate_workspace.py tests/test_release_candidate_workspace.py
git commit -m "chore: define reproducible ROM build contract"
```

DPE:

```bash
git add docs/release_candidate_species_contract.md
git commit -m "docs: define Release Candidate species contract"
```

---

### Task 2: Reserve stable Release Candidate species IDs in DPE

**Files:**
- Modify: `include/species.h` in DPE
- Modify: `include/pokedex.h` in DPE if new Pokédex entries are required by the chosen DPE convention
- Create: `tests/test_rc_species_contract.py` in DPE

**Interfaces:**
- Consumes: symbolic IDs from `docs/release_candidate_species_contract.md`.
- Produces: stable compile-time constants for the five Preview species.

- [ ] **Step 1: Write the failing contract test**

Create `tests/test_rc_species_contract.py`:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECIES = (ROOT / "include/species.h").read_text(encoding="utf-8")

REQUIRED = [
    "SPECIES_RC_TURTLE_01",
    "SPECIES_RC_FROG_01",
    "SPECIES_RC_FIREFOX_01",
    "SPECIES_RC_CAGLIARI_WILD_01",
    "SPECIES_RC_CAGLIARI_WILD_02",
]


def test_rc_species_are_reserved():
    for name in REQUIRED:
        assert name in SPECIES
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest discover -s tests -p 'test_rc_species_contract.py'
```

Expected: FAIL because no RC species constants exist yet.

- [ ] **Step 3: Reserve contiguous IDs after the current final species constant**

Inspect the tail of `include/species.h` at implementation time and append the five IDs contiguously without renumbering any existing species. Preserve all upstream constants and form ranges.

- [ ] **Step 4: Run GREEN**

Run the same test and expect PASS.

- [ ] **Step 5: Compile source-only DPE objects if toolchain is available**

Run:

```bash
python scripts/build.py
```

Expected: compile success without requiring a ROM insertion. If devkitARM is not available in the current executor, record `BLOCKED_TOOLCHAIN_DEVKITARM` in `docs/release_candidate_species_contract.md`; do not fake a successful compile.

- [ ] **Step 6: Commit**

```bash
git add include/species.h include/pokedex.h tests/test_rc_species_contract.py docs/release_candidate_species_contract.md
git commit -m "feat: reserve Release Candidate species ids"
```

---

### Task 3: Integrate the first original starter data path

**Files:**
- Modify: DPE `src/Base_Stats.c`
- Modify: DPE species name/text table identified from the repository at execution time
- Modify: DPE level-up learnset table identified from the repository at execution time
- Modify: DPE `src/Front_Pic_Table.c`
- Modify: DPE `src/Back_Pic_Table.c`
- Modify: DPE `src/Icon_Table.c`
- Modify: DPE coordinate/palette tables required by the existing sprite pipeline
- Add: original turtle starter front/back/icon graphics under existing DPE `graphics/frontspr`, `graphics/backspr`, `graphics/pokeicon` conventions
- Create: `tests/test_rc_turtle_data.py`

**Interfaces:**
- Consumes: `SPECIES_RC_TURTLE_01`.
- Produces: one battle-safe starter species that can be created in party once the ROM is locally built.

- [ ] **Step 1: Write a structural RED test**

The test must verify that `SPECIES_RC_TURTLE_01` appears in base stats, name/text data, a learnset, front sprite table, back sprite table and icon table.

- [ ] **Step 2: Run RED**

Expected: missing table entries.

- [ ] **Step 3: Add minimal balanced starter data**

Use this Preview baseline unless compile constraints require field-name adaptation:

```text
Typing: Grass/Ground
HP 48 / Atk 55 / Def 60 / SpA 42 / SpD 55 / Spe 40
Catch rate: 45
Growth: medium-slow or the nearest existing starter convention
Starting learnset: one neutral damaging move + one low-power thematic Grass/Ground move available by level 5
```

Do not add evolutions yet.

- [ ] **Step 4: Add original turtle graphics**

Create original 64×64-compatible battle sprite art and icon art in the repository's expected indexed format. Do not copy Pokémon or Unbound artwork.

- [ ] **Step 5: Run structural tests GREEN and source compile**

Run the Python contract test, then `python scripts/build.py` when devkitARM is available.

- [ ] **Step 6: Commit**

```bash
git add include src graphics tests
git commit -m "feat: add first Release Candidate starter"
```

---

### Task 4: Complete the Preview creature set

**Files:**
- Modify the same DPE species data/graphics tables as Task 3
- Add frog, fire-fox and Cagliari wild creature graphics
- Create: `tests/test_rc_preview_roster.py`

**Interfaces:**
- Consumes: all five RC species constants.
- Produces: the Preview roster contract used by starter choice, wild encounter and rival battle.

- [ ] **Step 1: Write RED roster test**

Test each mandatory Preview species for base stats, displayed name, minimal learnset, front sprite, back sprite and icon registration.

- [ ] **Step 2: Implement frog starter**

Preview baseline:

```text
Primary identity: Water
Stat bias: special attack / speed
Starter-equivalent catch/growth conventions
```

- [ ] **Step 3: Implement fire-fox starter**

Preview baseline:

```text
Primary identity: Fire
Stat bias: attack / speed
Starter-equivalent catch/growth conventions
```

- [ ] **Step 4: Implement Cagliari wild creature 1**

Give it a Mediterranean/urban-coastal identity and early-route power level. It must be safe to encounter around player level 3–5.

- [ ] **Step 5: Implement Cagliari wild creature 2 only if art/data are ready without delaying Gate 1**

If not, keep the already-reserved species ID unused in encounter tables; Preview 0.1 still satisfies the design with four playable original species.

- [ ] **Step 6: Run tests and source compile**

Expected: structural test PASS; DPE source build PASS where devkitARM is available.

- [ ] **Step 7: Commit**

```bash
git add include src graphics tests
git commit -m "feat: complete Cagliari preview creature roster"
```

---

### Task 5: Define ROM-editable Cagliari content as source-controlled manifests

**Files:**
- Create: CFRU `content/cagliari_preview/maps.yml`
- Create: CFRU `content/cagliari_preview/events.yml`
- Create: CFRU `content/cagliari_preview/dialogue.yml`
- Create: CFRU `content/cagliari_preview/encounters.yml`
- Create: CFRU `content/cagliari_preview/trainers.yml`
- Create: CFRU `scripts/validate_cagliari_content.py`
- Create: CFRU `tests/test_cagliari_content.py`

**Interfaces:**
- Consumes: DPE symbolic species IDs by name.
- Produces: a source-of-truth manifest used when editing the local ROM through map/event tools.

- [ ] **Step 1: Write RED manifest validation tests**

Required map IDs/names:

```text
RC_DELIVERY_HUB
RC_CAGLIARI_MARINA
RC_PORT_CONNECTION
```

Required story flags:

```text
RC_FLAG_STARTER_CHOSEN
RC_FLAG_RIVAL_INTRO_DONE
RC_FLAG_WILD_TUTORIAL_DONE
RC_FLAG_RIVAL_BATTLE_DONE
RC_FLAG_DEPLOY_TEASER_SEEN
```

- [ ] **Step 2: Implement YAML-like manifests using a dependency-free subset**

Use simple key/value and list syntax that `scripts/validate_cagliari_content.py` can parse without installing PyYAML. The validator must check uniqueness and required references.

- [ ] **Step 3: Write the approved opening dialogue**

Include the exact opening beat:

```text
Benvenuto a Cagliari. Il progetto era già iniziato quando sei arrivato.
```

The Delivery Hub starter scene must frame the creatures as the “risorse attualmente disponibili”, without presenting any choice as objectively superior.

- [ ] **Step 4: Define rival content**

The rival must reference KPI/story points/velocity in a way understandable without Agile knowledge and use the starter with matchup logic determined after player choice.

- [ ] **Step 5: Define encounter content**

The Marina/connection route must include `SPECIES_RC_CAGLIARI_WILD_01` at early-game levels and may mix official species temporarily.

- [ ] **Step 6: Run validator GREEN**

```bash
python scripts/validate_cagliari_content.py
python -m unittest discover -s tests -p 'test_cagliari_content.py'
```

- [ ] **Step 7: Commit**

```bash
git add content/cagliari_preview scripts/validate_cagliari_content.py tests/test_cagliari_content.py
git commit -m "feat: define Cagliari preview content manifests"
```

---

### Task 6: Author the Cagliari visual kit for ROM insertion

**Files:**
- Create: `assets/cagliari_preview/tiles/` original tilesheet sources
- Create: `assets/cagliari_preview/palettes/` palette references
- Create: `assets/cagliari_preview/overworld/` protagonist/rival/NPC sprite sources
- Create: `docs/rom/CAGLIARI_MAPPING_GUIDE.md`
- Create: `tests/test_cagliari_asset_manifest.py`

**Interfaces:**
- Consumes: map roles from Task 5.
- Produces: original art sources suitable for conversion/import into the FireRed working ROM.

- [ ] **Step 1: Add asset manifest RED test**

Require at least: limestone wall, Mediterranean pavement, sea/port edge, palm/greenery, Delivery Hub signage/interior accents, protagonist overworld source, rival overworld source.

- [ ] **Step 2: Create a coherent limited-palette visual kit**

Target Gen-3 hardware constraints while aiming for a richer Gen-4-inspired composition. Assets must be original and must not reproduce an existing Pokémon/Unbound map or tileset.

- [ ] **Step 3: Document map composition**

`CAGLIARI_MAPPING_GUIDE.md` must define a compressed layout:
- Delivery Hub interior -> Marina/Porto exterior;
- Marina as the main recognizable space;
- one short connection route for encounters/trainer;
- visual cues: warm limestone, water/port, palms/urban greenery, skyline/elevation suggestion.

- [ ] **Step 4: Run asset manifest test GREEN**

- [ ] **Step 5: Commit**

```bash
git add assets/cagliari_preview docs/rom/CAGLIARI_MAPPING_GUIDE.md tests/test_cagliari_asset_manifest.py
git commit -m "art: add Cagliari preview ROM asset kit"
```

---

### Task 7: Apply DPE + CFRU and build the local playable ROM

**Files:**
- Local-only: `BPRE0.gba`, generated `test.gba`, saves and emulator state
- Update: `docs/rom/BUILD_VERIFICATION.md` with non-copyrighted metadata only

**Interfaces:**
- Consumes: Tasks 1–6 plus a legally obtained local FireRed 1.0 ROM.
- Produces: a local playable build and verification record; no ROM binary enters Git.

- [ ] **Step 1: Validate local workspace**

```bash
python scripts/validate_release_candidate_workspace.py --dpe-path ../release-candidate-dpe
```

Expected: no missing source/tool path and ROM reported present.

- [ ] **Step 2: Apply DPE first**

In DPE workspace:

```bash
python scripts/make.py
```

Expected: generated local `test.gba` and offsets metadata.

- [ ] **Step 3: Apply CFRU to the DPE-expanded working ROM**

Copy/rename only inside the private local workspace so CFRU receives the expanded ROM as `BPRE0.gba`, then run:

```bash
python scripts/make.py
```

Expected: CFRU-enhanced local ROM builds successfully.

- [ ] **Step 4: Smoke-test first custom starter before map work**

Using a controlled party-injection/test event, verify name, icon, battle front/back sprite, stats, moves, battle completion and save/reload.

- [ ] **Step 5: Record Gate 1 evidence**

`BUILD_VERIFICATION.md` records tool versions, commit SHAs, symbolic species tested and PASS/FAIL results. It must not contain ROM bytes.

- [ ] **Step 6: Commit verification metadata only**

```bash
git add docs/rom/BUILD_VERIFICATION.md
git commit -m "test: verify first custom species in ROM"
```

---

### Task 8: Build the playable 10–15 minute Cagliari loop

**Files:**
- Local ROM maps/events/scripts derived from Task 5 manifests
- Update: `content/cagliari_preview/*.yml` if implementation-specific IDs are assigned
- Update: `docs/rom/BUILD_VERIFICATION.md`

**Interfaces:**
- Consumes: Cagliari maps/events manifests, visual kit and DPE roster.
- Produces: Preview 0.1 candidate.

- [ ] **Step 1: Build Delivery Hub**

Implement opening, onboarding and three-way starter selection. Set `RC_FLAG_STARTER_CHOSEN` and add the selected custom species to party.

- [ ] **Step 2: Implement rival introduction and matchup selection**

The rival chooses one of the two unchosen starters according to a deterministic matchup table documented in `trainers.yml`.

- [ ] **Step 3: Build Marina/Porto and connection route**

Use the original Cagliari visual kit and keep traversal compact enough that a blind player reaches the wild encounter within a few minutes.

- [ ] **Step 4: Add original wild encounter**

Encounter `SPECIES_RC_CAGLIARI_WILD_01`, finish battle cleanly and set `RC_FLAG_WILD_TUTORIAL_DONE` through the surrounding event flow where appropriate.

- [ ] **Step 5: Add short rival/trainer battle**

Complete battle, set `RC_FLAG_RIVAL_BATTLE_DONE`, retain playable/saveable state afterward.

- [ ] **Step 6: Add Deploy teaser**

End the preview with the revelation that the first Deploy is blocked and set `RC_FLAG_DEPLOY_TEASER_SEEN`. Do not implement the Release Manager boss.

- [ ] **Step 7: Full manual acceptance pass**

From new game to teaser verify:
- target duration 10–15 minutes;
- all three starter branches work;
- custom wild encounter works;
- rival matchup works for each starter;
- save/reload works after starter, after wild battle and after rival battle;
- no crash/blocker;
- screenshots read as Cagliari/Release Candidate rather than stock Kanto.

- [ ] **Step 8: Commit final source-controlled manifests/evidence**

```bash
git add content/cagliari_preview docs/rom/BUILD_VERIFICATION.md
git commit -m "feat: complete Cagliari Preview 0.1 playable loop"
```

---

### Task 9: Package a reviewable Preview candidate without distributing a ROM

**Files:**
- Create: `docs/rom/PREVIEW_0.1_ACCEPTANCE.md`
- Create: `release/preview-0.1-manifest.json`
- Optional local-only patch output generated from the user's lawful base ROM

**Interfaces:**
- Consumes: verified playable ROM from Task 8.
- Produces: reproducible review metadata and, only when legally appropriate, a patch rather than a ROM.

- [ ] **Step 1: Write acceptance record**

Record each Gate 0–3 criterion as PASS/FAIL with the exact CFRU and DPE commit SHAs.

- [ ] **Step 2: Create release manifest**

`preview-0.1-manifest.json` contains version, required base-ROM identity description, repository SHAs, expected playtime and content scope. Do not include copyrighted ROM data.

- [ ] **Step 3: Verify repository hygiene**

Run:

```bash
git status --ignored
git ls-files '*.gba' '*.sav' '*.sgm'
```

Expected: no tracked ROM/save files.

- [ ] **Step 4: Commit**

```bash
git add docs/rom/PREVIEW_0.1_ACCEPTANCE.md release/preview-0.1-manifest.json
git commit -m "docs: package Cagliari Preview 0.1 candidate"
```

## Self-review result

- Spec coverage: all approved Preview 0.1 story beats, Cagliari areas, 4–6 creature scope, starter choice, wild/rival battles, art strategy, build governance and Gates 0–3 map to Tasks 1–9.
- No-ROM rule: enforced in Task 1 and re-verified in Tasks 7 and 9.
- Architecture risk addressed: CFRU/DPE are binary-insertion projects rather than a full FireRed decomp; source-controlled manifests preserve intent while map/event application remains in the private working ROM.
- Earliest meaningful visual/playable checkpoint: Task 7 proves one original creature in battle; Task 8 provides the 10–15 minute Cagliari preview.
