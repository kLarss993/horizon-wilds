# Horizon Wilds

> **Written by AI.** This pack was generated end-to-end by an AI agent (GLM via OpenCode) — the code, textures, structures, tools and docs. kLarss993 ran the show, tested it against their Horizon install, and ships it as-is, no warranty.

A realism + new-features modpack for [Horizon](https://github.com/horizon-rust/horizon) **v0.2.93** (Minecraft 26.3, DataVersion 5023).

Everything in it is Horizon-native: **no Java jars** (Fabric/Forge mods can't run in Horizon), only `.hmod` content mods and WebAssembly (Rust) code mods, built against Horizon's own mod SDK at the same game tag, and tested with Horizon's own sandbox.

## What's in the pack

| Mod | Side | What it brings |
|---|---|---|
| **Wilds: Survival Kit** (`wilds_kit`) | content (API 0.2, registries) | Survival materials and blocks: **Tree Bark** (smelt any log), **Plant Twine** and **Rope**, **Pebbles** (crush gravel), **Pebblestone** + slab, **Bark Shingles** + slab, **Wild Thatch** + slab, a **Hide Flask** and **Smoked Jerky** (campfire/smoked recipes). Full crafting/smelting recipes, vanilla tool tags (pickaxe/axe/hoe, `slabs`, `sword_efficient`), self-drop loot and proper item models/textures. |
| **Wilds: Ruins & Camps** (`wilds_ruins`) | content (API 0.2, registries) | Two new jigsaw structures: **Abandoned Camps** (shelter variants with loot chests holding jerky, flasks, rope…) in forests/taiga/plains/meadows, and lone **Stone Shrines** (with rare loot incl. a damaged bow) elsewhere. Terrain-matching placement, `beard_thin` adaptation, spacing ~52 chunks. |
| **Wilds: Needs** (`wilds_needs`) | client (API 0.1, `input` experimental) | A bottom-left HUD panel with three gauges: **Water** (hydration drained by the clock — faster in the Nether, faster while moving, sleeping counts), **Load** (how much you carry, asked from the game every ~30 s; every 80 items past 0 adds a Slowness notch, I–IV, merged with the thirst gauge: the strongest wins), and **Comfort** (°C). From 45% "thirst" → 25% "weak" → 10% "unwell": vanilla hunger/slowness/weakness/nausea effects (run as you, see caveats). **Drink with the J key** (rebindable in Options > Mods) or **`/drink`**: stand in water or look at it nearby — the search walks five checks out from your body along your view, and each is the game's own `/execute if block` test. **`/needs`** hides/shows the panel. The gauge and settings persist in storage. |
| **Wilds: Climate** (`wilds_climate`) | server (API 0.3, experimental) | Runs where the world is simulated (e.g. single player's own server thread). Announces **cold bites** (frozen/snowy/windswept biomes, unless a heat source is near: any fire, lit campfire/furnace/smoker, lava, magma) and **heat presses in** (desert/badlands/savanna/nether…), throttled so it isn't spam. **`/temperature`** names your biome's verdict, **`/warmth`** finds the nearest warm block (also knows lava/fire). Greets players joining with the pack's rules. |

Recommended companions from the official registry (installable from the in-game mod browser — these cover more of the "modded feel" without any Java):

- **Recipes** — recipe/uses viewer for items (needs the `ui` experimental flag).
- **Mod Menu** — nicely organized Options > Mods page.
- **Blockscope** / **Lookat** — technical yet realistic block info.
- **Vein Miner** — QoL for chopping.
- **FPS Overlay** + **Keystrokes** — informational overlays.
- You already have **Minimap** and **Zoom**.

## Install

From the pack folder:

```sh
./install.sh
```

- copies `wilds_kit.hmod`, `wilds_ruins.hmod`, `wilds_needs.hmod`, `wilds_climate.hmod` from `mods-src/*/target/horizon-mod/` into your game folder's `horizon-mods/` (default `~/.local/share/horizon`; override with `HORIZON_DIR=/path/to/game ./install.sh`),
- appends `mod.wilds_kit:true` (etc.) to `horizon-mods.txt` if not already there, leaving every other line exactly as it is, with a `.bak` backup.

Then start the game. New blocks/items/recipes appear immediately; **new structures generate in NEW or not-yet-visited chunks only** (worldgen is planned per chunk). `/temperature` should reply at once in an opened world.

## Uninstall

```sh
./uninstall.sh
```

Removes the four `.hmod` files, their `horizon-mods.txt` toggle lines and the `wilds_needs` storage folder. Anything placed/generated in worlds stays (it's just blocks in the save).

## Commands

| Command / key | Runs on | Effect |
|---|---|---|
| **J** (keybind) or `/drink` | client | Starts the water search: five checks, 2 ticks apart — your feet block, waist height, then three points up ~1.8 m along your view. First hit refills Water to 100% (weight slowness stays if you're packed heavy); after the fifth miss: "No water in reach — stand in or look at water, then try again." |
| `/needs` | client | Toggles the HUD panel (choice persists) |
| `/temperature` | server | Current biome's comfort verdict |
| `/warmth` | server | Nearest warm block within ~7 blocks, or its absence |

## Honest caveats

- **Needs runs vanilla commands as you.** In single player with Allow Commands on (you're OP) everything works. In a world with **Allow Commands off** the thirst's `/effect` doses and the two probes (`/execute if block` for water, `/execute if items … Count:` for load) are refused: Drink replies "no water", Load stays at 0% — degraded but silent, nothing crashes.
- **`wilds_climate` is an API-0.3 *experimental* server mod** (matches Horizon docs). On plain vanilla 26.3 servers it is inert; every other piece of the pack still works.
- **Structures are new-chunk-only.** A world fully explored before installing gains nothing; regenerate or travel.
- The hydration/comfort gauges are deliberately simple. Seasons didn't make it into this pack — the "Tough As Nails"-style temperature stays at the cozy-biome level.

## Rebuild from source (optional)

All sources are generated by one script for reproducibility, and the SDK is vendored from your game's tag:

```sh
python3 tools/gen.py --sdk /path/to/horizon/crates/horizon-mod-sdk   # needs a v0.2.93 checkout
# then, with a Rust wasm32-unknown-unknown toolchain:
cd mods-src/wilds-kit      && cargo horizon-mod build
cd mods-src/wilds-ruins    && cargo horizon-mod build
cd mods-src/wilds-needs    && cargo horizon-mod build && cargo horizon-mod test
cd mods-src/wilds-climate  && cargo horizon-mod build && cargo horizon-mod test
```

Shipped files came from exactly this flow; the four `.hmod` files under `mods-src/*/target/horizon-mod/` are the same ones `install.sh` copies. Per-mod checks (`cargo horizon-mod check <built .hmod>`) and Horizon's sandbox trial runs all pass.

## Java mods → Horizon-native coverage

The pack exists because unported Java mods can't be loaded by Horizon. Mapping of the "realism pack" wants:

| Wanted (Java) | Horizon-native here |
|---|---|
| Thirst Was Taken, Tough As Nails (thirst/temperature) | `wilds_needs` (hydration + effects + drink key J) · `wilds_climate` (biome cold/heat, fires warm) |
| Inventory weight (Torcherino "Packing Tape"-style carry limits) | `wilds_needs` Load gauge: items counted via the game's own `if items` report; every 80 carried adds a Slowness notch |
| Serene Seasons (seasons/weather) | not reproduced — out of scope; biome-level climate only |
| YUNG's Structures, Towns & Towers (small wilds ruins) | `wilds_ruins` (camps + shrines, loot chests) |
| Farmer's Delight-ish campfire food | `wilds_kit` (jerky: campfire cooking + smoking, honey-flask "drink", bark → twine → rope → shingles/thatch chain) |
| AppleSkin (food details) | registry **Recipes** viewer covers the reads; no overlay equivalent yet |
| Survivalist-style early crafting | `wilds_kit` pebble/bark material chain |
