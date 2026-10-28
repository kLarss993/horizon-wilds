//! Wilds: Needs — a Horizon client mod (API 0.1), part of the Horizon
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
