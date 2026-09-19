# Release Candidate ROM — Cagliari Preview 0.1 Design

## Goal
Build a short, polished 10–15 minute ROM-hack preview that validates the new Release Candidate direction before expanding the whole game.

The preview must demonstrate, together in one playable slice:
- FireRed + Complete FireRed Upgrade (CFRU) as the gameplay foundation;
- Dynamic Pokémon Expansion (DPE) for original Release Candidate creatures;
- a recognizable, compressed reinterpretation of real Cagliari;
- the corporate-satire tone;
- an original starter choice;
- an original wild encounter;
- a short rival encounter and trainer battle;
- a closing teaser for the first Deploy arc.

This preview is a fan project and must remain non-commercial. No ROM binary is committed to GitHub. Distribution, if later approved, must be patch-based rather than distributing a copyrighted base ROM.

## Technical foundation

### CFRU repository
Primary orchestration repository:
`PalmasMich/release-candidate-cfru`

Working branch:
`feature/cagliari-preview-0.1`

CFRU remains responsible for battle engine, scripting hooks, configuration, QoL systems and runtime integration.

### DPE repository
Creature-content repository:
`PalmasMich/release-candidate-dpe`

Working branch:
`feature/cagliari-preview-0.1`

DPE is responsible for adding original Release Candidate species, their data, sprites, icons and cries.

### Base ROM handling
A legally obtained FireRed 1.0 ROM remains a local build input named `BPRE0.gba`, following the upstream toolchain. It must never be committed.

## Preview scope

### Playtime
Target: 10–15 minutes for a first blind playthrough.

### Narrative flow
1. Opening in Cagliari.
2. The protagonist is told: “Benvenuto a Cagliari. Il progetto era già iniziato quando sei arrivato.”
3. Arrival at the Delivery Hub.
4. Improvised onboarding and starter assignment.
5. Starter choice among three original Release Candidate creatures.
6. First encounter with the KPI/Story Point-obsessed rival.
7. Exit into the Marina/Port area.
8. First wild encounter with an original local creature.
9. One short trainer battle.
10. Closing beat reveals that the project’s first Deploy is blocked and tees up the future Go/No-Go chapter.

The first Release Manager boss and the full Deploy Clearance sequence are explicitly out of scope for Preview 0.1.

## Cagliari design
Cagliari is real-world recognizable but geographically compressed for RPG playability. It is not a 1:1 map reconstruction.

### Preview areas
- **Delivery Hub** — onboarding, starter choice, first exposition.
- **Marina / Porto** — first exterior hub area and strongest Cagliari identity.
- **Short connection route** — enough traversal to support encounters and one trainer.

Future branches such as Castello/Bastione, green urban zones and the business/deploy district are reserved for the full Cagliari chapter.

### Visual identity
The preview should evoke Cagliari through:
- Mediterranean light and warm limestone;
- port/sea cues;
- palms and urban greenery;
- compressed historic/urban architecture;
- elevation or skyline hints where feasible;
- custom tiles and palettes sufficient to avoid feeling like an unchanged Kanto map.

The goal is not photorealism. The goal is immediate recognition and a polished Gen-3/Gen-4-inspired ROM-hack presentation benchmarked against high-quality projects such as Unbound, without copying Unbound-specific assets or maps.

## Creatures
Preview 0.1 requires 4–6 original creatures.

### Mandatory
- Starter A: turtle/wanderer line — base stage only required in this preview.
- Starter B: frog line — base stage only required in this preview.
- Starter C: fire-fox line — base stage only required in this preview.
- Wild creature 1 — Cagliari-local identity.
- Wild creature 2 — optional if schedule allows; otherwise Preview 0.2.
- Rival creature — may be one of the two unchosen starters for the first preview, avoiding an unnecessary sixth bespoke species.

The long-term target remains approximately 15 original creatures for the complete Cagliari vertical slice, then ~30 for the first substantial release, followed by progressive replacement of official Pokémon over time.

### Data requirements
Each playable original creature needs:
- stable species identifier;
- name;
- typing;
- base stats;
- starter/wild/rival role;
- minimal learnset sufficient for Preview 0.1;
- front sprite;
- back sprite where battle presentation requires it;
- icon;
- cry (temporary original/synthetic cry is acceptable for 0.1 if clearly tracked for replacement).

## Starter scene
The starter selection intentionally parodies staffing/allocation rather than copying the classic professor presentation.

The Delivery Hub lead explains that these are the “resources currently available” and the protagonist must choose one for the assignment.

The three starter creatures should be displayed as equals. No choice is framed as canonically better.

## Rival
The rival is a capable colleague who treats everything as competition and is obsessed with KPI, velocity and story points.

He is not evil and should occasionally be useful. His Preview 0.1 appearance should establish:
- competitiveness;
- corporate jargon;
- confidence in metrics;
- a short battle or challenge that functions as gameplay onboarding.

## Tone and writing
Tone: affectionate corporate/IT satire, understandable even to players who do not work in Agile environments.

Jokes should work at two levels:
- surface-level absurd workplace humor;
- deeper references for analysts/developers/consultants.

Avoid making every line a jargon joke. Cagliari and the adventure should still feel like a place worth exploring.

## Gameplay
Preview 0.1 keeps CFRU’s mature battle infrastructure rather than recreating systems.

Required gameplay loop:
- walk/explore;
- talk/interact;
- starter selection;
- party creation;
- wild encounter;
- trainer/rival battle;
- basic healing/save loop inherited from the base where practical.

No custom mission system, difficulty selector, Mega/Z mechanics or advanced optional CFRU systems are required for 0.1 unless they are already enabled harmlessly by the chosen baseline.

## Mapping and scripting strategy
Use the existing FireRed ROM/event model plus CFRU scripting hooks. Prefer custom map content and event scripts over invasive engine modifications.

Preview 0.1 should minimize irreversible low-level changes. Engine modifications are justified only where needed for original species integration or a clear Release Candidate identity requirement.

## Art strategy
The preview should prioritize a small amount of authored, coherent art over a large amount of placeholder content.

Order of priority:
1. starter battle sprites/icons;
2. player/rival overworld appearance sufficient for the preview;
3. Cagliari Marina/Port tiles/palette;
4. wild creature sprite/icon;
5. Delivery Hub visual identity;
6. optional polish assets.

Custom art must be original or properly licensed. Do not copy assets from Pokémon Unbound or other fan projects.

## Build and repository governance
- Never commit `BPRE0.gba`, generated `test.gba`, commercial ROM data dumps or other copyrighted ROM binaries.
- Development occurs on `feature/cagliari-preview-0.1` or branches derived from it.
- `master` remains untouched until an explicit review/merge decision.
- CFRU and DPE changes must use matching species IDs/configuration contracts documented in-repo.
- Generated build artifacts should be ignored unless they are legally redistributable test metadata.

## Validation gates

### Gate 0 — Toolchain
Pass when:
- clean build environment is documented;
- DPE can compile/insert against the expected base;
- CFRU can compile/insert in the intended order;
- no ROM file is committed.

### Gate 1 — Custom creature
Pass when one original starter:
- exists in DPE data;
- renders correctly in battle;
- has working icon/name/stats/moves;
- can be added to the player party without crash/save corruption.

### Gate 2 — Cagliari playable loop
Pass when the player can:
- start the preview;
- reach Delivery Hub;
- select a starter;
- walk into Marina/Port;
- trigger and finish a custom wild encounter;
- complete the rival/trainer battle.

### Gate 3 — Preview candidate
Pass when:
- all three starters are selectable;
- 4–6 original creatures/assets required by scope are integrated;
- story flow reaches the Deploy teaser;
- representative saves/reloads work;
- no blocker/crash exists in a complete 10–15 minute run;
- screenshots visibly read as Release Candidate/Cagliari rather than stock FireRed.

## Out of scope for Preview 0.1
- full Cagliari chapter;
- first Go/No-Go boss;
- Deploy Clearance reward;
- Milano/India/Japan/Cupertino maps;
- 15+ complete original-species roster;
- replacing all official Pokémon;
- remastered standalone Godot version;
- commercial distribution;
- large-scale engine rewrites.

## Success criterion
A player should finish Preview 0.1 and understand, without explanation, that this is a Pokémon-style ROM-hack adventure with its own corporate satire, original creatures and Cagliari setting — and should want to see the first Deploy chapter next.
