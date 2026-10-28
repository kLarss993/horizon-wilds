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

## Pack tooling

- `tools/gen.py` — one script regenerating every source (textures are drawn in pure Python; structure templates are hand-rolled gzip NBT).
- `cargo horizon-mod test` in `mods-src/wilds-needs` and `mods-src/wilds-climate` — sandbox trial scripts that assert the HUD lines, commands' feedback, join greeting and campfire warmth.
- `install.sh` / `uninstall.sh` — copy/remove the four `.hmod`s and their `mod.<id>:true` lines idempotently.
