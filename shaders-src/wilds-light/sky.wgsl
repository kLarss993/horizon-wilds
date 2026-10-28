// Wilds Light — the sky.
//
// The Overworld's sky along each view ray, starting from vanilla's: a
// deeper blue overhead by day, dusk warmth around a low sun, a pale halo
// behind the moon, storms pulled to grey, and nights that stay readable.
override dusk_glow: f32 = 0.65;
override sky_haze: f32 = 0.5;
override night_glow: f32 = 0.5;

fn sky(input: SkyInput) -> vec4<f32> {
    let d = input.direction;
    var c = input.color.rgb;

    let day = daylight();
    let low = sun_low();
    let night = nightfall();
    let clear = 1.0 - overcast();
    let veil = 1.0 - clear;

    // A deeper blue overhead by day; storms pull the whole dome to grey.
    let zenith = smoothstep(0.12, 0.95, d.y) * day * 0.12;
    c *= vec3<f32>(1.0) - zenith * vec3<f32>(0.30, 0.12, 0.0);
    c = mix(c, vec3<f32>(luminance(c)) * 1.02, veil * 0.55);

    // The sun's halo, and warmth pouring over the horizon at gold hours.
    let toward = max(dot(d, frame.sun_direction), 0.0);
    let halo = pow(toward, 28.0) * 0.55 + pow(toward, 5.0) * 0.10;
    c += vec3<f32>(1.0, 0.72, 0.42) * halo * day * clear;
    let band = 1.0 - smoothstep(0.02, 0.45, abs(d.y));
    c *= mix(vec3<f32>(1.0), vec3<f32>(1.10, 0.95, 0.80), band * low * day * dusk_glow * 0.6);
    c += vec3<f32>(1.0, 0.42, 0.18) * (band * day) * pow(toward, 3.0) * dusk_glow * 0.5;

    // The moon's halo, a whisper of airglow, cooler nights.
    let moon = max(dot(d, frame.moon_direction), 0.0);
    let moon_halo = pow(moon, 22.0) * 0.38 + pow(moon, 5.0) * 0.06;
    c += vec3<f32>(0.60, 0.68, 0.88) * moon_halo * night * night_glow * clear;
    c += vec3<f32>(0.020, 0.028, 0.052) * night * night_glow;
    c *= mix(vec3<f32>(1.0), vec3<f32>(0.92, 0.96, 1.05), night * night_glow * 0.4);

    // A soft band of air on the horizon: the world's breath.
    let haze = exp(-abs(d.y) * 5.5) * 0.15 * sky_haze * (0.2 + 0.8 * day);
    let haze_tint = mix(frame.fog_color, vec3<f32>(1.0, 0.78, 0.55), low * day * 0.55);
    c = mix(c, haze_tint + vec3<f32>(0.03), haze * mix(1.0, 0.25, veil));

    return vec4<f32>(c, input.color.a);
}
