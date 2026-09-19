# Release Candidate — Intro & Naming Flow v0.2

## Objective

Replace the vanilla FireRed opening flow with a player-facing sequence authored for Release Candidate.

The intended experience must not expose:
- Professor Oak framing;
- Pokémon-world exposition;
- player-facing rival name selection;
- Pallet Town identity;
- "grandson/rival" dialogue structure.

## Target sequence

1. Release Candidate title screen.
2. Fade into a minimal onboarding screen / Delivery workspace.
3. Delivery Lead introduces the project, not the monster world.
4. Player creates their profile/badge.
5. Player enters name.
6. Delivery Lead confirms the badge.
7. Fixed KPI Rival identity is introduced.
8. Arrival transition to Cagliari.
9. First city reveal.
10. Delivery Hub.
11. Starter assignment.

## Dialogue intent

### Delivery Lead opening

Tone:
- competent;
- concise;
- dry;
- slightly tired;
- never tutorial-dump heavy.

Target copy:

"Benvenuto su Release Candidate."

"Il progetto è già partito, le scadenze pure."

"Io coordino la delivery. Ti spiego quello che serve e poi ti lascio lavorare."

### Player name framing

Instead of vanilla "What's your name?":

"Prima di aprirti gli accessi, devo creare il tuo badge."

"Come vuoi comparire nel workspace?"

[NAME INPUT]

"Perfetto, {PLAYER}."

"Badge creato. Accessi quasi pronti."

"Quasi."

### KPI Rival introduction

No player-facing rival name selection.

Target copy:

"Non sarai l'unico nuovo ingresso."

"Quello è il collega che misura qualsiasi cosa possa diventare un grafico."

KPI Rival:

"Solo le cose utili."

"Purtroppo sono quasi tutte."

Delivery Lead:

"Lo chiamano KPI Rival."

"Non chiedermi chi ha iniziato."

### Arrival

"Primo incarico: Cagliari."

"Il Delivery Hub è già operativo."

"Naturalmente nessuno ti ha ancora spiegato dove sia."

Then transition to city reveal.

## Implementation strategy

Preferred:
- preserve the existing underlying name-entry engine;
- replace surrounding text and presentation;
- bypass/remove rival-name choice from the intended path;
- use a fixed authored rival identity;
- redirect post-intro destination into RC arrival / Delivery Hub flow.

Fail-safe:
- if full structural replacement of the vanilla intro is too risky in one step, use a staged migration:
  1. rewrite all visible intro text;
  2. bypass rival name entry;
  3. repoint destination;
  4. replace background/presentation assets;
  5. remove remaining vanilla visual references.

## Name-entry requirements

- player still controls their chosen name;
- existing save compatibility should be retained where possible;
- no hardcoded player name;
- player name must remain available to later dialogue/scripts;
- name-entry keyboard can remain mechanically vanilla in the first v0.2 implementation if surrounding presentation is fully RC-authored.

## Rival identity

Player-facing label:
- KPI Rival

Internal technical name may remain compatible with existing engine data until a safe rename path is verified.

The player must never be asked to name the rival in the final v0.2 flow.

## Visual presentation

Opening palette:
- dark navy;
- warm limestone;
- teal;
- restrained release red.

Possible visual motifs:
- access badge;
- release board;
- project status card;
- Cagliari skyline silhouette;
- sea / limestone transition card.

Avoid:
- Pokédex exposition;
- lab background;
- professor framing;
- creature encyclopedia framing.

## Acceptance criteria

Intro v0.2 passes when:
- new game does not visibly present Oak's original framing;
- player name entry is framed as badge/workspace creation;
- rival name entry is absent;
- KPI Rival identity is fixed;
- transition lands in the RC Cagliari path;
- no obvious Pallet identity appears before gameplay;
- player name persists correctly in save/gameplay;
- new game reaches starter choice without crash.
