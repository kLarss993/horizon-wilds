//! Wilds: Needs — a Horizon client mod (API 0.1), part of the Horizon
//! Wilds realism pack.
//!
//! Thirst the world can drain, the weight you carry, and a comfort gauge.
//! To drink: stand in water, or look at it while it is close, and press J
//! (or run /drink). The drink check and the carried count are read the way
//! the game itself reads them from commands: a probe runs with the
//! player's rights through `command.run`, and its feedback, which the game
//! always shows the player, the mod hears in chat. Everything else comes
//! from what the game copies to client mods each tick; no game files are
//! touched.
use horizon_mod_sdk::{
    warn, Mod, Registration, chat, command, game, input,
    hud::{self, Corner, Line},
    storage,
};

const FULL: f32 = 100.0;
/// About one full hydration per 1.5 game days at rest: 36000 ticks.
const DRAIN: f32 = 100.0 / 36_000.0;
const EFFECT_PERIOD: u64 = 150;
const NAUSEA_PERIOD: u64 = 600;
const BUCKET: u32 = 5;
/// The load gauge: a probe 10 s into a world, then every half minute;
/// 400 items show the full bar, and every 80 press on a slowness notch.
const PROBE_FIRST: u64 = 200;
const PROBE_PERIOD: u64 = 600;
const LOAD_FULL: u32 = 400;
const LOAD_STEP: u32 = 80;

/// The token a drink probe whispers, so this mod knows its own water test
/// passed and no other chat does.
const MARK: &str = "wilds-drink-mk";
/// One drink attempt walks five probes one at a time, two ticks apart,
/// stopping at the first water: the body's own blocks, then the view.
const STAGES: usize = 5;
const STAGE_TICKS: u64 = 2;

/// What each probe tests, in the view of vanilla's own `/execute`: a body
/// block first, then blocks a step out along the look, which reach the
/// water the player aims at.
fn probe_line(stage: usize) -> String {
    let base = match stage {
        0 => "execute if block ~ ~ ~",                     // the block underfoot
        1 => "execute if block ~ ~1 ~",                    // waist- and neck-deep
        2 => "execute anchored eyes positioned ^ ^ ^0.9 if block ~ ~ ~",
        3 => "execute anchored eyes positioned ^ ^ ^1.8 if block ~ ~ ~",
        _ => "execute anchored eyes positioned ^ ^ ^3.2 if block ~ ~ ~",
    };
    format!("{base} minecraft:water run msg @s {MARK}")
}

/// The plain load probe: how many items the main inventory's stacks sum to,
/// in the count the `if items` feedback reports.
fn load_probe() -> String {
    "execute if items entity @s container.* *".to_string()
}

/// Carried weight: every LOAD_STEP items pressed on is one slowness notch,
/// at most Slowness IV.
fn weight_level(count: u32) -> u32 {
    (count / LOAD_STEP).min(4)
}

/// The load line's color, green when light and red when the walk crawls.
fn weight_color(level: u32) -> u32 {
    match level {
        0 => 0x8BC34A,
        1 => 0xC0CA33,
        2 => 0xFFC857,
        3 => 0xFF9A3C,
        _ => 0xFF6E6E,
    }
}

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

/// A bar: `part` of `whole`, `notches` wide.
fn bar(part: f32, whole: f32, notches: usize) -> String {
    let filled = ((part / whole * notches as f32).round() as i32).clamp(0, notches as i32) as usize;
    format!("[{}{}]", "=".repeat(filled), "-".repeat(notches - filled))
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

/// "Test passed. Count: 35" and its friends, in the languages the game
/// ships (en, ru, uk), the report that carries the load probe's count. The
/// words must both be there and the count read out, so other chat cannot
/// slip a number in.
fn count_from_line(line: &str) -> Option<u32> {
    let pass = line.contains("Test passed")
        || line.contains("Тест пройден")
        || line.contains("Проверка пройдена")
        || line.contains("conditional.pass_count");
    let fail = line.contains("Test failed")
        || line.contains("Тест провален")
        || line.contains("Проверка неуспешна")
        || line.contains("conditional.fail_count");
    if !(pass || fail) {
        return None;
    }
    // The count comes after the words' colon; take the last number on the
    // line, which both the pass and the fail branch carry.
    line.rsplit(|c: char| !c.is_ascii_digit())
        .find(|s| !s.is_empty())
        .and_then(|s| s.parse().ok())
}

/// Effects the thirst side clears when a drink lands (slowness only when
/// no weight still wants it).
fn drank_clears(with_slowness: bool) -> Vec<String> {
    let mut out = vec![
        "effect clear @s minecraft:hunger".to_string(),
        "effect clear @s minecraft:weakness".to_string(),
        "effect clear @s minecraft:nausea".to_string(),
    ];
    if with_slowness {
        out.push("effect clear @s minecraft:slowness".to_string());
    }
    out
}

struct Attempt {
    stage: usize,
    at: u64,
}

struct Needs {
    hydration: f32,
    hud_on: bool,
    last_pos: Option<(f64, f64)>,
    last_day_time: Option<u64>,
    /// Thirst and slowness levels as effects last ran them.
    last_thirst: u32,
    last_slow: u32,
    next_refresh: u64,
    next_nausea: u64,
    /// A drink attempt in flight.
    pending: Option<Attempt>,
    /// The carried count as the game reported it, None before the first.
    count: Option<u32>,
    next_probe: u64,
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
        if let Err(e) = input::register_key("drink", "Drink water", "key.keyboard.j") {
            // The player can rebind it in Options > Mods; a key the game
            // cannot name alone never keeps the mod from loading.
            warn(&format!("registering the drink key failed: {e}"));
        }
        let state = Needs {
            hydration,
            hud_on,
            last_pos: None,
            last_day_time: None,
            last_thirst: 0,
            last_slow: 0,
            next_refresh: 0,
            next_nausea: 0,
            pending: None,
            count: None,
            next_probe: PROBE_FIRST,
        };
        Ok((
            state,
            Registration::new()
                .command("drink")
                .command("needs")
                .on_tick()
                .on_chat(),
        ))
    }

    fn tick(&mut self, tick: u64) {
        let Some(p) = game::get_player() else {
            self.last_day_time = None;
            self.pending = None;
            return;
        };
        let Some(clock) = game::get_clock() else { return };

        // The key's drink, when the player pressed it since the last tick.
        for ev in input::poll() {
            if let input::Event::KeyDown(name) = ev
                && name == "drink"
            {
                self.trigger(tick);
            }
        }

        // The attempt walks its probes; a stage every two ticks, so a
        // drink lands in a couple of hundredths of a second the moment
        // the first check says water.
        if let Some(a) = &self.pending {
            if tick >= a.at + STAGE_TICKS {
                let next = a.stage + 1;
                if next < STAGES {
                    command::run(&probe_line(next));
                    self.pending = Some(Attempt { stage: next, at: tick });
                } else {
                    self.pending = None;
                    chat::show("No water in reach — stand in or look at water, then try again.");
                }
            }
        }

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

        // weariness and weight share one slowness gauge: the strongest
        // cause wins, and hunger or friends stay the thirst's own.
        let lvl = level(self.hydration);
        let w = self.count.map(weight_level).unwrap_or(0);
        let slow = lvl.max(w);
        if tick >= self.next_refresh {
            self.next_refresh = tick + EFFECT_PERIOD;
            let mut lines: Vec<String> = Vec::new();
            if lvl > 0 {
                lines.push("effect give @s minecraft:hunger 15 0 false".to_string());
                if lvl >= 2 {
                    lines.push("effect give @s minecraft:weakness 10 0 false".to_string());
                }
            }
            match slow {
                0 => {} // nothing to carry or thirst away
                n => lines.push(format!(
                    "effect give @s minecraft:slowness 15 {} false",
                    n - 1
                )),
            }
            if !lines.is_empty() {
                command::run_quiet(&lines);
            }
        }
        if lvl >= 3 && tick >= self.next_nausea {
            self.next_nausea = tick + NAUSEA_PERIOD;
            command::run_quiet(&["effect give @s minecraft:nausea 8 0 false".to_string()]);
        }
        // When a cause eased off since the last refresh, clear what it had.
        let mut clears: Vec<String> = Vec::new();
        if lvl == 0 && self.last_thirst > 1 {
            clears.push("effect clear @s minecraft:weakness".to_string());
        }
        if lvl == 0 && self.last_thirst > 0 {
            clears.push("effect clear @s minecraft:hunger".to_string());
        }
        if slow == 0 && self.last_slow > 0 {
            clears.push("effect clear @s minecraft:slowness".to_string());
        }
        if !clears.is_empty() {
            command::run_quiet(&clears);
        }
        self.last_thirst = lvl;
        self.last_slow = slow;

        // the load gauge: the game's own report, first at 10 s, then once
        // every half minute
        if tick >= self.next_probe {
            self.next_probe = tick + PROBE_PERIOD;
            command::run(&load_probe());
        }

        // the panel
        if self.hud_on {
            hud::set_panel(Corner::BottomLeft, &self.lines(&p, clock.day_time));
        }

        // persist in coarse 5-point buckets so writes stay rare
        let bucket = (self.hydration / BUCKET as f32) as u32;
        let saved = storage::get("hydr").and_then(|v| v.first().copied())
            .map(|b| b as u32).unwrap_or(255);
        if bucket != saved {
            let _ = storage::set("hydr", &[(bucket.min(20) * BUCKET) as u8]);
        }
    }

    fn chat(&mut self, text: &str) {
        // A mark of our own: the water's found, drink.
        if text.contains(MARK) {
            if self.pending.take().is_some() {
                self.drank();
                chat::show("You drink deep and feel refreshed.");
            }
            return;
        }
        if let Some(n) = count_from_line(text) {
            self.count = Some(n);
        }
    }

    fn command(&mut self, name: &str, _args: &str) -> Result<Option<String>, String> {
        match name {
            "drink" => {
                if self.pending.is_some() {
                    return Ok(None);
                }
                command::run(&probe_line(0));
                self.pending = Some(Attempt { stage: 0, at: 0 });
                Ok(Some("Drinking — find the water…".to_string()))
            }
            "needs" => {
                self.hud_on = !self.hud_on;
                if self.hud_on {
                    let _ = storage::set("hud_on", &[1]);
                    Ok(Some(
                        "Needs panel shown — hide with /needs, drink with J near water."
                            .to_string(),
                    ))
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
    /// The panel's lines: hydration, the load, comfort, then what wants
    /// attention.
    fn lines(&self, p: &game::Player, day_time: u64) -> Vec<Line> {
        let h = self.hydration;
        let mut lines = vec![Line {
            text: format!("Water {} {:.0}%", bar(h, FULL, 16), h),
            color: hydration_color(h),
        }];
        let count = self.count.unwrap_or(0);
        let shown = (count as f32 / LOAD_FULL as f32 * 100.0).min(100.0);
        let wl = weight_level(count);
        lines.push(Line {
            text: format!("Load {} {:.0}%", bar(shown, 100.0, 8), shown),
            color: weight_color(wl),
        });
        let t = temperature(p, day_time);
        lines.push(Line {
            text: format!("Comfort {}°C ({})", t, comfort_word(t)),
            color: 0xB0BEC5,
        });
        if level(h) > 0 {
            lines.push(Line {
                text: "Thirsty — find water, look at it, press J".to_string(),
                color: 0xFF6E6E,
            });
        }
        if wl >= 3 {
            lines.push(Line {
                text: "Packed heavy — your walk slows down".to_string(),
                color: 0xFF9A3C,
            });
        }
        lines
    }

    fn trigger(&mut self, tick: u64) {
        if self.pending.is_some() {
            return;
        }
        command::run(&probe_line(0));
        self.pending = Some(Attempt { stage: 0, at: tick });
    }

    /// The water was reached: the bars refill and the thirst's effects
    /// rest (the weight's slowness, if any, stays).
    fn drank(&mut self) {
        self.hydration = FULL;
        self.next_refresh = 0;
        self.next_nausea = 0;
        self.last_thirst = 0;
        let heavy = self.count.map(weight_level).unwrap_or(0) > 0;
        command::run_quiet(&drank_clears(!heavy));
        self.last_slow = if heavy { self.last_slow } else { 0 };
    }

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
