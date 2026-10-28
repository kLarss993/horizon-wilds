#!/usr/bin/env python3
"""Generates the Horizon Wilds pack sources (v0.1.0).

Everything is generated rather than hand-copied, so the pack can be rebuilt
and tweaked with one command. Layout it produces:

  mods-src/wilds-kit/      content mod (blocks, items, recipes, tags, loot)
  mods-src/wilds-ruins/    content mod (jigsaw structures + chests)
  mods-src/wilds-needs/    client mod crate (thirst + comfort HUD)
  mods-src/wilds-climate/  server mod crate (biome climate + campfire warmth)
  sdk/horizon-mod-sdk/     a vendored copy of the SDK (passed by --sdk)

Run:  python3 gen.py --sdk /path/to/horizon/crates/horizon-mod-sdk
Then build every mod (see the pack README).
"""
import argparse
import gzip
import json
import random
import shutil
import struct
import zlib
from pathlib import Path

NB_END, NB_BYTE, NB_SHORT, NB_INT, NB_LONG, NB_FLOAT, NB_DOUBLE = 0, 1, 2, 3, 4, 5, 6
NB_BYTE_ARR, NB_STR, NB_LIST, NB_COMPOUND, NB_INT_ARR = 7, 8, 9, 10, 11


def jwrite(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def twrite(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ----------------------------------------------------------- PNG writer ----

def write_png(path: Path, w: int, h: int, pixels):
    """pixels: h rows of w (r,g,b,a)."""
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(
            ">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def hx(color, alpha=255):
    color = color.lstrip("#")
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), alpha)


TRANSPARENT = (0, 0, 0, 0)
BASE_PNG = px if (px := [TRANSPARENT]) else None


def canvas(w=16, h=16):
    return [[TRANSPARENT] * w for _ in range(h)]


def put(img, x, y, color):
    if 0 <= x < len(img[0]) and 0 <= y < len(img):
        img[y][x] = color


def fill(img, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(img, x, y, color)


def noise(img, rng, palette):
    for y in range(len(img)):
        for x in range(len(img[0])):
            put(img, x, y, hx(palette[rng.randrange(len(palette))]))


def text(img, rng, palette):
    noise(img, rng, palette)


# ------------------------------------------------------------- textures ----

def tex_pebblestone():
    rng = random.Random(1201)
    base = ["#7f7f7f", "#8a8a8a", "#94948f", "#6f6f6f"]
    img = canvas()
    noise(img, rng, base)
    for (cx, cy, r, col) in [(4, 4, 2, "#a3a39e"), (11, 5, 2, "#b3b3ad"),
                             (8, 10, 2, "#a3a39e"), (13, 12, 1, "#b3b3ad"),
                             (3, 12, 1, "#b3b3ad")]:
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                if x * x + y * y <= r * r:
                    put(img, cx + x, cy + y, hx(col))
    for (x, y) in [(0, 0), (0, 15), (15, 0), (15, 15), (2, 7), (7, 13), (12, 8)]:
        put(img, x, y, hx("#4f4f4f"))
    return img


def tex_pebble_slab():
    img = tex_pebblestone()
    rng = random.Random(1202)
    dark = ["#6d6d6d", "#79796f"]
    for y in range(8, 16):
        for x in range(16):
            put(img, x, y, hx(dark[rng.randrange(2)]))
    for x in range(16):
        put(img, x, 11, hx("#565656"))
        put(img, x, 7, hx("#b9b9b4"))
    return img


def tex_bark():
    rng = random.Random(1301)
    img = canvas()
    noise(img, rng, ["#6a4f30", "#5c452b", "#75593a", "#4f3a23"])
    for x in [2, 6, 11, 14]:
        for y in range(16):
            if rng.random() < 0.7:
                put(img, x, y, hx("#8a6c46"))
    for (x, y) in [(4, 3), (9, 6), (13, 10), (3, 12)]:
        put(img, x, y, hx("#3a2b1a"))
    return img


def tex_bark_shingles():
    rng = random.Random(1302)
    rows = ["#7a5a36", "#6a4f30", "#8a6a45", "#5c452b"]
    img = canvas()
    for y in range(16):
        for x in range(16):
            band = (y // 4 * 5 + x) % 4
            img[y][x] = hx(rows[band] if rng.random() > 0.12 else rows[(band + 1) % 4])
    for y in [3, 7, 11, 15]:
        for x in range(16):
            put(img, x, y, hx("#46331d"))
    for x in [3, 8, 12]:
        for y in range(16):
            if y % 4 != 3:
                put(img, x, y, hx("#59422a"))
    return img


def tex_bark_shingles_slab():
    img = tex_bark_shingles()
    rng = random.Random(1303)
    dark = ["#53402a", "#594630"]
    for y in range(8, 16):
        for x in range(16):
            put(img, x, y, hx(dark[rng.randrange(2)]))
    for x in range(16):
        put(img, x, 11, hx("#3d2c1a"))
        put(img, x, 7, hx("#95755f"))
    return img


def tex_thatch():
    rng = random.Random(1401)
    img = canvas()
    noise(img, rng, ["#c9a34b", "#b8903c", "#d8b559", "#a67c33"])
    for x in range(16):
        for y in range(16):
            if (x + y) % 5 == 0:
                put(img, x, y, hx("#8a5f22"))
            if (x * 3 + y) % 7 == 0:
                put(img, x, y, hx("#e0bf6a"))
    for y in [0, 5, 10, 15]:
        for x in range(16):
            put(img, x, y, hx("#5e411a" if rng.random() < 0.6 else "#7a5323"))
    return img


def tex_thatch_slab():
    img = tex_thatch()
    rng = random.Random(1402)
    dark = ["#8a6730", "#7a5a2e"]
    for y in range(8, 16):
        for x in range(16):
            put(img, x, y, hx(dark[rng.randrange(2)]))
    for x in range(16):
        put(img, x, 11, hx("#5e411a"))
        put(img, x, 7, hx("#e2c273"))
    return img


def tex_pebble_item():
    img = canvas()
    def stone(cx, cy, light):
        for y in range(-2, 3):
            for x in range(-2, 3):
                if abs(x) + abs(y) <= 2:
                    put(img, cx + x, cy + y, hx("#8a8a85"))
        if light:
            for y in range(-1, 2):
                for x in range(0, 2):
                    put(img, cx + x - 1, cy + y - 1, hx("#b6b6b0"))
    stone(5, 6, True)
    stone(11, 5, False)
    stone(8, 11, True)
    return img


def tex_twine():
    img = canvas()
    braid = ["#b98d54", "#7a5a34", "#a2784a"]
    for x in range(16):
        y = (8 + 3 * x) % 16 - 2
        for dy in (-1, 0, 1):
            put(img, x, (y + dy) % 16, hx(braid[(x + dy) % 3]))
    return img


def tex_rope():
    img = canvas()
    cols = ["#8a6a45", "#6a4f30", "#a3815b"]
    for (cx, cy, r) in [(3, 11, 6), (11, 11, 5), (7, 10, 7), (4, 6, 4)]:
        for x in range(16):
            for y in range(16):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if r * r * 0.82 <= d2 <= r * r + 0.6:
                    put(img, x, y, hx(cols[(x + y) % 3]))
    return img


def tex_flask():
    img = canvas()
    leather_a, leather_b = hx("#8a5a34"), hx("#6d4526")
    for y in range(4, 13):
        w = 4 if y < 6 else (5 if y < 10 else 4)
        for x in range(8 - w, 8 + w):
            put(img, x, y, leather_b if (x + y) % 5 == 0 else leather_a)
    fill(img, 7, 1, 9, 3, hx("#b98d5c"))
    put(img, 8, 2, hx("#5c3f22"))
    fill(img, 11, 4, 12, 4, leather_b)
    fill(img, 3, 4, 4, 4, leather_b)
    fill(img, 3, 5, 3, 9, leather_b)
    fill(img, 12, 5, 12, 8, leather_b)
    put(img, 6, 6, hx("#a87346"))
    put(img, 6, 7, hx("#a87346"))
    return img


def tex_jerky():
    img = canvas()
    meat = ["#7a3b2a", "#5c2b1e", "#8a4a33", "#6d3323"]
    for i, (x0, y0) in enumerate([(1, 3), (1, 8), (2, 12)]):
        rng = random.Random(1500 + i)
        lean = meat[rng.randrange(4)]
        for x in range(x0, x0 + 12):
            for y in range(y0, y0 + 3):
                shade = meat[(i + 1) % 4] if (x + y) % 4 == 0 else lean
                put(img, x, y, hx(shade))
        put(img, x0 + 1, y0 + 1, hx("#4a2419"))
        put(img, x0 + 10, y0 + 1, hx("#4a2419"))
    return img


# ------------------------------------------------- content-mod writers -----

CUBE_ALL = "minecraft:block/cube_all"
CUBE_SLAB = "minecraft:block/cube_slab"

def variant(model, y=0):
    v = {"model": model}
    v["y"] = y
    return v


def loot_self(ns, name):
    return {
        "type": "minecraft:block",
        "pools": [{
            "condition": {"type": "minecraft:survives_explosion"},
            "entries": [{"type": "minecraft:item", "name": f"{ns}:{name}"}],
            "rolls": 1,
        }],
        "random_sequence": f"{ns}:blocks/{name}",
    }


def block_state_files(root, ns, block, template, props, models):
    """models: dict variant->model. Writes decl + blockstates + item def + loot."""
    jwrite(root / f"data/{ns}/horizon/block/{block}.json",
           {"template": f"minecraft:{template}"})
    decl = {"template": f"minecraft:{template}"}
    if props:
        decl["properties"] = props
    jwrite(root / f"data/{ns}/horizon/block/{block}.json", decl)
    # "mc:block/x" is shorthand for this ns's own model assets/wilds_kit/models/block/x.json
    repl = lambda m: m.replace("mc:", f"{ns}:")
    variants = {name: variant(repl(model)) for name, model in models.items()}
    jwrite(root / f"assets/{ns}/blockstates/{block}.json", {"variants": variants})
    item_model = models.get("", models.get("type=bottom"))
    jwrite(root / f"assets/{ns}/items/{block}.json",
           {"model": {"type": "minecraft:model", "model": repl(item_model)}})
    jwrite(root / f"data/{ns}/loot_table/blocks/{block}.json", loot_self(ns, block))


def write_item(root, ns, name, template, texture, rarity=None, stack=None):
    decl = {"template": f"minecraft:{template}"}
    if rarity:
        decl["rarity"] = rarity
    if stack:
        decl["max_stack_size"] = stack
    jwrite(root / f"data/{ns}/horizon/item/{name}.json", decl)
    jwrite(root / f"assets/{ns}/models/item/{name}.json",
           {"parent": "minecraft:item/generated",
            "textures": {"layer0": f"{ns}:item/{texture}"}})
    jwrite(root / f"assets/{ns}/items/{name}.json",
           {"model": {"type": "minecraft:model", "model": f"{ns}:item/{name}"}})


def gen_kit(pack_root: Path):
    ns = "wilds_kit"
    root = pack_root / "mods-src" / "wilds-kit"
    if root.exists():
        shutil.rmtree(root)
    twrite(root / "horizon-mod.toml", """id = "wilds_kit"
name = "Wilds: Survival Kit"
version = "0.1.0"
description = "Realism materials: bark, twine, rope, pebblestone, wild thatch, a hide flask and slow-smoked jerky."
authors = ["klarss"]
api = "0.2"
side = "both"
capabilities = ["registries"]
""")

    # ---- blocks
    block_state_files(
        root, ns, "pebblestone", "cobblestone", {"hardness": 1.2},
        {"": "mc:block/pebblestone"})
    block_state_files(
        root, ns, "pebblestone_slab", "cobblestone_slab", {"hardness": 1.2},
        {"type=bottom": "mc:block/pebblestone_slab",
         "type=top": "mc:block/pebblestone_slab_top",
         "type=double": "mc:block/pebblestone"})
    jwrite(root / f"assets/{ns}/models/block/pebblestone.json",
           {"parent": CUBE_ALL, "textures": {"all": f"{ns}:block/pebblestone"}})
    for n in ["pebblestone_slab", "pebblestone_slab_top"]:
        jwrite(root / f"assets/{ns}/models/block/{n}.json",
               {"parent": CUBE_SLAB,
                "textures": {"bottom": f"{ns}:block/pebblestone",
                              "top": f"{ns}:block/pebblestone",
                              "side": f"{ns}:block/pebblestone_slab"}})
    write_png(root / f"assets/{ns}/textures/block/pebblestone.png", 16, 16, tex_pebblestone())
    write_png(root / f"assets/{ns}/textures/block/pebblestone_slab.png", 16, 16, tex_pebble_slab())

    block_state_files(
        root, ns, "bark_shingles", "oak_planks", {"hardness": 0.8},
        {"": "mc:block/bark_shingles"})
    block_state_files(
        root, ns, "bark_shingles_slab", "oak_slab", {"hardness": 0.8},
        {"type=bottom": "mc:block/bark_shingles_slab",
         "type=top": "mc:block/bark_shingles_slab_top",
         "type=double": "mc:block/bark_shingles"})
    jwrite(root / f"assets/{ns}/models/block/bark_shingles.json",
           {"parent": CUBE_ALL, "textures": {"all": f"{ns}:block/bark_shingles"}})
    for n in ["bark_shingles_slab", "bark_shingles_slab_top"]:
        jwrite(root / f"assets/{ns}/models/block/{n}.json",
               {"parent": CUBE_SLAB,
                "textures": {"bottom": f"{ns}:block/bark_shingles",
                              "top": f"{ns}:block/bark_shingles",
                              "side": f"{ns}:block/bark_shingles_slab"}})
    write_png(root / f"assets/{ns}/textures/block/bark_shingles.png", 16, 16, tex_bark_shingles())
    write_png(root / f"assets/{ns}/textures/block/bark_shingles_slab.png", 16, 16, tex_bark_shingles_slab())

    block_state_files(
        root, ns, "thatch", "hay_block",
        {"hardness": 0.5, "sounds": "minecraft:hay_block", "map_color": 10},
        {"": "mc:block/thatch"})
    block_state_files(
        root, ns, "thatch_slab", "oak_slab",
        {"hardness": 0.35, "sounds": "minecraft:hay_block"},
        {"type=bottom": "mc:block/thatch_slab",
         "type=top": "mc:block/thatch_slab_top",
         "type=double": "mc:block/thatch"})
    jwrite(root / f"assets/{ns}/models/block/thatch.json",
           {"parent": CUBE_ALL, "textures": {"all": f"{ns}:block/thatch"}})
    for n in ["thatch_slab", "thatch_slab_top"]:
        jwrite(root / f"assets/{ns}/models/block/{n}.json",
               {"parent": CUBE_SLAB,
                "textures": {"bottom": f"{ns}:block/thatch",
                              "top": f"{ns}:block/thatch",
                              "side": f"{ns}:block/thatch_slab"}})
    write_png(root / f"assets/{ns}/textures/block/thatch.png", 16, 16, tex_thatch())
    write_png(root / f"assets/{ns}/textures/block/thatch_slab.png", 16, 16, tex_thatch_slab())

    # ---- items
    write_item(root, ns, "bark", "paper", "bark")
    write_png(root / f"assets/{ns}/textures/item/bark.png", 16, 16, tex_bark())
    write_item(root, ns, "twine", "string", "twine", stack=32)
    write_png(root / f"assets/{ns}/textures/item/twine.png", 16, 16, tex_twine())
    write_item(root, ns, "rope", "string", "rope")
    write_png(root / f"assets/{ns}/textures/item/rope.png", 16, 16, tex_rope())
    write_item(root, ns, "pebble", "flint", "pebble")
    write_png(root / f"assets/{ns}/textures/item/pebble.png", 16, 16, tex_pebble_item())
    write_item(root, ns, "flask", "honey_bottle", "flask", stack=1)
    write_png(root / f"assets/{ns}/textures/item/flask.png", 16, 16, tex_flask())
    write_item(root, ns, "jerky", "cooked_beef", "jerky")
    write_png(root / f"assets/{ns}/textures/item/jerky.png", 16, 16, tex_jerky())

    # ---- recipes (26.3 data pack shape, as the SDK example writes them)
    R = root / f"data/{ns}/recipe"
    jwrite(R / "pebble_from_gravel.json", {
        "type": "minecraft:crafting_shapeless", "category": "building",
        "ingredients": ["minecraft:gravel"],
        "result": {"count": 2, "id": f"{ns}:pebble"}})
    jwrite(R / "pebblestone.json", {
        "type": "minecraft:crafting_shaped", "category": "building",
        "key": {"P": f"{ns}:pebble"}, "pattern": ["PP", "PP"],
        "result": {"id": f"{ns}:pebblestone"}})
    jwrite(R / "pebblestone_slab.json", {
        "type": "minecraft:crafting_shaped", "category": "building",
        "key": {"P": f"{ns}:pebblestone"}, "pattern": ["PPP"],
        "result": {"count": 6, "id": f"{ns}:pebblestone_slab"}})
    jwrite(R / "thatch.json", {
        "type": "minecraft:crafting_shapeless", "category": "building",
        "ingredients": ["minecraft:hay_block", f"{ns}:twine"],
        "result": {"count": 2, "id": f"{ns}:thatch"}})
    jwrite(R / "thatch_slab.json", {
        "type": "minecraft:crafting_shaped", "category": "building",
        "key": {"T": f"{ns}:thatch"}, "pattern": ["TTT"],
        "result": {"count": 6, "id": f"{ns}:thatch_slab"}})
    jwrite(R / "bark_shingles.json", {
        "type": "minecraft:crafting_shaped", "category": "building",
        "key": {"B": f"{ns}:bark"}, "pattern": ["BB", "BB"],
        "result": {"count": 4, "id": f"{ns}:bark_shingles"}})
    jwrite(R / "bark_shingles_slab.json", {
        "type": "minecraft:crafting_shaped", "category": "building",
        "key": {"S": f"{ns}:bark_shingles"}, "pattern": ["SSS"],
        "result": {"count": 6, "id": f"{ns}:bark_shingles_slab"}})
    jwrite(R / "twine.json", {
        "type": "minecraft:crafting_shapeless", "category": "building",
        "ingredients": [f"{ns}:bark", f"{ns}:bark", f"{ns}:bark"],
        "result": {"count": 2, "id": f"{ns}:twine"}})
    jwrite(R / "rope.json", {
        "type": "minecraft:crafting_shaped", "category": "building",
        "key": {"T": f"{ns}:twine"}, "pattern": ["TT", "TT"],
        "result": {"id": f"{ns}:rope"}})
    jwrite(R / "rope_loop.json", {
        "type": "minecraft:crafting_shaped", "category": "building",
        "key": {"T": f"{ns}:twine"}, "pattern": ["T T", "T T", " T "],
        "result": {"count": 2, "id": f"{ns}:rope"}})
    jwrite(R / "flask.json", {
        "type": "minecraft:crafting_shapeless", "category": "building",
        "ingredients": ["minecraft:leather", f"{ns}:twine", f"{ns}:twine"],
        "result": {"id": f"{ns}:flask"}})
    jwrite(R / "bark_from_log.json", {
        "type": "minecraft:smelting", "category": "misc", "cookingtime": 100,
        "experience": 0.15, "ingredient": "#minecraft:logs",
        "result": {"count": 1, "id": f"{ns}:bark"}})
    jwrite(R / "jerky.json", {
        "type": "minecraft:campfire_cooking", "category": "food",
        "cookingtime": 300, "experience": 0.35,
        "ingredient": "minecraft:beef", "result": {"id": f"{ns}:jerky"}})
    jwrite(R / "jerky_smoked.json", {
        "type": "minecraft:smoking", "category": "food", "cookingtime": 100,
        "experience": 0.35, "ingredient": "minecraft:beef",
        "result": {"id": f"{ns}:jerky"}})

    # ---- tags
    jwrite(root / "data/minecraft/tags/block/mineable/pickaxe.json",
           {"values": [f"{ns}:pebblestone", f"{ns}:pebblestone_slab"]})
    jwrite(root / "data/minecraft/tags/block/mineable/axe.json",
           {"values": [f"{ns}:bark_shingles", f"{ns}:bark_shingles_slab"]})
    jwrite(root / "data/minecraft/tags/block/mineable/hoe.json",
           {"values": [f"{ns}:thatch", f"{ns}:thatch_slab"]})
    jwrite(root / "data/minecraft/tags/block/slabs.json",
           {"values": [f"{ns}:pebblestone_slab", f"{ns}:bark_shingles_slab",
                        f"{ns}:thatch_slab"]})
    jwrite(root / "data/minecraft/tags/block/sword_efficient.json",
           {"values": [f"{ns}:thatch", f"{ns}:thatch_slab"]})

    # ---- lang
    jwrite(root / f"assets/{ns}/lang/en_us.json", {
        f"block.{ns}.pebblestone": "Pebblestone",
        f"block.{ns}.pebblestone_slab": "Pebblestone Slab",
        f"block.{ns}.bark_shingles": "Bark Shingles",
        f"block.{ns}.bark_shingles_slab": "Bark Shingle Slab",
        f"block.{ns}.thatch": "Wild Thatch",
        f"block.{ns}.thatch_slab": "Wild Thatch Slab",
        f"item.{ns}.bark": "Tree Bark",
        f"item.{ns}.twine": "Plant Twine",
        f"item.{ns}.rope": "Rope",
        f"item.{ns}.pebble": "Pebble",
        f"item.{ns}.flask": "Hide Flask",
        f"item.{ns}.jerky": "Smoked Jerky",
    })


# ------------------------------------------------------------ structures ---

def rng_range(lo, hi_):
    return {"type": "minecraft:uniform", "min": lo, "max": hi_}


def loot_entry(name, weight, lo, hi, extra=None):
    fns = [{"function": "minecraft:set_count", "count": rng_range(lo, hi), "add": False}]
    if extra:
        fns.extend(extra)
    return {"type": "minecraft:item", "name": name, "weight": weight, "functions": fns}


class Template:
    """One vanilla-style structure template (single palette)."""

    def __init__(self):
        self.palette: dict = {}
        self.blocks: list = []

    def add(self, x, y, z, name, props=None, nbt=None):
        key = (name, tuple(sorted((props or {}).items())))
        self.palette.setdefault(key, len(self.palette))
        entry = {"pos": [x, y, z], "state": self.palette[key]}
        if nbt:
            entry["nbt"] = nbt
        self.blocks.append(entry)

    def wall(self, x0, y0, z0, x1, y1, z1, solid):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                for x in range(x0, x1 + 1):
                    if x in (x0, x1) or z in (z0, z1):
                        self.add(x, y, z, solid)
                    else:
                        self.add(x, y, z, "minecraft:air")

    def floor(self, x0, y0, z0, x1, z1, solid):
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                self.add(x, y0, z, solid)

    def to_nbt(self, size) -> bytes:
        def nbt_string(s: str) -> bytes:
            b = s.encode("utf-8")
            return struct.pack(">H", len(b)) + b

        def named(name: str, code: int, payload: bytes) -> bytes:
            return bytes((code,)) + nbt_string(name) + payload

        def w_str(value: str) -> bytes:
            return nbt_string(value)

        def w_int(value: int) -> bytes:
            return struct.pack(">i", value)

        def int_array(name, values):
            return named(name, NB_INT_ARR,
                         struct.pack(">i", len(values)) + b"".join(w_int(v) for v in values))

        def compound(entries: bytes) -> bytes:
            return entries + bytes((NB_END,))

        palette_payload = b""
        palette_entries = []
        for (name, props) in self.palette:
            # One palette entry: the Name tag, then Properties when set, all
            # as tags of the entry's own compound (which ends itself).
            payload = w_str(name)
            if props:
                props_payload = b""
                for k, v in props:
                    props_payload += named(k, NB_STR, w_str(v))
                payload += named("Properties", NB_COMPOUND, compound(props_payload))
            palette_entries.append(compound(named("Name", NB_STR, payload)))

        blocks_payload = []
        for b in self.blocks:
            body = int_array("pos", b["pos"]) + named("state", NB_INT, w_int(b["state"]))
            if "nbt" in b:
                nbt_payload = b""
                for k, v in b["nbt"].items():
                    nbt_payload += named(k, NB_STR, w_str(str(v)))
                body += named("nbt", NB_COMPOUND, compound(nbt_payload))
            blocks_payload.append(compound(body))

        def list_compound(name, items):
            return named(name, NB_LIST,
                         bytes((NB_COMPOUND,)) + struct.pack(">i", len(items)) + b"".join(items))

        def list_empty(name):
            return named(name, NB_LIST, bytes((NB_END,)) + struct.pack(">i", 0))

        root = compound(
            int_array("size", size)
            + list_compound("palette", palette_entries)
            + list_compound("blocks", blocks_payload)
            + list_empty("entities")
            + named("DataVersion", NB_INT, w_int(5023)))
        return named("", NB_COMPOUND, root)


def write_template(path: Path, template: Template, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(template.to_nbt(size), mtime=0))


def gen_ruins(pack_root: Path):
    ns = "wilds_ruins"
    root = pack_root / "mods-src" / "wilds-ruins"
    if root.exists():
        shutil.rmtree(root)
    twrite(root / "horizon-mod.toml", """id = "wilds_ruins"
name = "Wilds: Ruins & Camps"
version = "0.1.0"
description = "Abandoned camps and lone stone shrines you can find and loot out in the wilds."
authors = ["klarss"]
api = "0.2"
side = "both"
capabilities = ["registries"]
""")

    S = root / f"data/{ns}/worldgen/structure"
    P = root / f"data/{ns}/worldgen/template_pool"
    T = root / "data" / ns / "structure"
    jwrite(S / "abandoned_camp.json", {
        "type": "minecraft:jigsaw", "biomes": f"#{ns}:has_camp",
        "step": "surface_structures", "spawn_overrides": {},
        "terrain_adaptation": "beard_thin",
        "start_pool": f"{ns}:camp/start", "size": 1,
        "start_height": {"absolute": 0},
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "max_distance_from_center": 80})
    jwrite(S / "stone_shrine.json", {
        "type": "minecraft:jigsaw", "biomes": f"#{ns}:has_shrine",
        "step": "surface_structures", "spawn_overrides": {},
        "terrain_adaptation": "beard_box",
        "start_pool": f"{ns}:shrine/start", "size": 1,
        "start_height": {"absolute": 0},
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "max_distance_from_center": 80})

    def pool(folder, name, elements):
        jwrite(P / name, {"fallback": "minecraft:empty",
                          "elements": [{"weight": w,
                                        "element": {"element_type": "minecraft:single_pool_element",
                                                    "location": f"{ns}:{loc}",
                                                    "projection": proj,
                                                    "processors": "minecraft:empty"}}
                                       for (loc, w, proj) in elements]})
    pool("x", "camp/start.json", [("camp/shelter_a", 2, "terrain_matching"),
                                  ("camp/shelter_b", 2, "terrain_matching"),
                                  ("camp/camp_open", 3, "terrain_matching")])
    pool("x", "shrine/start.json", [("shrine/shrine_a", 1, "terrain_matching")])

    jwrite(root / f"data/{ns}/worldgen/structure_set/camps.json", {
        "structures": [{"structure": f"{ns}:abandoned_camp", "weight": 1}],
        "placement": {"type": "minecraft:random_spread", "salt": 4321971,
                      "spacing": 52, "separation": 30, "spread_type": "linear"}})
    jwrite(root / f"data/{ns}/worldgen/structure_set/shrines.json", {
        "structures": [{"structure": f"{ns}:stone_shrine", "weight": 1}],
        "placement": {"type": "minecraft:random_spread", "salt": 771023,
                      "spacing": 104, "separation": 64, "spread_type": "linear"}})

    jwrite(root / f"data/{ns}/tags/worldgen/biome/has_camp.json", {
        "values": ["#minecraft:is_forest", "#minecraft:is_taiga",
                    "minecraft:plains", "minecraft:meadow"]})
    jwrite(root / f"data/{ns}/tags/worldgen/biome/has_shrine.json", {
        "values": ["#minecraft:is_overworld"]})

    # ---------------- templates
    # shelter_a: 9 x 5 x 8 cobbled hut with a slab roof and a hearth
    t = Template()
    t.wall(0, 0, 0, 8, 2, 7, "minecraft:cobblestone")
    rng = random.Random(77)
    worn = ["minecraft:mossy_cobblestone", "minecraft:cracked_stone_bricks"]
    for z in range(8):
        for y in range(3):
            for x in (0, 8):
                t.add(x, y, z, "minecraft:cobblestone")
    for z in range(8):
        for x in range(9):
            on_face = x in (0, 8) or z in (0, 7)
            if on_face and rng.random() < 0.25:
                t.add(x, rng.randrange(3), z, worn[rng.randrange(2)])
    for z in range(1, 7):
        t.add(2, 3, z, "minecraft:cobblestone_slab", {"type": "top", "waterlogged": "false"})
        t.add(5, 3, z, "minecraft:cobblestone_slab", {"type": "top", "waterlogged": "false"})
    t.add(3, 3, 7, "minecraft:oak_log", {"axis": "x"})
    t.add(4, 3, 7, "minecraft:oak_log", {"axis": "x"})
    t.add(5, 3, 7, "minecraft:oak_log", {"axis": "x"})
    t.add(2, 0, 2, "minecraft:campfire",
          {"facing": "south", "lit": "true", "signal_fire": "false", "waterlogged": "false"})
    t.add(7, 0, 5, "minecraft:hay_block", {"axis": "y"})
    t.add(7, 0, 6, "minecraft:hay_block", {"axis": "y"})
    t.add(6, 0, 6, "minecraft:hay_block", {"axis": "y"})
    t.add(6, 0, 2, "minecraft:chest", {"facing": "south", "waterlogged": "false"},
          {"id": "minecraft:chest", "LootTable": f"{ns}:chests/abandoned_camp"})
    t.add(2, 0, 6, "minecraft:crafting_table")
    for (x, z) in [(0, 0), (8, 0), (0, 7), (8, 7)]:
        t.add(x, 3, z, "minecraft:oak_log", {"axis": "y"})
    for x in range(3, 7):
        t.add(x, 3, 0, "minecraft:oak_log", {"axis": "x"})
    write_template(T / "camp/shelter_a.nbt", t, [9, 5, 8])

    # shelter_b: 8 x 4 x 8 lean-to under a fallen oak trunk
    t = Template()
    t.floor(0, 0, 0, 7, 7, "minecraft:coarse_dirt")
    for x in range(8):
        t.add(x, 2, 3, "minecraft:oak_log", {"axis": "x"})
    t.add(0, 1, 3, "minecraft:cobblestone")
    t.add(7, 1, 3, "minecraft:cobblestone")
    t.add(1, 1, 6, "minecraft:hay_block", {"axis": "y"})
    t.add(2, 1, 6, "minecraft:hay_block", {"axis": "y"})
    t.add(3, 1, 6, "minecraft:hay_block", {"axis": "y"})
    t.add(1, 2, 6, "minecraft:hay_block", {"axis": "y"})
    t.add(2, 2, 6, "minecraft:hay_block", {"axis": "y"})
    t.add(5, 1, 6, "minecraft:campfire",
          {"facing": "south", "lit": "true", "signal_fire": "false", "waterlogged": "false"})
    t.add(1, 1, 1, "minecraft:chest", {"facing": "south", "waterlogged": "false"},
          {"id": "minecraft:chest", "LootTable": f"{ns}:chests/abandoned_camp"})
    t.add(2, 1, 5, "minecraft:gray_wool")
    t.add(3, 1, 5, "minecraft:gray_wool")
    t.add(6, 1, 1, "minecraft:barrel", {"facing": "up", "open": "false"})
    t.add(2, 0, 2, "minecraft:cobweb")
    t.add(3, 0, 1, "minecraft:cobweb")
    t.add(6, 0, 4, "minecraft:cobweb")
    write_template(T / "camp/shelter_b.nbt", t, [8, 4, 8])

    # camp_open: 7 x 3 x 9 open firepit camp with a lantern post
    t = Template()
    t.floor(2, 0, 3, 5, 6, "minecraft:mud")
    t.add(3, 1, 4, "minecraft:campfire",
          {"facing": "south", "lit": "true", "signal_fire": "false", "waterlogged": "false"})
    for (x, z) in [(2, 3), (2, 5), (5, 3), (5, 5), (3, 3), (4, 3), (3, 5), (4, 5)]:
        t.add(x, 0, z, "minecraft:mossy_cobblestone")
    t.add(1, 0, 4, "minecraft:oak_log", {"axis": "y"})
    t.add(6, 0, 5, "minecraft:oak_log", {"axis": "y"})
    t.add(0, 0, 0, "minecraft:oak_log", {"axis": "y"})
    t.add(0, 1, 0, "minecraft:oak_log", {"axis": "y"})
    t.add(0, 2, 0, "minecraft:oak_log", {"axis": "y"})
    t.add(1, 1, 0, "minecraft:barrel", {"facing": "up", "open": "false"})
    t.add(1, 2, 0, "minecraft:hay_block", {"axis": "y"})
    t.add(0, 2, 1, "minecraft:hay_block", {"axis": "y"})
    t.add(0, 3, 0, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    t.add(4, 1, 8, "minecraft:oak_log", {"axis": "y"})
    t.add(3, 1, 8, "minecraft:oak_log", {"axis": "y"})
    t.add(4, 2, 8, "minecraft:oak_fence", {"waterlogged": "false"})
    t.add(3, 2, 8, "minecraft:oak_fence", {"waterlogged": "false"})
    t.add(5, 1, 8, "minecraft:hay_block", {"axis": "y"})
    write_template(T / "camp/camp_open.nbt", t, [7, 3, 9])

    # shrine: 7 x 11 x 7 stone shrine tower with a beacon fire up top
    t = Template()
    rng2 = random.Random(4242)
    worn2 = ["minecraft:cobblestone", "minecraft:mossy_cobblestone",
             "minecraft:cracked_stone_bricks", "minecraft:stone_bricks"]
    t.floor(0, 0, 0, 6, 6, "minecraft:mossy_cobblestone")
    for y in range(1, 7):
        for x in range(7):
            for z in range(7):
                on_face = x in (0, 6) or z in (0, 6)
                if on_face:
                    t.add(x, y, z, worn2[rng2.randrange(4)])
                else:
                    t.add(x, y, z, "minecraft:air")
    t.add(4, 0, 2, "minecraft:mossy_cobblestone")
    for y in range(1, 7):
        t.add(4, y, 2, "minecraft:ladder", {"facing": "south", "waterlogged": "false"})
    for x in range(1, 6):
        for z in range(1, 6):
            t.add(x, 7, z, "minecraft:stone_bricks")
    for (x, z) in [(0, 0), (6, 0), (0, 6), (6, 6)]:
        t.add(x, 7, z, "minecraft:mossy_cobblestone")
    for x in range(7):
        for z in range(7):
            if x == 0 or x == 6 or z == 0 or z == 6:
                t.add(x, 8, z, "minecraft:cobblestone_wall")
    t.add(4, 7, 2, "minecraft:air")
    t.add(3, 8, 3, "minecraft:campfire",
          {"facing": "south", "lit": "true", "signal_fire": "true", "waterlogged": "false"})
    t.add(1, 7, 1, "minecraft:chest", {"facing": "south", "waterlogged": "false"},
          {"id": "minecraft:chest", "LootTable": f"{ns}:chests/stone_shrine"})
    t.add(5, 7, 1, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
    write_template(T / "shrine/shrine_a.nbt", t, [7, 11, 7])

    # ---------------- loot
    L = root / f"data/{ns}/loot_table/chests"

    def chest(name, pools):
        jwrite(L / f"{name}.json", {"type": "minecraft:chest", "pools": pools})

    chest("abandoned_camp", [
        {"rolls": rng_range(2, 3), "entries": [
            loot_entry("wilds_kit:jerky", 15, 1, 4),
            loot_entry("minecraft:bread", 10, 1, 2),
            loot_entry("minecraft:baked_potato", 10, 2, 4),
            loot_entry("wilds_kit:twine", 9, 2, 4),
            loot_entry("wilds_kit:rope", 6, 1, 2),
            loot_entry("minecraft:torch", 9, 2, 6),
            loot_entry("minecraft:stick", 8, 2, 5),
            loot_entry("minecraft:string", 6, 1, 3),
            loot_entry("minecraft:flint", 5, 1, 2),
            loot_entry("minecraft:leather", 5, 1, 3)]},
        {"rolls": rng_range(0, 1), "entries": [
            loot_entry("wilds_kit:flask", 8, 1, 1),
            loot_entry("wilds_kit:bark_shingles", 4, 6, 10),
            loot_entry("wilds_kit:thatch", 4, 8, 12),
            loot_entry("wilds_kit:pebble", 5, 3, 6),
            loot_entry("minecraft:iron_ingot", 3, 1, 2),
            loot_entry("minecraft:emerald", 1, 1, 1)]},
    ])
    chest("stone_shrine", [
        {"rolls": rng_range(2, 3), "entries": [
            loot_entry("minecraft:torch", 9, 2, 5),
            loot_entry("wilds_kit:rope", 7, 1, 3),
            loot_entry("wilds_kit:flask", 6, 1, 1),
            loot_entry("minecraft:iron_ingot", 6, 1, 3),
            loot_entry("minecraft:golden_apple", 2, 1, 1),
            loot_entry("wilds_kit:jerky", 10, 1, 3)]},
        {"rolls": rng_range(0, 1), "entries": [
            loot_entry("minecraft:bow", 3, 1, 1,
                       [{"function": "minecraft:set_damage",
                         "damage": rng_range(0.1, 0.8), "add": False}]),
            loot_entry("wilds_kit:thatch", 4, 8, 12)]},
    ])

    # ---- lang (empty: no own strings to translate)
    jwrite(root / f"assets/{ns}/lang/en_us.json", {})


# ---------------------------------------------------------------- crates ---

NEEDS_TOML = """id = "wilds_needs"
name = "Wilds: Needs"
version = "0.1.0"
description = "Thirst and a comfort gauge in a small HUD panel; /drink and /needs."
authors = ["klarss"]
api = "0.1"
side = "client"
capabilities = ["game-read", "hud", "chat", "command", "storage"]
"""

CLIMATE_TOML = """id = "wilds_climate"
name = "Wilds: Climate"
version = "0.1.0"
description = "Server-side climate: biome warmth notices, campfire checks, /temperature and /warmth."
authors = ["klarss"]
api = "0.3"
side = "server"
capabilities = ["players", "world"]
"""


def crate_cargo(name: str, description: str):
    return (f"""[package]
name = "{name}"
version = "0.1.0"
edition = "2021"
publish = false
license = "MIT"
description = "{description}"

[lib]
crate-type = ["cdylib"]

[dependencies]
horizon-mod-sdk = {{ path = "../../sdk/horizon-mod-sdk" }}

[profile.release]
opt-level = "s"
lto = true
""", )


def write_crate(pack_root: Path, folder: str, name: str, description: str,
                mod_toml: str, lib_rs: str, tests):
    root = pack_root / "mods-src" / folder
    if root.exists():
        shutil.rmtree(root)
    twrite(root / "horizon-mod.toml", mod_toml)
    twrite(root / "Cargo.toml", crate_cargo(name, description)[0])
    (root / "src").mkdir(parents=True, exist_ok=True)
    twrite(root / "src/lib.rs", lib_rs)
    for fname, body in tests:
        twrite(root / "tests" / fname, body)


NEEDS_LIB = r'''//! Wilds: Needs — a Horizon client mod (API 0.1), part of the Horizon
//! Wilds realism pack.
//!
//! Thirst the world can drain, a comfort gauge, and a rule: to drink, stand
//! close to water, look at it, and run /drink. Everything comes from what
//! the game copies to client mods each tick (position, look, clock); the
//! meter is HZD-simple and no game files are touched.
use horizon_mod_sdk::{
    Mod, Registration, command, game,
    hud::{self, Corner, Line},
    storage,
};

const FULL: f32 = 100.0;
/// About one full hydration per 1.5 game days at rest: 36000 ticks.
const DRAIN: f32 = 100.0 / 36_000.0;
const EFFECT_PERIOD: u64 = 150;
const NAUSEA_PERIOD: u64 = 600;
const BUCKET: u32 = 5;

/// Blocks the player may drink from, as `raycast` reports their ids.
const WATER: [&str; 2] = ["minecraft:water", "minecraft:water_cauldron"];

/// Hydration to weariness: 1 thirst, 2 weakness, 3 unwell. 0 is fine.
fn level(h: f32) -> u32 {
    if h <= 10.0 {
        3
    } else if h <= 25.0 {
        2
    } else if h <= 45.0 {
        1
    } else {
        0
    }
}

/// A rough comfort temperature at the player's place, degrees.
fn temperature(p: &game::Player, day_time: u64) -> i32 {
    if p.dimension == "minecraft:the_nether" {
        return 40;
    }
    if p.dimension == "minecraft:the_end" {
        return 6;
    }
    let mut t = 16;
    let tod = (day_time % 24_000) as i32;
    if tod >= 13_000 && tod <= 23_000 {
        t -= 6; // nights bite
    }
    let y = p.y as i32;
    if y > 80 {
        t -= (y - 80) / 10; // the thin air up high
    }
    if y < 45 {
        t += ((45 - y) / 10).min(3); // caves hold their warmth
    }
    t
}

fn comfort_word(t: i32) -> &'static str {
    if t <= 2 {
        "freezing"
    } else if t < 8 {
        "cold"
    } else if t < 14 {
        "chilly"
    } else if t < 24 {
        "mild"
    } else if t < 34 {
        "warm"
    } else if t < 44 {
        "hot"
    } else {
        "scorching"
    }
}

/// A 16-notch water bar.
fn bar(h: f32) -> String {
    let filled = ((h / FULL * 16.0).round() as i32).clamp(0, 16) as usize;
    format!("[{}{}]", "=".repeat(filled), "-".repeat(16 - filled))
}

fn hydration_color(h: f32) -> u32 {
    if h > 45.0 {
        0x6EC6FF // calm water blue
    } else if h > 25.0 {
        0xFFC857 // a warning, sand
    } else {
        0xFF6E6E // dry danger
    }
}

fn thirst_group(clear: bool) -> Vec<String> {
    if clear {
        vec![
            "effect clear @s minecraft:hunger".to_string(),
            "effect clear @s minecraft:slowness".to_string(),
            "effect clear @s minecraft:weakness".to_string(),
            "effect clear @s minecraft:nausea".to_string(),
        ]
    } else {
        vec![]
    }
}

struct Needs {
    hydration: f32,
    hud_on: bool,
    last_pos: Option<(f64, f64)>,
    last_day_time: Option<u64>,
    last_level: u32,
    next_refresh: u64,
    next_nausea: u64,
}

impl Mod for Needs {
    fn init() -> Result<(Self, Registration), String> {
        let hud_on = storage::get("hud_on")
            .map(|v| v.first().copied().unwrap_or(1) == 1)
            .unwrap_or(true);
        let hydration = storage::get("hydr")
            .and_then(|v| v.first().copied())
            .map(|u| u as f32)
            .filter(|h| *h <= FULL)
            .unwrap_or(FULL);
        let state = Needs {
            hydration,
            hud_on,
            last_pos: None,
            last_day_time: None,
            last_level: 0,
            next_refresh: 0,
            next_nausea: 0,
        };
        Ok((
            state,
            Registration::new()
                .command("drink")
                .command("needs")
                .on_tick(),
        ))
    }

    fn tick(&mut self, tick: u64) {
        let Some(p) = game::get_player() else {
            self.last_day_time = None;
            return;
        };
        let Some(clock) = game::get_clock() else { return };

        // drain over the time actually passed (a night's sleep counts too)
        if let Some(last) = self.last_day_time {
            let passed = clock.day_time.saturating_sub(last).min(24_000) as f32;
            let moving = self.moving(&p);
            let dim_factor = match p.dimension.as_str() {
                "minecraft:the_nether" => 1.3,
                "minecraft:the_end" => 0.9,
                _ => 1.0,
            };
            self.hydration = (self.hydration - DRAIN * passed * moving * dim_factor).max(0.0);
        }
        self.last_day_time = Some(clock.day_time);
        self.last_pos = Some((p.x, p.z));

        // weariness: the drier you are, the harder the walk
        let lvl = level(self.hydration);
        if lvl > 0 && tick >= self.next_refresh {
            self.next_refresh = tick + EFFECT_PERIOD;
            let mut lines = vec!["effect give @s minecraft:hunger 15 0 false".to_string(),
                "effect give @s minecraft:slowness 10 0 false".to_string()];
            if lvl >= 2 {
                lines.push("effect give @s minecraft:weakness 10 0 false".to_string());
            }
            command::run_quiet(&lines);
        }
        if lvl >= 3 && tick >= self.next_nausea {
            self.next_nausea = tick + NAUSEA_PERIOD;
            command::run_quiet(&["effect give @s minecraft:nausea 8 0 false".to_string()]);
        }
        if lvl == 0 && self.last_level > 0 {
            command::run_quiet(&thirst_group(true));
        }
        self.last_level = lvl;

        // the panel
        if self.hud_on {
            let t = temperature(&p, clock.day_time);
            let h = self.hydration;
            let mut lines = vec![
                Line {
                    text: format!("Hydration {:.0}% {}", h, bar(h)),
                    color: hydration_color(h),
                },
                Line {
                    text: format!("Comfort {}°C ({})", t, comfort_word(t)),
                    color: 0xB0BEC5,
                },
            ];
            if lvl > 0 {
                lines.push(Line {
                    text: "You are thirsty — find water and /drink".to_string(),
                    color: 0xFF6E6E,
                });
            }
            hud::set_panel(Corner::BottomLeft, &lines);
        }

        // persist in coarse 5-point buckets so writes stay rare
        let bucket = (self.hydration / BUCKET as f32) as u32;
        let saved = storage::get("hydr").and_then(|v| v.first().copied())
            .map(|b| b as u32).unwrap_or(255);
        if bucket != saved {
            let _ = storage::set("hydr", &[(bucket.min(20) * BUCKET) as u8]);
        }
    }

    fn command(&mut self, name: &str, _args: &str) -> Result<Option<String>, String> {
        match name {
            "drink" => {
                match game::raycast(4.5) {
                    Some(hit) if WATER.contains(&hit.block.as_str()) => {
                        self.hydration = FULL;
                        self.next_refresh = 0;
                        self.next_nausea = 0;
                        self.last_level = 0;
                        command::run_quiet(&thirst_group(true));
                        Ok(Some("You drink deep and feel refreshed.".to_string()))
                    }
                    _ => Ok(Some(
                        "No water in reach — stand close and look at a water block.".to_string(),
                    )),
                }
            }
            "needs" => {
                self.hud_on = !self.hud_on;
                if self.hud_on {
                    let _ = storage::set("hud_on", &[1]);
                    Ok(Some("Needs panel shown".to_string()))
                } else {
                    hud::clear();
                    let _ = storage::set("hud_on", &[0]);
                    Ok(Some("Needs panel hidden".to_string()))
                }
            }
            _ => Ok(None),
        }
    }
}

impl Needs {
    /// 1.0 standing still, up to 2.2 sprinting: thirst follows your legs.
    fn moving(&self, p: &game::Player) -> f32 {
        let Some((lx, lz)) = self.last_pos else { return 1.0 };
        let dx = p.x - lx;
        let dz = p.z - lz;
        let speed = (dx * dx + dz * dz).sqrt();
        if speed >= 0.26 {
            2.2 // sprinting
        } else if speed >= 0.09 {
            1.4 // walking
        } else {
            1.0
        }
    }
}

horizon_mod_sdk::export_mod!(Needs);
'''


CLIMATE_LIB = r'''//! Wilds: Climate — a Horizon server mod (API 0.3, experimental), part of
//! the Horizon Wilds realism pack.
//!
//! It runs where the world is simulated (single player's own server thread
//! in particular), so it can see what a client cannot: the biome under each
//! player and the blocks around them. That becomes a light touch of
//! realism: cold and heat notices, /temperature, /warmth, and fire that
//! keeps a person warm.
use horizon_mod_sdk::server::{Args, Player, Registration, ServerMod, players, world};
use std::collections::HashMap;

#[derive(PartialEq, Eq, Clone, Copy)]
enum Comfort {
    Frigid,
    Cold,
    Mild,
    Warm,
    Hot,
}

/// Blocks that keep a person warm, by the state string the game reports.
fn is_warm(state: &str) -> bool {
    let base = state.split('[').next().unwrap_or(state);
    match base {
        "minecraft:lava" | "minecraft:magma_block" | "minecraft:soul_fire"
        | "minecraft:fire" => true,
        "minecraft:campfire" => state.contains("lit=true"),
        "minecraft:furnace" | "minecraft:smoker" => state.contains("lit=true"),
        _ => false,
    }
}

/// How a biome name reads as weather. Vanilla names scale the world.
fn comfort(biome: &str) -> Comfort {
    let b = biome.trim_start_matches("minecraft:");
    if b.contains("frozen") || b.contains("snowy") || b.contains("ice") {
        Comfort::Frigid
    } else if b.contains("cold") || b.contains("windswept") || b.contains("jagged") {
        Comfort::Cold
    } else if b.contains("desert")
        || b.contains("badlands")
        || b.contains("savanna")
        || b.contains("nether")
        || b.contains("basalt")
        || b.contains("crimson")
        || b.contains("warped")
        || b.contains("soul")
    {
        Comfort::Hot
    } else if b.contains("jungle") || b.contains("swamp") || b.contains("mangrove") {
        Comfort::Warm
    } else {
        Comfort::Mild
    }
}

impl Comfort {
    fn word(self) -> &'static str {
        match self {
            Comfort::Frigid => "freezing",
            Comfort::Cold => "chilly",
            Comfort::Mild => "mild",
            Comfort::Warm => "warm",
            Comfort::Hot => "hot",
        }
    }
}

fn feet(p: &Player) -> (i32, i32, i32) {
    (p.x.floor() as i32, p.y.floor() as i32, p.z.floor() as i32)
}

/// The nearest warm block in a box around the player: (pos, distance²).
fn nearest_warm(p: &Player, reach: i32) -> Option<((i32, i32, i32), i64)> {
    let (x, y, z) = feet(p);
    let mut best: Option<((i32, i32, i32), i64)> = None;
    for dy in -2..=2 {
        for dx in -reach..=reach {
            for dz in -reach..=reach {
                let Some(state) = world::get_block(&p.dimension, x + dx, y + dy, z + dz)
                else {
                    continue;
                };
                if is_warm(&state) {
                    let d2 = (dx * dx + dy * dy + dz * dz) as i64;
                    if best.map_or(true, |(_, bd)| d2 < bd) {
                        best = Some(((x + dx, y + dy, z + dz), d2));
                    }
                }
            }
        }
    }
    best
}

struct Climate {
    /// Player id -> (last cold notice tick, last heat notice tick).
    last_word: HashMap<String, (u64, u64)>,
}

impl ServerMod for Climate {
    fn init() -> Result<(Self, Registration), String> {
        Ok((
            Climate {
                last_word: HashMap::new(),
            },
            Registration::new()
                .command_with("temperature", [])
                .command_with("warmth", [])
                .on_joins()
                .on_tick(),
        ))
    }

    fn player_joined(&mut self, player: &Player) {
        players::tell(
            &player.id,
            "Welcome to the Horizon Wilds — the weather bites here: /temperature and /warmth.",
        );
    }

    fn tick(&mut self, tick: u64) {
        if tick % 300 != 0 {
            return;
        }
        for p in players::online() {
            let (x, y, z) = feet(&p);
            let Some(biome) = world::get_biome(&p.dimension, x, y, z) else {
                continue;
            };
            let entry = self
                .last_word
                .entry(p.id.clone())
                .or_insert((0, 0));
            match comfort(&biome) {
                Comfort::Frigid | Comfort::Cold => {
                    if tick >= entry.0 && nearest_warm(&p, 3).is_none() {
                        entry.0 = tick + 1_500;
                        players::tell(&p.id, "The cold bites — get near a fire.");
                    }
                }
                Comfort::Hot => {
                    if tick >= entry.1 {
                        entry.1 = tick + 1_800;
                        players::tell(&p.id, "The heat presses in.");
                    }
                }
                _ => {}
            }
        }
    }

    fn command(
        &mut self,
        player: &Player,
        name: &str,
        _args: &Args,
    ) -> Result<Option<String>, String> {
        match name {
            "temperature" => {
                let (x, y, z) = feet(player);
                let biome = world::get_biome(&player.dimension, x, y, z)
                    .unwrap_or_else(|| "minecraft:unknown".to_string());
                Ok(Some(format!(
                    "You are in {biome} — {}",
                    comfort(&biome).word()
                )))
            }
            "warmth" => {
                if let Some(((bx, by, bz), _)) = nearest_warm(player, 6) {
                    Ok(Some(format!("A warm block is at {bx} {by} {bz}")))
                } else {
                    Ok(Some("Nothing warm within 7 blocks.".to_string()))
                }
            }
            _ => Ok(None),
        }
    }
}

horizon_mod_sdk::export_server_mod!(Climate);
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdk", required=True, help="path to crates/horizon-mod-sdk (v0.2.93)")
    args = ap.parse_args()
    pack_root = Path(__file__).resolve().parent.parent

    vendor = pack_root / "sdk" / "horizon-mod-sdk"
    if vendor.parent.exists():
        shutil.rmtree(vendor.parent)
    shutil.copytree(Path(args.sdk).resolve(), vendor,
                    ignore=shutil.ignore_patterns("examples", "target", "*.hmod"))
    # The vendored crate must stand alone: no workspace inheritance.
    toml = vendor / "Cargo.toml"
    toml.write_text(toml.read_text(encoding="utf-8")
                    .replace("edition.workspace = true", 'edition = "2024"')
                    .replace("license.workspace = true", 'license = "MIT"')
                    .replace("[lints]\nworkspace = true\n", ""), encoding="utf-8")

    gen_kit(pack_root)
    gen_ruins(pack_root)

    write_crate(
        pack_root, "wilds-needs", "wilds-needs", "thirst and comfort for the Horizon Wilds",
        NEEDS_TOML, NEEDS_LIB, [
            ("needs_panel.toml", """# The panel when a world starts, and after an hour of standing still.
[[step]]
ticks = 1
expect.panel = ["Hydration 100% [================]", "Comfort 16°C (mild)"]
expect.corner = "bottom-left"

[[step]]
ticks = 3600
expect.panel = ["Hydration 90% [==============--]", "Comfort 16°C (mild)"]
expect.corner = "bottom-left"
"""),
            ("needs_drink.toml", """# The test game has no blocks, so the raycast finds nothing.
[[step]]
command = "drink"
expect.feedback = "No water in reach — stand close and look at a water block."
"""),
            ("needs_toggle.toml", """# /needs hides the panel and then shows it again.
[[step]]
command = "needs"
expect.feedback = "Needs panel hidden"

[[step]]
ticks = 1
expect.panel = []

[[step]]
command = "needs"
expect.feedback = "Needs panel shown"
"""),
        ])

    write_crate(
        pack_root, "wilds-climate", "wilds-climate", "biome climate and campfire warmth for the Horizon Wilds",
        CLIMATE_TOML, CLIMATE_LIB, [
            ("climate_welcome.toml", """# A joining player is welcomed with the pack's rules.
[[step]]
join = "Alex"
expect.told = ["Alex: Welcome to the Horizon Wilds — the weather bites here: /temperature and /warmth."]
"""),
            ("climate_temperature.toml", """# Plains weather: mild.
[[step]]
join = "Alex"

[[step]]
command = "temperature"
expect.feedback = "You are in minecraft:plains — mild"
"""),
            ("climate_warmth_none.toml", """# Nothing warm is placed: no fire in reach.
[[step]]
join = "Alex"

[[step]]
command = "warmth"
expect.feedback = "Nothing warm within 7 blocks."
"""),
            ("climate_warmth_fire.toml", """# A lit campfire two blocks east of Alex's feet.
[[step]]
join = "Alex"
blocks = [{ x = 2, y = 64, z = 0,
            state = "minecraft:campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]" }]

[[step]]
command = "warmth"
expect.feedback = "A warm block is at 2 64 0"
"""),
        ])

    print("pack sources generated under", pack_root / "mods-src")


if __name__ == "__main__":
    main()
