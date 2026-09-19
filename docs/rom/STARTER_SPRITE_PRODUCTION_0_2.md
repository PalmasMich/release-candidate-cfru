# Release Candidate — Starter Sprite Production Contract v0.2

Approved visual direction:
- Tartrek: limestone trail scout, Grass/Ground.
- Frobyte: storm hopper, Water/Electric.
- Emberfox: ember-shadow fox, Fire/Dark.

The approved concept art is the visual north star. In-game sprites must simplify it without changing identity.

## Global sprite rules

Target:
- FireRed/CFRU-compatible battle presentation;
- crisp silhouette at native scale;
- original art only;
- no direct conversion of concept art without manual cleanup.

Required deliverables per starter:
1. front battle sprite;
2. back battle sprite;
3. menu/icon sprite;
4. normal palette;
5. shiny palette;
6. front coordinate values;
7. back coordinate values;
8. thumbnail silhouette proof.

## Tartrek

Must preserve:
- young land-turtle proportions;
- limestone/earth shell;
- explorer strap motif;
- olive/sage body;
- calm expression.

Simplify:
- shell vegetation to 2–3 major clusters;
- rock detail to large readable planes;
- accessory detail to one main strap + medallion/fastener shape.

Do not:
- turn the shell into a generic backpack;
- overfill with tiny plants;
- make it resemble a tank.

## Frobyte

Must preserve:
- compact frog body;
- strong rear legs;
- blue/cyan body;
- yellow electric accents;
- charged throat-sac identity.

Simplify:
- water droplets into one or two accent pixels/shapes;
- dorsal fins/markings into a clean silhouette;
- electric motif into large lightning shapes.

Do not:
- make it robotic;
- use excessive glow effects that disappear at native scale.

## Emberfox

Must preserve:
- slender fox silhouette;
- large ears;
- charcoal + burnt-orange palette;
- controlled flame-tail identity;
- confident expression.

Simplify:
- flame tail into one primary mass;
- facial markings into 1–2 strong shapes;
- shoulder/leg dark accents into large clusters.

Do not:
- make it demonic;
- use many detached flame particles;
- make first-stage proportions too adult.

## Approval gate

A sprite is not production-ready unless:
- front and back read as the same creature;
- silhouette remains recognisable at 1x;
- palette count is within engine limits;
- icon matches head shape;
- concept identity survives simplification;
- sprite is reviewed before DPE integration.

## Integration rule

Existing placeholder sprite assets are not considered approved art and may be replaced completely while keeping species IDs stable:
- Tartrek 0x050E
- Frobyte 0x050F
- Emberfox 0x0510
- Mistrillo 0x0511

No save-facing species IDs may change during this art replacement.
