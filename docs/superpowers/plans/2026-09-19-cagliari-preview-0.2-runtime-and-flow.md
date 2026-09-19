# Cagliari Preview 0.2 Runtime and Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the source-level cause of the post-starter crash, make that integration fail closed in the private build, and advance the authored V0.2 opening/dialogue/map contracts without claiming an unrun ROM smoke test.

**Architecture:** DPE remains the owner of custom-species runtime tables and receives explicit National Dex identities for all four active RC species. CFRU consumes that contract through a cross-repository pre-build validator, while its existing relocatable script/map pipeline continues to own Chapter 1 flow. Content improvements stay declarative in `content/cagliari_preview/`; binary changes remain structurally validated and private-ROM runtime checks remain a separate gate.

**Tech Stack:** Python 3 standard library, `unittest`, DPE/CFRU C tables, JSON content manifests, FireRed event bytecode, Git.

**Spec:** `docs/rom/CAGLIARI_PREVIEW_0_2_REBUILD.md`

## Global Constraints

- Work only on `feature/cagliari-preview-0.2-rebuild` in CFRU and the declared RC DPE integration branch; never modify or merge `master`.
- Preserve species IDs `0x050E` through `0x0511` and Chapter 1 flags `0x0AF` through `0x0B9`.
- Never commit `BPRE0.gba`, generated ROMs, saves, or ROM-derived binaries.
- Do not patch ambiguous binary signatures; fail closed.
- Keep DPE -> CFRU build order and retain the existing Linux audio/charmap/build fixes.
- Do not claim the runtime crash fixed until all three starters pass a clean private-ROM smoke matrix.

## Review Focus

- A custom species with a zero/default Species -> National Dex entry must fail source validation before a private build.
- All active RC species must have unique non-zero National Dex identities within the expanded count.
- DPE overlay apply/restore must include every newly patched table and leave upstream source byte-for-byte restored.
- CFRU must validate the sibling DPE checkout actually selected by the build, not a hard-coded unrelated path.
- Source-only success must remain visibly distinct from private-ROM runtime success.

---

### Task 1: DPE National Dex runtime contract

**Files:**
- Modify: `../release-candidate-dpe/include/release_candidate_species.h`
- Modify: `../release-candidate-dpe/include/pokedex.h`
- Modify: `../release-candidate-dpe/release_candidate/preview_species.json`
- Modify: `../release-candidate-dpe/release_candidate/preview_runtime_contract.json`
- Modify: `../release-candidate-dpe/scripts/apply_release_candidate_overlay.py`
- Create: `../release-candidate-dpe/tests/test_rc_pokedex_runtime.py`

**Interfaces:**
- Consumes: stable species symbols and numeric IDs from `include/release_candidate_species.h`.
- Produces: unique `NATIONAL_DEX_RC_*` values, rendered Species -> National Dex entries, and complete RC Pokédex records/descriptions in the transactional DPE overlay.

- [ ] **Step 1: Write the failing runtime-table tests**

```python
def test_every_active_rc_species_has_unique_nonzero_national_dex_mapping():
    rendered = overlay.render_species_to_pokedex(species)
    for item in species:
        assert f"[{item['id']} - 1] = {item['national_dex_symbol']}" in rendered

def test_overlay_tracks_all_pokedex_targets():
    assert overlay.SPECIES_TO_POKEDEX in overlay.TARGETS
    assert overlay.POKEDEX_DATA in overlay.TARGETS
    assert overlay.POKEDEX_STRINGS in overlay.TARGETS
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_rc_pokedex_runtime -v`

Expected: FAIL because the manifest/renderers/targets do not yet exist.

- [ ] **Step 3: Implement the minimal complete DPE mapping**

Add National Dex IDs 899-902, extend `FINAL_DEX_ENTRY`, add manifest metadata, render transactional entries into `Species_To_Pokdex_Table.c`, `Pokedex_Data_Table.c`, and `strings/Pokedex_Data.string`, and include those files in backup/restore.

- [ ] **Step 4: Verify GREEN and the DPE suite**

Run: `python -m unittest tests.test_rc_pokedex_runtime -v`

Expected: PASS.

Run: `python -m unittest discover -s tests -v`

Expected: all DPE tests PASS.

- [ ] **Step 5: Commit**

```bash
git add include/release_candidate_species.h include/pokedex.h release_candidate/preview_species.json release_candidate/preview_runtime_contract.json scripts/apply_release_candidate_overlay.py tests/test_rc_pokedex_runtime.py
git commit -m "fix: assign RC species valid National Dex entries"
```

### Task 2: CFRU cross-repository starter integrity gate

**Files:**
- Modify: `scripts/validate_rc_starter_runtime.py`
- Modify: `scripts/build_release_candidate.py`
- Create: `tests/test_rc_starter_runtime_validator.py`
- Modify: `tests/test_release_candidate_build_pipeline.py`
- Modify: `docs/rom/POST_STARTER_CRASH_DIAGNOSTIC.md`

**Interfaces:**
- Consumes: DPE `preview_species.json`, overlay renderer, RC National Dex constants, and the build's `--dpe-path`.
- Produces: `validate(dpe_root: Path) -> list[str]` and a build stage that rejects missing/zero/duplicate custom mappings before CFRU compilation.

- [ ] **Step 1: Write failing validator tests**

```python
def test_validator_rejects_missing_rc_national_dex_mapping(self):
    errors = validator.validate(self.fixture_dpe_root)
    self.assertIn("missing National Dex mapping", "\n".join(errors))

def test_pipeline_passes_selected_dpe_root_to_runtime_validator(self):
    self.assertEqual(captured, [dpe_root])
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.test_rc_starter_runtime_validator tests.test_release_candidate_build_pipeline -v`

Expected: FAIL because the validator does not accept/inspect a DPE root and the pipeline callback has no argument.

- [ ] **Step 3: Implement the cross-repository gate**

Parse the four active DPE species, require stable CFRU/DPE IDs, require unique non-zero `national_dex` values, require rendered table/data/string registration, add `--dpe-path`, and pass the selected checkout through `run_pipeline`.

- [ ] **Step 4: Verify GREEN and CFRU source preflight**

Run: `python -m unittest tests.test_rc_starter_runtime_validator tests.test_release_candidate_build_pipeline -v`

Expected: PASS.

Run: `python scripts/preflight_chapter1.py`

Expected: `CHAPTER1_PREFLIGHT=PASS`.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_rc_starter_runtime.py scripts/build_release_candidate.py tests/test_rc_starter_runtime_validator.py tests/test_release_candidate_build_pipeline.py docs/rom/POST_STARTER_CRASH_DIAGNOSTIC.md
git commit -m "fix: fail private build on incomplete starter dex wiring"
```

### Task 3: V0.2 authored opening and dialogue guardrails

**Files:**
- Modify: `content/cagliari_preview/dialogue.yml`
- Modify: `scripts/audit_rc_opening.py`
- Modify: `tests/test_cagliari_content.py`
- Modify: `tests/test_release_candidate_preview_patch.py`

**Interfaces:**
- Consumes: the approved Delivery Lead, KPI Rival, Consulente Junior, Release Manager, and System voice definitions.
- Produces: consistently authored Chapter 1 copy and an opening audit that rejects visible Oak/Pallet/rival-naming remnants while distinguishing text replacement from structural bypass.

- [ ] **Step 1: Write failing voice and opening-audit tests**

```python
def test_kpi_rival_uses_fixed_authored_speaker_name(self):
    self.assertNotIn("Rivale", speakers)
    self.assertIn("KPI Rival", speakers)

def test_opening_audit_rejects_rival_name_prompt(self):
    with self.assertRaisesRegex(RuntimeError, "rival-name"):
        audit.validate_opening(fixture_with_rival_prompt)
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.test_cagliari_content tests.test_release_candidate_preview_patch -v`

Expected: FAIL on legacy `Rivale` speaker labels and the missing structural audit contract.

- [ ] **Step 3: Make the minimum authored-content changes**

Normalize the fixed KPI Rival identity, tighten each named voice, keep System deadpan, remove legacy naming semantics from authored content, and make the audit report structural rival-name bypass as an explicit pending/runtime gate when it cannot prove it from source.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_cagliari_content tests.test_release_candidate_preview_patch -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add content/cagliari_preview/dialogue.yml scripts/audit_rc_opening.py tests/test_cagliari_content.py tests/test_release_candidate_preview_patch.py
git commit -m "content: enforce authored V0.2 character voices"
```

### Task 4: Source verification and private smoke handoff

**Files:**
- Modify: `docs/rom/BUILD_VERIFICATION.md`
- Modify: `docs/rom/POST_STARTER_CRASH_DIAGNOSTIC.md`

**Interfaces:**
- Consumes: passing DPE/CFRU suites and the one-command private build.
- Produces: exact Codespaces commands and a three-starter smoke record that cannot be marked PASS without private ROM evidence.

- [ ] **Step 1: Run all source checks**

Run in DPE: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

Run in CFRU: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

Run in CFRU: `python scripts/preflight_chapter1.py`

Expected: `CHAPTER1_PREFLIGHT=PASS`.

- [ ] **Step 2: Check binary hygiene**

Run: `git ls-files '*.gba' '*.sav' '*.srm'`

Expected: no output in either repository.

- [ ] **Step 3: Attempt the supported private build only when a lawful local ROM exists**

Run: `python scripts/build_release_candidate.py --dpe-path ../release-candidate-dpe`

Expected with ROM: `BUILD_STATUS=SUCCESS`; expected without ROM: explicit `Private base ROM not found`/workspace block, recorded as not run rather than success.

- [ ] **Step 4: Document the exact clean-save matrix**

Record Tartrek, Frobyte, and Emberfox separately for confirmation text, party open, save/reload, and KPI Rival progression. Leave every runtime result `PENDING` until observed.

- [ ] **Step 5: Commit**

```bash
git add docs/rom/BUILD_VERIFICATION.md docs/rom/POST_STARTER_CRASH_DIAGNOSTIC.md
git commit -m "docs: define V0.2 private runtime acceptance gate"
```
