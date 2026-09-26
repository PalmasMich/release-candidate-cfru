# Release Candidate — Chapter 1: Cagliari

## Core direction

Release Candidate uses FireRed/CFRU/DPE as a technical engine, **not** as the world, plot, map progression or narrative template.

The long-term target is an original monster-training RPG with:

- original story progression;
- original characters;
- original maps and area layouts;
- original event scripts and cutscenes;
- original chapter structure;
- original creatures progressively replacing temporary official species;
- corporate/IT satire as a narrative layer rather than a simple text reskin.

The current Route 1 / Pallet reuse is a **technical bootstrap only**. It exists to prove the build pipeline, custom species, event scripting, trainer battles and save-safe runtime behavior. It must not become the permanent Chapter 1 layout.

## Chapter role

Cagliari is the first complete story chapter and the player's real starting region.

Target full-chapter playtime: **30–45 minutes** for the first substantial implementation.

Preview 0.1 is the first 10–15 minutes of this chapter, not a disposable demo.

## Chapter arc

### Act 1 — Late onboarding

The protagonist arrives after the project has already started.

Opening line:

> Benvenuto a Cagliari. Il progetto era già iniziato quando sei arrivato.

The player reaches the Delivery Hub, receives minimal context and is assigned one of three original starter creatures.

The KPI-focused rival is introduced as a competent colleague who turns every activity into a measurable competition.

### Act 2 — First assignment

The player leaves the Delivery Hub and enters a custom Marina/Porto district.

Goals:

- establish Cagliari visually;
- introduce exploration and local wild creatures;
- introduce the first small delivery task;
- meet the Consulente Junior;
- complete the first trainer battle.

The current former-Route-1 implementation is only the bootstrap for this sequence.

### Act 3 — Scope changes

The apparent simple task starts changing.

Story beats:

- a requirement is modified after implementation has already begun;
- a stakeholder contradicts the original request;
- the rival treats the change as an opportunity to improve velocity;
- the Delivery Lead asks the player to reach the business/deploy district.

The player gains access to a second part of Cagliari rather than returning to stock FireRed progression.

### Act 4 — Go / No-Go

The player reaches the first deployment checkpoint.

The first Release Manager functions as the chapter boss / gatekeeper.

The confrontation should combine battle progression with the corporate premise: the player has technically completed the requested work, but the release cannot proceed because new conditions have appeared.

### Act 5 — Deploy 1

After resolving the blockers, the player completes the first Deploy.

Reward/progression concept:

- first Deploy Clearance;
- access to the next chapter;
- rival progression;
- teaser for Milano / the next project environment.

## Custom Cagliari areas

Permanent Chapter 1 area IDs:

1. `RC_CAGLIARI_ARRIVAL`
   - opening / arrival beat;
   - short transition into the Delivery Hub.

2. `RC_DELIVERY_HUB`
   - onboarding;
   - starter assignment;
   - recurring safe hub;
   - early healing/save support.

3. `RC_CAGLIARI_MARINA`
   - first major exterior area;
   - sea, port, palms, warm facades;
   - NPCs and first local identity.

4. `RC_PORT_CONNECTION`
   - encounter/trainer corridor;
   - later replaced by a fully authored custom layout.

5. `RC_CASTELLO_ASCENT`
   - vertical/elevated Cagliari identity;
   - scope-change story beat;
   - exploration and second encounter cluster.

6. `RC_DEPLOY_DISTRICT`
   - business/deploy area;
   - Go/No-Go sequence;
   - Release Manager confrontation.

7. `RC_DEPLOY_ROOM_01`
   - first chapter climax;
   - Deploy 1 completion.

## Narrative systems

Chapter 1 should progressively move away from binary replacement of existing FireRed scripts toward source-controlled original event definitions.

Required story-system concepts:

- chapter flags;
- area unlock flags;
- cutscene completion flags;
- rival progression state;
- deploy state;
- optional NPC dialogue variants after major events.

## Bootstrap retirement rule

Any implementation that directly repurposes a stock FireRed map, NPC or script must be tagged as `bootstrap_only`.

A bootstrap element may remain only until the equivalent custom map/event has passed a smoke test.

For Preview 0.1, acceptable bootstrap elements include:

- former Route 1 encounter table;
- former Route 1 Mart Clerk NPC used as the Consulente Junior trainer proof;
- stock geometry while custom Cagliari maps are not yet inserted.

These are not part of the permanent design.

## Quality benchmark

The benchmark is the degree of transformation achieved by high-quality ROM hacks: the player should feel they are playing a new game built on a mature engine.

Do not copy Pokémon Unbound maps, assets, music, dialogue or proprietary creative content.

The useful benchmark is:

- confidence to replace the original world;
- dense scripted events;
- strong area identity;
- custom progression;
- polished presentation;
- coherent original story.

## Immediate implementation priority

1. Preserve the current bootstrap until trainer-battle and custom-species runtime are proven.
2. Introduce permanent Chapter 1 map IDs and flags now.
3. Create the custom map/event insertion pipeline.
4. Replace Delivery Hub first.
5. Replace Marina/Porto next.
6. Move the wild encounter and Consulente Junior trainer from bootstrap Route 1 into the custom Port Connection map.
7. Continue into Castello Ascent and Deploy District.
