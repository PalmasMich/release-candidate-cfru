# Release Candidate — Cagliari Preview 0.2 Rebuild

Branch: `feature/cagliari-preview-0.2-rebuild`

## Purpose

Preview 0.1 is retained as the technical proof-of-tech baseline:
- DPE + CFRU private build works;
- six custom maps can be compiled and installed atomically;
- story flags, relocatable event scripts and dialogue payloads exist;
- the first full private ROM was produced successfully.

Preview 0.2 is a presentation and content rebuild, not a cosmetic pass.

The target is a first chapter that feels like an original game running on FireRed/CFRU rather than a FireRed reskin.

## Non-negotiable goals

1. Replace the vanilla-style opening flow.
2. Replace bootstrap environments with authored Cagliari locations.
3. Rewrite all chapter dialogue from scratch.
4. Replace placeholder starter art with production-quality original creatures.
5. Preserve the stable RC species IDs and story flags.
6. Fix the current post-starter runtime crash before the new story flow is considered playable.
7. Keep master untouched and keep all private ROM files outside Git.

## Opening sequence — full redesign

The game must no longer feel like Professor Oak / Pallet Town with changed text.

Target opening:

1. Release Candidate title screen.
2. New-project onboarding scene.
3. Delivery Lead introduces the player to the project.
4. Name selection is reframed as creation of the player's corporate profile / badge.
5. Optional short player-look selection if technically safe.
6. Arrival in Cagliari.
7. First visual reveal of the city.
8. Delivery Hub onboarding.
9. Starter assignment.

The original Oak speech, Pokémon-world exposition and grandson framing must not be visible in the final 0.2 path.

### Name selection tone

The player is asked how their name should appear in the delivery workspace / badge, not asked the vanilla "what is your name?" question.

Example intent only, not final copy:

- "Prima di aprirti gli accessi, come vuoi comparire nel workspace?"
- player enters name
- "Perfetto. Badge creato. Accessi quasi pronti. Quasi."

The rival name selection should be removed from the player-facing flow. KPI Rival must have a fixed authored identity or title.

## Cagliari environment rebuild

Bootstrap General/Celadon/House tiles are temporary and must not define the final look.

### Visual north star

- Mediterranean Sardinia;
- warm limestone;
- strong sunlight;
- teal/turquoise sea accents;
- ochre, cream and terracotta architecture;
- palm / coastal vegetation used selectively;
- modern illustrative handheld-game readability;
- clearly custom composition, not Pallet/Viridian visual language.

### Required authored locations

#### Delivery Hub
Indoor product/delivery space:
- warm limestone + contemporary office details;
- three physical starter stations;
- large project board / release board;
- windows or terrace cues to Cagliari;
- no Oak Lab silhouette.

#### Marina
Must read instantly as Cagliari waterfront:
- sea edge / quay;
- limestone buildings;
- boats / port cues;
- Mediterranean light;
- delivery lead positioned naturally in the environment;
- route to Port Link visually obvious.

#### Port Link
A transitional waterfront path, not Route 1:
- promenade / port service lane;
- patches of vegetation for encounters;
- visible water / harbor infrastructure;
- a clear trainer checkpoint.

#### Castello
Strong vertical limestone identity:
- climb / stair rhythm;
- walls, viewpoints, narrow passages;
- visual sense of elevation;
- not a generic mountain route.

#### Deploy District
Urban/corporate climax:
- evening or late-afternoon possibility;
- stronger release / operations identity;
- clear Go/No-Go checkpoint.

#### Deploy Room
Final Chapter 1 interior:
- release control room / war room;
- screens, release board, deployment visual language;
- dramatic boss staging.

## Dialogue rewrite

All Chapter 1 dialogue must be rewritten as authored conversation, not short functional placeholders.

Tone:
- dry corporate satire;
- natural Italian;
- readable by people who do not work in Agile;
- occasional technical terms only when the joke still works without specialist knowledge;
- characters should have distinct voices.

### Character voices

Delivery Lead:
- competent;
- tired but sharp;
- knows the project is chaotic;
- not a caricature.

KPI Rival:
- competitive;
- obsessed with metrics and dashboards;
- insists it is "not a competition" while clearly treating it as one.

Consulente Junior:
- eager;
- slightly anxious;
- repeats phrases they have heard from seniors.

Release Manager:
- concise;
- intimidating;
- speaks in Go/No-Go, rollback, evidence and risk language.

System messages:
- minimal;
- deadpan;
- used sparingly.

## Starter art rebuild

The current starter sprites are placeholders and must be replaced.

The new pipeline must begin with high-quality concept art before pixel conversion.

### Tartrek
Core identity:
- young turtle / wandering traveler;
- Grass/Ground;
- readable silhouette at small size;
- shell integrated with travel / terrain motifs;
- confident but not aggressive;
- no direct resemblance to existing Pokémon.

### Frobyte
Core identity:
- compact blue frog;
- Water/Electric;
- expressive face;
- electric accents integrated into amphibian anatomy;
- agile silhouette;
- later evolution may become more imposing.

### Emberfox
Core identity:
- fox-like fire creature;
- Fire/Dark;
- sharper silhouette than the other two;
- dark ear/tail/flame accents;
- mischievous rather than evil;
- must remain distinct from existing fire fox creatures in commercial monster franchises.

### Art quality gate

Before a sprite enters DPE:
1. concept art approved;
2. silhouette test at thumbnail size;
3. front battle pose approved;
4. back battle pose approved;
5. palette approved;
6. icon approved;
7. only then pixel conversion / integration.

Do not auto-convert weak concept art into sprites and treat it as final.

## Technical migration rules

- Keep species IDs 0x050E–0x0511 stable.
- Keep Chapter 1 flag IDs 0x0AF–0x0B9 stable.
- Existing six-map linker/installer infrastructure may be reused.
- Map dimensions may change if necessary, but warp contracts must be revalidated.
- Custom tileset work must not reuse copyrighted Pokémon/Nintendo art.
- Private ROM remains local-only.
- No merge to master during 0.2 development.

## Immediate implementation order

1. Reproduce and fix the post-starter crash.
2. Replace the vanilla intro/name flow.
3. Freeze final Chapter 1 narrative beats.
4. Rewrite all dialogue.
5. Produce new starter concepts and approve them.
6. Build custom Cagliari tileset / map art.
7. Integrate new sprites and maps.
8. Private ROM build.
9. Full Chapter 1 smoke test.
10. Only after runtime pass, polish social/demo presentation.

## 0.2 completion definition

0.2 is not complete merely because it builds.

It is complete when:
- the player sees no obvious Oak/Pallet bootstrap in the intended path;
- the intro and naming sequence feel authored for Release Candidate;
- all six locations have distinct Cagliari-specific visual identity;
- all Chapter 1 dialogue is rewritten;
- all three starters have approved, high-quality original art and functional sprites;
- the post-starter crash is fixed;
- the full Chapter 1 loop passes on a private ROM from new game to Deploy 01 completion.
