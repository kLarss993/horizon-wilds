// Wilds Light — the last pass, onto the screen. A gentle tonemap, golden
// hours and blue nights, grey rain days, underwater colour, then
// saturation, a light vignette and a flicker of grain.
override saturation: f32 = 1.12;
override contrast: f32 = 0.3;
override night_blue: f32 = 0.35;
override vignette: f32 = 0.35;
override grain: f32 = 0.1;

fn post(input: PostInput) -> vec4<f32> {
    var c = input.color.rgb;

    // A shoulder that keeps 0 and 1 in place and lifts the middle a hair.
    c = c / (1.0 + 0.25 * c) * 1.25;

    // A little more punch.
    c = mix(c, c * c * (3.0 - 2.0 * c), contrast);

    // Time and weather grade the light.
    let day = daylight();
    let low = sun_low();
    let night = nightfall();
    let golden = low * day * (1.0 - frame.rain * 0.7);
    c *= mix(vec3<f32>(1.0), vec3<f32>(1.10, 0.97, 0.84), golden * 0.8);
    c *= mix(vec3<f32>(1.0), vec3<f32>(0.90, 0.95, 1.10), night * night_blue * 0.6);
    let wet = clamp(frame.rain * 1.3, 0.0, 1.0);
    c = mix(c, vec3<f32>(luminance(c)) * 0.96 + 0.035, wet * 0.35);

    // The water you stand in, and the lava's bake.
    if frame.eye_in == 1u {
        c *= vec3<f32>(0.55, 0.75, 0.86);
    } else if frame.eye_in == 2u {
        c *= vec3<f32>(1.15, 0.65, 0.30);
    }

    c = mix(vec3<f32>(luminance(c)), c, saturation);
    let aspect = frame.resolution.x / frame.resolution.y;
    let d = length((input.uv - 0.5) * vec2<f32>(aspect, 1.0)) / length(vec2<f32>(aspect, 1.0) * 0.5);
    c *= 1.0 - smoothstep(0.55, 1.12, d) * vignette * 0.42;
    let n = hash12(vec2<f32>(
        input.uv.x * frame.resolution.x,
        input.uv.y * frame.resolution.y + frame.time * 111.0,
    )) - 0.5;
    c += n * grain * 0.05;
    return vec4<f32>(clamp(c, vec3<f32>(0.0), vec3<f32>(1.0)), input.color.a);
}
