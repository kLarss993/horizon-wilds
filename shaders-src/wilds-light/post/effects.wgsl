// Wilds Light — the first pass over the picture: the air itself.
//
// 1. What you see through water wobbles (through lava, slower and hotter).
// 2. Rain streaks down the screen, angled a little by the wind.
// 3. Leaves drift past the camera on their way down: small ovals, lit by
//    the day, depth-tested against the world so they hide behind walls,
//    and staying away indoors and in heavy rain.
override rain_streaks: f32 = 0.6;
override leaves: f32 = 0.7;
override underwater_warp: f32 = 0.7;

// The screen-space warp of looking through a fluid.
fn warped(uv: vec2<f32>, in_water: bool) -> vec2<f32> {
    let t = frame.time;
    if in_water {
        let wob = vec2<f32>(
            sin(uv.y * 52.0 + t * 2.2) + sin(uv.y * 23.0 - t * 1.1),
            cos(uv.x * 47.0 + t * 1.8),
        );
        return uv + wob * 0.0045 * underwater_warp;
    }
    return uv;
}

fn post(input: PostInput) -> vec4<f32> {
    var c = input.color.rgb;

    // 1. The water pulses what you see through it.
    if frame.eye_in == 1u && underwater_warp > 0.0 {
        let uv = warped(input.uv, true);
        c = textureSampleLevel(previous, linear_sampler, uv, 0.0).rgb;
    }

    // 2. Rain on the screen.
    if frame.rain > 0.05 && frame.eye_in == 0u && rain_streaks > 0.0 {
        let r = frame.resolution;
        let px = vec2<f32>(input.uv.x * r.x - input.uv.y * r.y * 0.14, input.uv.y * r.y);
        let col = floor(px.x / 3.0);
        let seg = 20.0;
        let slide = px.y - frame.time * r.y * 1.15;
        let row = floor(slide / seg);
        let h = hash12(vec2<f32>(col * 0.37, row * 1.13));
        let dens = 0.34 * min(frame.rain * 1.6, 1.0) * rain_streaks;
        let on = step(1.0 - dens, h);
        let pos = fract(slide / seg);
        let fade = smoothstep(0.0, 0.15, pos) * (1.0 - smoothstep(0.75, 1.0, pos));
        let tint = mix(vec3<f32>(0.55, 0.62, 0.72), vec3<f32>(0.95, 0.97, 1.0), daylight() * 0.7);
        c += tint * (on * fade) * 0.35 * rain_streaks * min(frame.rain * 1.5, 1.0);
    }

    // 3. Leaves: fourteen swatches of autumn drifting around the camera.
    if leaves > 0.0 && frame.eye_in == 0u && frame.dimension == 0
        && frame.rain < 0.75 && frame.eye_light.y > 0.55
    {
        for (var i = 0; i < 14; i++) {
            let seed = f32(i) * 19.7 + 11.0;
            let speed = mix(0.55, 1.1, hash01(seed * 2.3));
            let span = 13.0;
            let phase = hash01(seed) + frame.time * speed / span;
            let fall = fract(phase);
            // Some leaves never spawn for a while: the density knob.
            if hash01(seed * 5.9 + floor(phase) * 17.7) < leaves {
                let swayx = sin(frame.time * (1.1 + hash01(seed * 4.1)) + seed) * mix(0.5, 1.4, hash01(seed * 6.1));
                let swayz = cos(frame.time * 0.9 + seed * 1.7) * mix(0.4, 1.2, hash01(seed * 8.3));
                let ang = hash01(seed * 9.9) * 6.283 + frame.time * 0.028;
                let rad = mix(3.5, 15.0, hash01(seed * 11.3));
                let rel = vec3<f32>(cos(ang) * rad + swayx, 5.0 - fall * span, sin(ang) * rad + swayz);
                let clip = frame.projection * frame.view * vec4<f32>(rel, 1.0);
                if clip.w > 0.4 {
                    let depth = clip.z / clip.w;
                    if depth > 0.0008 {
                        let ndc = clip.xy / clip.w;
                        let center = vec2<f32>(ndc.x * 0.5 + 0.5, 0.5 - ndc.y * 0.5);
                        let px_per_m = frame.resolution.y * frame.projection[1][1] * 0.5 / clip.w;
                        let size = clamp(0.30 * px_per_m, 2.2, 7.5);
                        let rel_px = (input.uv - center) * frame.resolution;
                        if all(abs(rel_px) < vec2<f32>(size * 2.0)) {
                            let spin = hash01(seed * 13.7) * 6.283 + frame.time * (1.0 + hash01(seed * 15.1) * 0.8);
                            let cs = cos(spin);
                            let sn = sin(spin);
                            let r = vec2<f32>(rel_px.x * cs - rel_px.y * sn, rel_px.x * sn + rel_px.y * cs) / size;
                            let shape = 1.0 - smoothstep(0.55, 1.0, dot(r, r * vec2<f32>(1.0, 1.7)));
                            // In front of whatever stands there?
                            if shape > 0.0 && depth > depth_at(center) - 0.004 {
                                let born = smoothstep(0.0, 0.12, fall);
                                let dying = 1.0 - smoothstep(0.82, 1.0, fall);
                                let fresh = hash01(seed * 3.1);
                                let leaf = mix(
                                    vec3<f32>(0.28, 0.46, 0.09),
                                    vec3<f32>(0.72, 0.60, 0.14),
                                    fresh,
                                ) * (0.30 + 0.75 * daylight()) + vec3<f32>(0.02, 0.02, 0.045) * (1.0 - daylight());
                                c = mix(c, leaf, shape * 0.5 * born * dying);
                            }
                        }
                    }
                }
            }
        }
    }

    return vec4<f32>(c, input.color.a);
}
