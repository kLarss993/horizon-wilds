# Wilds Light

A shader pack for Horizon's own shader API: made for the Horizon Wilds pack,
and good on any world. Realism where it is cheap: light that feels hand-lit,
water that remembers the sky, and leaves drifting past the camera on their
way down. Deliberately light — four small passes and one sky, tuned to add
about a millisecond on the GPU.

## What it does

| Stage / pass | What you see |
|---|---|
| **Atmosphere** (sky) | A deeper blue overhead, dusk warmth around a low sun, a pale halo behind the moon, greyer storms, nights that stay readable. |
| **Light & water** (material) | Torch-lit block surfaces go warm and breathe (a slow flicker); water gets crossing waves, the sky bent back over it by fresnel, a sun/moon glint on the small waves and light bands where the reflections fold. Stained glass and ice take the same sheen, softer. |
| **Weather & leaves** (post 1) | Rain streaks down the screen, leaves fall past the camera (depth-tested, so they vanish behind walls), and what you see through water gently wobbles. |
| **Glow** (post 2) | A soft halo around the brightest things — the sun, lava, torches at night. |
| **Sunbeams** (post 3) | Light rays reaching out from the sun along the screen, hidden where terrain stands; stronger at dawn and dusk. |
| **Colour grade** (post 4) | A gentle tonemap, golden hours, blue nights, grey rain days, underwater colour, a light vignette and a flicker of film grain. |

## Options

Every knob lives on Options > Horizon Settings > Shader Packs > settings.
Turn **Leaves** down if you dislike the drifting leaves; every other effect
also fades to vanilla at 0.

## Installing

Put this folder (or the built `wilds_light-<version>.hshader`) into the game
folder's `shaderpacks/`, then pick **Wilds Light** on
Options > Horizon Settings > Shader Packs. The game checks the pack first;
failed packs are refused with the reason in chat.

## Performance

- 4 post passes (under water tints and distortion at 8 taps each), 1 sky
  function, 1 material function.
- Budget: `gpu_ms = 1.4`. Per-stage cost is printed by
  `horizon-shader check shaders-src/wilds-light`.
- Open F3 in the game to see each pass's GPU time live (the overlay measures
  while it shows).

## Notes

- The leaves are the pack's signature: small ovals drifting down a ring
  around the camera, depth-tested against the world so they hide behind
  walls, and gone indoors or in heavy rain. They are stylized everywhere,
  not tied to a biome — turn **Leaves** down if you find them too much.
- Requires a game with the Shader Packs page (Options > Horizon Settings).

Written by AI (GLM via OpenCode), directed by kLarss993. MIT.
