# Commands & Features — Horizon Wilds

> Written by AI (GLM via OpenCode), directed by kLarss993.
> Target: Horizon v0.2.93 (Minecraft 26.3, DataVersion 5023).
> `wilds_needs` v0.2.0: drink key **J**, new HUD, carried-load gauge.

## Player commands

| Command / key | Runs on | What it does |
|---|---|---|
| **J** (rebindable in Options > Mods) | client (`wilds_needs`) | Same as `/drink`, without opening chat. |
| `/drink` | client (`wilds_needs`) | Starts the water search and answers at once: "Drinking — find the water…". Five checks, 2 ticks apart: the block at your feet, at waist height, then three points up to ~3.2 m along your view (`anchored eyes` + local coordinates). Each check is the game's own `/execute if block <point> minecraft:water` run as you — where it finds water, the game whispers you a marker line the mod hears, your Water bar refills to 100% and the thirst's effects clear (weight slowness stays if you carry a lot). After the fifth miss: "No water in reach — stand in or look at water, then try again." |
| `/needs` | client (`wilds_needs`) | Toggles the HUD panel bottom-left. The choice is saved in mod storage. |
| `/temperature` | server (`wilds_climate`) | Reads the biome you stand in and answers, e.g. `You are in minecraft:plains — mild` / `...frozen_ocean — freezing` / `...desert — hot`. |
| `/warmth` | server (`wilds_climate`) | Scans a box around your feet (±6 in x/z, ±2 in y) and reports the nearest warm block's coordinates, or `Nothing warm within 7 blocks.` |

## HUD panel (`wilds_needs`, bottom-left)

```
Water [================] 100%
Load  [====----] 50%
Comfort 16°C (mild)
Thirsty — find water, look at it, press J   (from 45%)
Packed heavy — your walk slows down         (from Slowness III, ~240+ items)
```

- **Water**: 16-notch bar, blue → sand → red as it empties; the percentage is rounded to whole points.
- **Load**: 8-notch bar, green → red; 400 carried items read 100%. Counts sum over every inventory stack — reading the game's own count report (`Test passed. Count: N`), first ~10 s after a world opens, then every ~30 s.
- **Comfort**: the temperature word line as before.

## Hydration & effects (`wilds_needs`)

- Full water = 100%. Drain ≈ 1 full bar per 1.5 game days at rest (36,000 ticks), ×1.4 walking, ×2.2 sprinting, ×1.3 in the Nether, ×0.9 in the End. Sleeping hours count.
- Thresholds:
  - **≤ 45% — thirsty**: `Hunger`, refreshed every 150 ticks (7.5 s);
  - **≤ 25% — weak**: adds `Weakness`;
  - **≤ 10% — unwell**: adds `Nausea`, every 600 ticks (30 s).
- **Slowness is one shared gauge**: `max(thirst level, weight level)` — hunger-thirst and a heavy pack don't stack, the stronger cause wins. Every 80 items past 0 is one notch (Slowness I–IV at 80/160/240/320+). Effects renew when the gauge changes; each cause clears its own part when it eases (a drink leaves the weight's slowness on).
- Drinking (J or `/drink` at water) instantly refills Water and clears the thirst's effects.

## Carried load (`wilds_needs`)

- The count is the sum of stack sizes across the main inventory (36 slots), the same number `execute if items entity @s container.* *` reports as its `Count:`. The probe runs as you and the game shows its one-line feedback — other chat can't fake the bar.
- Levels: 0–79 none · 80–159 Slowness I · 160–239 II · 240–319 III · 320+ IV. The bar shows count/400, capped at 100%.

## Comfort gauge

- Rough temperature at your feet: **16 °C** overworld baseline; **−6 °C at night** (ticks 13,000–23,000); **−1 °C per 10 blocks** above y=80; **+ up to 3 °C** below y=45 (caves hold warmth); **40 °C in the Nether**, **6 °C in the End**.
- Words: ≤2 freezing · <8 cold · <14 chilly · <24 mild · <34 warm · <44 hot · else scorching.

## Climate notices (`wilds_climate`)

- **Cold biomes** (frozen/snowy/ice/windswept/jagged names): `The cold bites — get near a fire.` if no warm block within reach — at most every 1,500 ticks.
- **Hot biomes** (desert/badlands/savanna/nether/basalt/crimson/warped/soul...): `The heat presses in.` — at most every 1,800 ticks.
- Tells every joining player the pack's rules once.
- Warm blocks: any `fire`, `soul_fire`, `campfire` (lit), `furnace`/`smoker` (lit), `lava`, `magma_block`.

## Blocks, items and recipes (`wilds_kit`)

**Blocks** (all slabs join `minecraft:slabs`, plus proper tool tags and self-drops):
pebblestone · pebblestone_slab · bark_shingles · bark_shingles_slab · wild thatch · thatch_slab

**Items**: tree bark · plant twine · rope · pebble · hide flask · smoked jerky

**Crafting / smelting:**
| Recipe | Result |
|---|---|
| 1 × gravel (shapeless) | 2 × pebble |
| 4 pebbles (2×2) | 1 pebblestone |
| 3 pebblestone (row) | 6 pebblestone slabs |
| any log — *smelters* | 1 tree bark |
| 3 bark (shapeless) | 2 twine |
| 4 twine (2×2) — or the loop `T T / T T /  T ` | rope (1 or 2) |
| hay block + twine (shapeless) | 2 wild thatch |
| 3 thatch (row) | 6 thatch slabs |
| 2×2 bark | 4 bark shingles |
| 3 shingles (row) | 6 shingle slabs |
| leather + 2 twine (shapeless) | 1 hide flask |
| raw beef — *campfire cook* (300 ticks) or *smoker* (100 ticks) | smoked jerky |

## Structures (`wilds_ruins`)

- **Abandoned Camp** — cobble shelters with a hearth and a loot chest (jerky, flasks, bread, rope, torches, rare iron/emerald), plus an open-fire variant. Forests, taiga, plains, meadows. Spacing 52 / separation 30 chunks.
- **Stone Shrine** — lone worn shrine with a rare chest (rarely a damaged bow). Any overworld biome. Spacing 104 / separation 64.
- Only generate in **new/unvisited chunks**.

## Shader pack: Wilds Light (`shaders-src/wilds-light`)

Horizon's own WGSL shader API (schema 1, api 0.1): three stage kinds — `sky`,
`material` (terrain surfaces), `post` (full-screen passes, up to 8) — with
options as WGSL `override`s the game shows under
Options > Horizon Settings > Shader Packs. Six stages:

| Stage | Pass | What it draws |
|---|---|---|
| `sky` | Atmosphere | The Overworld's dome: deeper day blue, dusk warmth around a low sun, a halo behind the moon, storms pulled grey, nights that stay readable, a soft horizon haze. |
| `material` | Light & water | Warm, slowly breathing torch light on block light; water (any translucent terrain) gets crossing waves, fresnel-deepened sky reflection, a sun/moon glint on the small waves, light bands. |
| `post` 1 | Weather & leaves | Underwater warp (slow in lava), rain streaks down the screen, **14 falling leaves** ringed around the camera — projected, depth-tested so walls hide them, faded in and out, dimmed indoors (`eye_light.y ≤ 0.55`), gone in heavy rain or underground. |
| `post` 2 | Glow | A ten-tap halo on the brightest pixels; five times weaker over the sky, a touch stronger at night. |
| `post` 3 | Sunbeams | Seven marching steps toward the sun's screen projection; sky light leaks along the ray, terrain stops it. Dawn/dusk lean it colder; rain or night turn it off. |
| `post` 4 | Colour grade | Shoulder tonemap (0→0, 1→1), S-curve contrast, golden hours, blue nights, grey rain lift, underwater colour, saturation, vignette, film grain. |

**Options (19)**: `dusk_glow`, `sky_haze`, `night_glow`, `torch_warmth`,
`torch_flicker`, `water_depth`, `water_waves`, `water_glint`, `water_bands`,
`rain_streaks`, `leaves`, `underwater_warp`, `glow`, `beams`, `saturation`,
`contrast`, `night_blue`, `vignette`, `grain` — every one fades its effect
to vanilla at (or toward) 0.

**Performance numbers** (from `horizon-shader check`):

```
sky       Atmosphere     269 expressions, 0 texture reads
material  Light & water  341 expressions, 0 texture reads
post      Weather &      632 expressions, 3 texture reads
post      Glow           246 expressions, 3 texture reads
post      Sunbeams       272 expressions, 3 texture reads
post      Colour grade   345 expressions, 2 texture reads
```

against the API's 20 000 expressions / 64 texture reads per stage, and a
`budget.gpu_ms = 1.4` the pack declares. Open F3 in the game to see each
pass's GPU time live.

## Pack tooling

- `tools/gen.py` — one script regenerating every source (textures are drawn in pure Python; structure templates are hand-rolled gzip NBT).
- `cargo horizon-mod test` in `mods-src/wilds-needs` and `mods-src/wilds-climate` — sandbox trial scripts that assert the HUD lines, commands' feedback, join greeting and campfire warmth.
- `install.sh` / `uninstall.sh` — copy/remove the four `.hmod`s and their `mod.<id>:true` lines idempotently.
