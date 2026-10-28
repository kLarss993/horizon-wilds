//! Wilds: Climate — a Horizon server mod (API 0.3, experimental), part of
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
