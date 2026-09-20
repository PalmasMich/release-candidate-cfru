# Release Candidate — Cagliari Location Bible v0.2

This document freezes the environmental identity of Chapter 1 before final tileset and map production.

## Global art direction

Cagliari must read as a real Mediterranean city translated into a compact handheld monster-training RPG language.

Core visual vocabulary:
- warm limestone and cream plaster;
- sea blue / turquoise accents;
- terracotta and ochre;
- strong sun and high-contrast shadows;
- palms and coastal vegetation used selectively;
- narrow streets, stairs, walls and height changes;
- modern city details mixed with historic fabric;
- clean pixel readability over photorealism.

The goal is recognisable atmosphere, not literal 1:1 reconstruction.

Avoid:
- Pallet/Viridian visual language;
- generic tropical islands;
- generic fantasy castle imagery;
- copied Nintendo/Pokémon tiles or landmark art;
- excessive tourist-postcard clutter.

## 1. Delivery Hub

Narrative role:
- player onboarding;
- starter assignment;
- first KPI Rival interaction;
- establishes the corporate satire.

Visual identity:
- contemporary delivery/product workspace inside a warm limestone building;
- large windows or terrace cues toward the city/sea;
- teal accents, light wood, stone, plants;
- large release board / backlog wall;
- three physically distinct starter stations;
- cables, screens and paperwork used as visual storytelling.

Must feel like:
- "modern Cagliari office inside old Mediterranean architecture".

Must not feel like:
- laboratory;
- Pokémon Center;
- Oak Lab reskin;
- generic office cubicle farm.

Key props:
- release board;
- three starter pedestals;
- delivery dashboard screen;
- coffee area;
- access badge terminal;
- windows/terrace.

## 2. Marina

Narrative role:
- first major outdoor reveal;
- visual proof that the game is really set in Cagliari;
- hub for optional interactions;
- gateway to Port Link and later Castello.

Visual identity:
- waterfront promenade;
- pale stone paving;
- harbor edge and visible water;
- moored boats / masts used as background rhythm;
- cream and ochre facades;
- palms, lamps, benches;
- bright Mediterranean daylight.

Composition:
- player should see water quickly after entering;
- Port Link direction must be visually obvious;
- Castello direction should read as "uphill";
- Locanda del Molo should sit naturally along the promenade, not as a detached gimmick.

Optional micro-location: Locanda del Molo
- original fictional venue;
- warm wood frontage;
- lantern accents;
- compact ramen counter / izakaya-inspired interior;
- no use of real venue names or branding;
- optional rest/story interaction;
- tone: safe pause from project chaos.

## 3. Port Link

Narrative role:
- first field-testing zone;
- wild encounter tutorial;
- first minor trainer checkpoint.

Visual identity:
- harbor service road / promenade transition;
- stone paving mixing into rougher terrain;
- fenced port infrastructure;
- water glimpses;
- patches of coastal grass;
- low walls, bollards, utility lamps;
- a clear visual checkpoint.

Must not feel like:
- Route 1;
- generic grass corridor;
- forest path.

Encounter vegetation:
- coastal grass patches should be intentional and limited;
- wild area should look integrated into the urban waterfront edge.

## 4. Castello Ascent

Narrative role:
- scope-change detour;
- chapter's strongest sense of vertical progression;
- bridge from waterfront to release climax.

Visual identity:
- limestone stairs;
- bastions and walls;
- narrow passages;
- overlooks;
- strong elevation;
- glimpses of sea and lower city;
- planters / small vegetation between stone surfaces.

Mood:
- late afternoon is acceptable if technically feasible;
- warmer shadows than Marina;
- ascent should feel earned.

Must not feel like:
- mountain route;
- medieval fantasy castle;
- cave.

Optional viewpoint:
- short dead-end overlook;
- city/sea panorama implication;
- one memorable line of dialogue;
- no gameplay reward required in v0.2.

## 5. Deploy District

Narrative role:
- transition from city adventure to release climax;
- Go/No-Go staging area.

Visual identity:
- more contemporary urban zone while still unmistakably Cagliari;
- stone + glass + concrete;
- red release/status accents;
- monitors / status terminals integrated into streetscape;
- stronger evening / golden-hour feeling if feasible.

Mood:
- controlled tension;
- many people waiting;
- "everything is ready except the decision".

Must not feel like:
- generic cyberpunk district;
- sterile business park;
- futuristic city.

## 6. Deploy Room

Narrative role:
- Chapter 1 boss room;
- Release Manager encounter;
- Deploy 01 completion.

Visual identity:
- release war room inside Mediterranean-modern architecture;
- large central table;
- wall monitors;
- status board;
- warm monitor light against limestone/wood;
- minimal but dramatic staging.

Boss composition:
- Release Manager visible before interaction;
- clean walk from entrance to confrontation point;
- terminal/status screen nearby;
- visual "GO / NO-GO" language can be original UI motifs.

Must not feel like:
- generic house;
- Oak Lab;
- villain lair.

## Palette families

Cagliari exterior daylight:
- limestone cream
- warm beige
- pale terracotta
- deep Mediterranean blue
- turquoise
- olive/palm green
- charcoal shadow

Castello:
- brighter limestone
- amber shadow
- dusty olive
- muted teal sky/sea accents

Deploy:
- limestone / concrete neutral
- muted navy
- warm monitor amber
- restrained release red

Locanda del Molo:
- dark warm wood
- lantern amber
- cream paper
- muted red
- deep navy/charcoal

## Map production quality gate

No location is considered visually approved until:
1. top-down blockout reads correctly without labels;
2. landmark/silhouette identity is recognisable;
3. palette matches this bible;
4. collision path is readable;
5. story anchors remain reachable;
6. warp destinations remain coherent;
7. screenshot at GBA scale is visually distinct from vanilla FireRed;
8. no copyrighted tiles/art have been copied.

Technical transition rule:

- a `requires` field is documentation only and must never be treated as runtime gating;
- a conditioned physical warp must be blocked by a real ObjectEventTemplate whose `flagId` hides it when the story condition is met, or by an equivalently compiled script gate;
- the Chapter 1 preflight must verify every target `warp_id` exists and lands on the declared `target_anchor`.

Tileset production is tracked in `content/cagliari_preview/tileset_art_manifest.json`.
`python scripts/validate_rc_tileset_pipeline.py` validates map coverage, stage order, original-art policy, and metatile-profile compatibility. The current `BOOTSTRAP` result is intentional: blockouts and technical profiles are usable for source integration, but none of the five tileset contracts may be called final. `--require-approved` must stay blocked until every stage has approval evidence and no map uses a `bootstrap_only` metatile profile.

## Naming

Player-facing names for Chapter 1:
- Delivery Hub
- Marina
- Port Link
- Castello
- Deploy District
- Deploy Room
- Locanda del Molo

Internal technical IDs may remain stable for compatibility.
