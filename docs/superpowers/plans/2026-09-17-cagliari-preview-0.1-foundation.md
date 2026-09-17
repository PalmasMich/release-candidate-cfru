# Cagliari Preview 0.1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a reproducible FireRed + DPE + CFRU development pipeline and prove one original Release Candidate starter can be inserted, rendered, battled with, saved, and reloaded before investing in Cagliari mapping.

**Architecture:** The preview uses three layers: DPE owns original species data and battle graphics; CFRU owns the upgraded engine/runtime and scripting hooks; a private local FireRed 1.0 workspace owns ROM-only map/event edits. GitHub stores source, original assets, manifests, tests and documentation, but never `BPRE0.gba` or generated ROM binaries. DPE is applied before CFRU, matching the upstream DPE integration guidance.

**Tech Stack:** Pokémon FireRed 1.0, Dynamic Pokémon Expansion, Complete Fire Red Upgrade, devkitARM/devkitPro, Python 3, GNU assembler/linker toolchain used by the upstream projects, Python `unittest`, XSE-compatible event scripting for later map work.

**Spec:** `docs/superpowers/specs/2026-09-17-cagliari-preview-0.1-design.md`

## Global Constraints

- Work only on `feature/cagliari-preview-0.1` or branches derived from it; do not modify `master` during implementation.
- Never commit `BPRE0.gba`, `test.gba`, generated commercial-ROM dumps, save files, or other copyrighted ROM binaries.
- The user supplies a legally obtained FireRed 1.0 ROM locally as `BPRE0.gba`.
- The project remains non-commercial; CFRU's upstream terms prohibit monetization and donations without explicit permission.
- Use DPE for original species/data/sprites/icons/cries and CFRU for engine/runtime integration.
- Apply DPE before CFRU to the integration ROM.
- Do not copy maps, code, graphics, music, dialogue or other content from Pokémon Unbound; it is a quality benchmark only.
- Gate 0 must pass before any Cagliari map work. Gate 1 must pass before integrating the remaining Preview 0.1 creatures.

---

## File Structure

### CFRU repository — `PalmasMich/release-candidate-cfru`

- Create `tools/release_candidate/validate_workspace.py` — zero-dependency preflight for legal/reproducible workspace state.
- Create `tests/release_candidate/test_workspace_contract.py` — tests ROM exclusions and expected upstream insertion offsets/order metadata.
- Create `release_candidate/pipeline.json` — machine-readable DPE→CFRU integration contract and branch names.
- Create `docs/release-candidate/BUILD.md` — exact private-ROM build procedure and validation commands.
- Modify `.gitignore` — explicitly ignore ROM/save/patch-work files produced locally.
- Do not change `scripts/make.py` in Gate 0; retain upstream CFRU insertion offset `0x900000` until the combined build proves it is safe.

### DPE repository — `PalmasMich/release-candidate-dpe`

- Create `release_candidate/creatures.json` — stable Release Candidate species registry shared conceptually with CFRU scripts/docs.
- Create `tests/release_candidate/test_creature_contract.py` — source-level contract tests for the first custom species.
- Modify `include/species.h` — add stable identifier `SPECIES_RC_TURTLE_01` without renumbering existing species.
- Modify `src/Base_Stats.c` — add first starter's battle data.
- Modify `src/Front_Pic_Table.c` and `src/Back_Pic_Table.c` — point the species at its original battle graphics.
- Modify `src/Front_Pic_Coords_Table.c` and `src/Back_Pic_Coords_Table.c` — define display coordinates.
- Modify `src/Icon_Table.c` and `src/Icon_Palette_Table.c` — register party icon and palette.
- Modify `include/sprite_data.h` and `include/graphics.h` only as required by the existing DPE graphics pattern after the first RED contract test identifies the exact adjacent declarations.
- Create original graphics under `graphics/frontspr/`, `graphics/backspr/`, and `graphics/pokeicon/` using the exact format already consumed by DPE's grit build rules.
- Keep upstream DPE insertion offset `0x1800000` for the first combined-build proof.

The first species uses the stable internal ID `SPECIES_RC_TURTLE_01`. Its Preview 0.1 working display identity is **Viandante**, Grass/Ground, with a deliberately modest starter-stage BST of 310: HP 55 / Atk 56 / Def 60 / SpA 38 / SpD 51 / Spe 50. The internal identifier is permanent even if the display name is later refined.

---

### Task 1: Lock Repository Hygiene and Pipeline Contract

**Files:**
- Create: `release_candidate/pipeline.json`
- Create: `tools/release_candidate/validate_workspace.py`
- Create: `tests/release_candidate/test_workspace_contract.py`
- Create: `docs/release-candidate/BUILD.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: upstream CFRU `scripts/make.py` using `BPRE0.gba` and offset `0x900000`; upstream DPE `scripts/make.py` using `BPRE0.gba` and offset `0x1800000`.
- Produces: `validate_workspace.py` command returning exit code 0 only when repo hygiene and expected pipeline metadata are valid; `pipeline.json` consumed by later integration checks.

- [ ] **Step 1: Write the failing workspace-contract test**

Create `tests/release_candidate/test_workspace_contract.py` using only stdlib `unittest`. It must assert that `release_candidate/pipeline.json` exists and contains exactly these keys/values:

```json
{
  "base_rom_filename": "BPRE0.gba",
  "dpe_repo": "PalmasMich/release-candidate-dpe",
  "dpe_branch": "feature/cagliari-preview-0.1",
  "dpe_offset": "0x1800000",
  "cfru_repo": "PalmasMich/release-candidate-cfru",
  "cfru_branch": "feature/cagliari-preview-0.1",
  "cfru_offset": "0x900000",
  "application_order": ["dpe", "cfru"]
}
```

The test must also read `.gitignore` and assert the literal patterns `*.gba`, `*.sav`, `*.sa1`, `*.sgm`, and `workspace/` are present.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python -m unittest tests.release_candidate.test_workspace_contract -v
```

Expected: FAIL because `release_candidate/pipeline.json` does not yet exist.

- [ ] **Step 3: Add the minimal pipeline metadata and ignore rules**

Create `release_candidate/pipeline.json` with the exact JSON above. Add the five required ignore patterns to `.gitignore` without deleting upstream rules.

- [ ] **Step 4: Add the workspace validator**

Create `tools/release_candidate/validate_workspace.py`. It must:

```python
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_SUFFIXES = {".gba", ".sav", ".sa1", ".sgm"}


def tracked_candidate_paths(root: Path):
    for path in root.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        yield path


def main() -> int:
    pipeline = json.loads((ROOT / "release_candidate/pipeline.json").read_text())
    assert pipeline["application_order"] == ["dpe", "cfru"]
    forbidden = [p for p in tracked_candidate_paths(ROOT) if p.suffix.lower() in FORBIDDEN_SUFFIXES]
    if forbidden:
        print("Forbidden ROM/save files in repository workspace:")
        for path in forbidden:
            print(path.relative_to(ROOT))
        return 1
    print("RELEASE_CANDIDATE_WORKSPACE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Document the exact private-ROM build order**

Create `docs/release-candidate/BUILD.md` describing these commands and no ROM download links:

```bash
# 1. Put the user's legally obtained FireRed 1.0 copy at:
#    workspace/BPRE0.gba

# 2. Work on a disposable copy for DPE.
cp workspace/BPRE0.gba ../release-candidate-dpe/BPRE0.gba
cd ../release-candidate-dpe
python scripts/make.py

# 3. Carry DPE's resulting ROM forward as the CFRU input.
cp test.gba ../release-candidate-cfru/BPRE0.gba
cd ../release-candidate-cfru
python scripts/make.py

# 4. The final local test ROM is release-candidate-cfru/test.gba.
```

State explicitly that all `.gba` files remain local and are deleted from repository worktrees after testing.

- [ ] **Step 6: Run contract tests and validator**

Run:

```bash
python -m unittest tests.release_candidate.test_workspace_contract -v
python tools/release_candidate/validate_workspace.py
```

Expected: all tests PASS and output includes `RELEASE_CANDIDATE_WORKSPACE_OK`.

- [ ] **Step 7: Commit**

```bash
git add .gitignore release_candidate/pipeline.json tools/release_candidate/validate_workspace.py tests/release_candidate/test_workspace_contract.py docs/release-candidate/BUILD.md
git commit -m "chore: lock release candidate ROM pipeline"
```

---

### Task 2: Prove the Clean Upstream DPE → CFRU Build

**Files:**
- Modify only if a compatibility failure is reproduced: `release_candidate/pipeline.json`, `docs/release-candidate/BUILD.md`
- Local-only input/output: `BPRE0.gba`, `test.gba`, `offsets.ini`

**Interfaces:**
- Consumes: the user's local FireRed 1.0 `BPRE0.gba`; `python scripts/make.py` in DPE then CFRU.
- Produces: one local-only final ROM that boots with both expansions applied and a recorded build transcript/checksum metadata that contains no ROM bytes.

- [ ] **Step 1: Verify the ROM file stays untracked before building**

Run in each repository after placing the local file:

```bash
git status --short
```

Expected: no `BPRE0.gba` entry.

- [ ] **Step 2: Build DPE on a disposable copy**

Run:

```bash
python scripts/make.py
```

Expected: exit code 0 and local `test.gba` plus `offsets.ini`.

- [ ] **Step 3: Use the DPE result as CFRU input and build CFRU**

Copy the DPE `test.gba` to CFRU as local `BPRE0.gba`, then run:

```bash
python scripts/make.py
```

Expected: exit code 0 and CFRU `test.gba`.

- [ ] **Step 4: Boot-smoke the resulting ROM in an emulator**

Verify manually or through available emulator automation that the title screen appears, New Game reaches the first controllable overworld state, and opening/closing the party menu does not crash.

Expected evidence record (text only):

```text
DPE_BUILD=PASS
CFRU_BUILD=PASS
BOOT=PASS
NEW_GAME=PASS
PARTY_MENU=PASS
```

- [ ] **Step 5: If and only if the combined build fails, debug before changing offsets**

Use `superpowers:systematic-debugging`. Do not guess new insertion offsets. Capture the failing command and error, determine whether the collision is DPE/CFRU code/data or a stale build, and change `pipeline.json` only after the root cause is proven.

- [ ] **Step 6: Commit only source/documentation changes**

If no compatibility changes were needed, there is no code commit for this task. If metadata/docs changed, commit only those files:

```bash
git add release_candidate/pipeline.json docs/release-candidate/BUILD.md
git commit -m "fix: document verified expansion integration"
```

Gate 0 passes only after Steps 1–4 pass.

---

### Task 3: Add the Stable First Release Candidate Species Contract in DPE

**Files:**
- Create: `release_candidate/creatures.json`
- Create: `tests/release_candidate/test_creature_contract.py`
- Modify: `include/species.h`
- Modify: `src/Base_Stats.c`

**Interfaces:**
- Consumes: DPE's current species numbering and `struct BaseStats` layout.
- Produces: permanent symbol `SPECIES_RC_TURTLE_01` and registry entry `rc_turtle_01`; later graphic tables and scripts use this symbol rather than a raw number.

- [ ] **Step 1: Write the failing source-contract test**

Create `tests/release_candidate/test_creature_contract.py` with `unittest`. It must assert:

```python
species_h = Path("include/species.h").read_text()
base_stats = Path("src/Base_Stats.c").read_text()
self.assertIn("SPECIES_RC_TURTLE_01", species_h)
self.assertIn("[SPECIES_RC_TURTLE_01]", base_stats)
```

It must load `release_candidate/creatures.json` and assert the first entry exactly contains:

```json
{
  "id": "rc_turtle_01",
  "symbol": "SPECIES_RC_TURTLE_01",
  "display_name": "VIANDANTE",
  "types": ["GRASS", "GROUND"],
  "base_stats": {"hp": 55, "attack": 56, "defense": 60, "speed": 50, "sp_attack": 38, "sp_defense": 51},
  "role": "starter"
}
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python -m unittest tests.release_candidate.test_creature_contract -v
```

Expected: FAIL because the registry and symbol do not exist.

- [ ] **Step 3: Allocate the next free DPE species ID without renumbering anything**

Inspect the last existing numeric `#define SPECIES_...` in `include/species.h`; append `SPECIES_RC_TURTLE_01` at the next free numeric value and update DPE's species-count sentinel only if the file already uses one. Never insert the symbol in the middle of existing numeric IDs.

- [ ] **Step 4: Add the registry entry**

Create `release_candidate/creatures.json` as a JSON array containing exactly the Viandante object above.

- [ ] **Step 5: Add Viandante's base-stat row following the adjacent DPE initializer shape**

Use the DPE `struct BaseStats` field names already defined in `include/base_stats.h`, assigning the six exact stats above, types `TYPE_GRASS`/`TYPE_GROUND`, and conservative existing abilities/items copied by semantic choice from an ordinary early-game species rather than introducing new engine mechanics.

- [ ] **Step 6: Run the contract test**

Run:

```bash
python -m unittest tests.release_candidate.test_creature_contract -v
```

Expected: PASS.

- [ ] **Step 7: Compile DPE source**

With local `BPRE0.gba` present, run:

```bash
python scripts/make.py
```

Expected: exit code 0. If compilation fails, use systematic debugging before altering the species numbering or struct layout.

- [ ] **Step 8: Commit**

```bash
git add release_candidate/creatures.json tests/release_candidate/test_creature_contract.py include/species.h src/Base_Stats.c
git commit -m "feat: register first release candidate starter"
```

---

### Task 4: Integrate Viandante Battle Art and Party Icon in DPE

**Files:**
- Create original source art under: `graphics/frontspr/`, `graphics/backspr/`, `graphics/pokeicon/`
- Modify: `src/Front_Pic_Table.c`
- Modify: `src/Back_Pic_Table.c`
- Modify: `src/Front_Pic_Coords_Table.c`
- Modify: `src/Back_Pic_Coords_Table.c`
- Modify: `src/Icon_Table.c`
- Modify: `src/Icon_Palette_Table.c`
- Modify as required by the existing adjacent DPE pattern: `include/sprite_data.h`, `include/graphics.h`
- Modify: `tests/release_candidate/test_creature_contract.py`

**Interfaces:**
- Consumes: `SPECIES_RC_TURTLE_01`; DPE grit pipeline and existing sprite declarations.
- Produces: front sprite, back sprite and party icon resolvable for `SPECIES_RC_TURTLE_01` with no fallback to another species.

- [ ] **Step 1: Extend the test to require all six table references**

Add assertions that the exact token `SPECIES_RC_TURTLE_01` occurs in each of:

```text
src/Front_Pic_Table.c
src/Back_Pic_Table.c
src/Front_Pic_Coords_Table.c
src/Back_Pic_Coords_Table.c
src/Icon_Table.c
src/Icon_Palette_Table.c
```

Also assert that three Viandante-owned source-art files exist under the corresponding graphics directories.

- [ ] **Step 2: Run the test and verify RED**

Expected: FAIL because art/table registrations do not exist.

- [ ] **Step 3: Create original pixel art for Viandante**

Produce an original turtle/wanderer starter with no copied Pokémon/Unbound silhouette or markings. Conform exactly to the dimensions, bit depth, palette and filename convention used by a neighboring DPE species in `graphics/frontspr/`, `graphics/backspr/`, and `graphics/pokeicon/`. The front and back sprites must read as the same character; the icon must preserve the shell/green-earth identity at party-menu scale.

- [ ] **Step 4: Register graphics using the existing DPE table pattern**

Add Viandante rows to all six tables. Add declarations in `include/sprite_data.h` / `include/graphics.h` only where the neighboring species pattern requires them; do not create a parallel graphics loader.

- [ ] **Step 5: Run source contract and DPE build**

Run:

```bash
python -m unittest tests.release_candidate.test_creature_contract -v
python scripts/make.py
```

Expected: PASS / exit code 0.

- [ ] **Step 6: Commit**

```bash
git add graphics include src tests/release_candidate/test_creature_contract.py
git commit -m "feat: add Viandante battle art"
```

---

### Task 5: Prove Gate 1 End-to-End Through CFRU

**Files:**
- Create in CFRU: `docs/release-candidate/evidence/gate-1.md`
- Modify DPE/CFRU source only if an actual reproduced integration defect requires it.
- Local-only: combined ROM and save data.

**Interfaces:**
- Consumes: built DPE species `SPECIES_RC_TURTLE_01`, combined DPE→CFRU ROM.
- Produces: documented evidence that one original species renders, battles, joins/exists in party, saves and reloads without corruption.

- [ ] **Step 1: Rebuild the combined ROM from a clean private base**

Apply DPE first and CFRU second using the Task 1 build procedure. Do not reuse a hand-edited ROM from an earlier test.

- [ ] **Step 2: Inject/add Viandante to a controlled test party using an existing XSE/CFRU script command rather than editing save bytes**

Use CFRU's existing scripting command set and the symbolic species ID generated by DPE. The temporary test event may exist only in the local ROM workspace; the permanent Cagliari starter event belongs to the next implementation plan.

- [ ] **Step 3: Validate visual/runtime behavior**

In emulator, verify all of the following:

```text
NAME=VIANDANTE
FRONT_SPRITE=PASS
BACK_SPRITE=PASS
PARTY_ICON=PASS
SUMMARY_STATS=PASS
BATTLE_START=PASS
MOVE_EXECUTION=PASS
BATTLE_END=PASS
SAVE=PASS
RELOAD=PASS
PARTY_AFTER_RELOAD=PASS
```

- [ ] **Step 4: Write the evidence record**

Create `docs/release-candidate/evidence/gate-1.md` containing the exact checklist above, tested emulator name/version, DPE commit SHA, CFRU commit SHA, and no ROM/hash value that can be used as a download source. Screenshots may be referenced only if they contain gameplay output, not ROM bytes.

- [ ] **Step 5: Run repository hygiene validation again**

Run in both repos:

```bash
git status --short
```

In CFRU also run:

```bash
python tools/release_candidate/validate_workspace.py
```

Expected: no ROM/save files staged or untracked in repository paths and validator prints `RELEASE_CANDIDATE_WORKSPACE_OK`.

- [ ] **Step 6: Commit Gate 1 evidence**

```bash
git add docs/release-candidate/evidence/gate-1.md
git commit -m "test: verify first custom species end to end"
```

Gate 1 passes only when every checklist item is `PASS`. If any item fails, use `superpowers:systematic-debugging` and keep Gate 1 open.

---

## Next Plan After Gate 1

Do not start Cagliari mapping before Gate 1 passes. The next implementation plan will cover Gates 2–3: the three starter species, Delivery Hub starter event, compressed Marina/Porto map, first custom wild species, rival/trainer battle, Deploy teaser, visual polish, save/reload regression run, and patch-candidate generation. This split is intentional: the largest technical risk is proving that the historical binary-hacking toolchain and a new DPE species work together cleanly before authored map/story work begins.

## Self-Review Result

- **Spec coverage for this plan:** Gate 0 and Gate 1 are fully covered; map/story/polish requirements are intentionally deferred to the second plan after the technical foundation proves viable.
- **Placeholders:** none; stable species symbol, working display identity, typing, stats, offsets, branch names, commands and validation outputs are explicit.
- **Type/interface consistency:** DPE→CFRU order, species symbol `SPECIES_RC_TURTLE_01`, registry key `rc_turtle_01`, and branch names are consistent across tasks.
