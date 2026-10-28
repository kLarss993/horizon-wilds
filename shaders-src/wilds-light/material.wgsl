// Wilds Light — how block surfaces are lit.
//
// Vanilla's own is `albedo * tint * vec4(lightmap, 1.0)`. Here the block
// light goes warm and breathes like a flame, and water (any translucent
// terrain: water, stained glass, ice) gets crossing waves, the sky bent
// back over it by fresnel, a sun or moon glint on the small waves, and
// light bands where the reflections fold.
override torch_warmth: f32 = 0.7;
override torch_flicker: f32 = 0.5;
override water_depth: f32 = 0.55;
override water_waves: f32 = 0.6;
override water_glint: f32 = 0.6;
override water_bands: f32 = 0.45;

fn warm_light(lm: vec3<f32>, block: f32, t: f32) -> vec3<f32> {
    // A slow flame breathing, felt only where the torch light reaches.
    let breathe = 1.0 + (sin(t * 10.7) + sin(t * 6.3)) * 0.023 * torch_flicker;
    let warm = mix(vec3<f32>(1.0), vec3<f32>(1.0, 0.80, 0.55), block * torch_warmth * 0.7);
    return lm * warm * mix(1.0, breathe, block);
}

fn material(input: MaterialInput) -> Surface {
    let lm = warm_light(input.lightmap, input.light.x, frame.time);
    var color = input.albedo * input.tint * vec4<f32>(lm, 1.0);

    if input.translucent && frame.dimension == 0 {
        let p = input.position;
        let v = p * (1.0 / sqrt(max(dot(p, p), 0.0001))); // a safe "toward camera"
        let t = frame.time;

        // Two crossing waves and their slope, paced like a light breeze.
        let a = p.x * 1.8 + p.z * 0.9 + t * 2.1;
        let b = p.z * 2.4 - p.x * 0.7 + t * 1.6;
        let h = sin(a) * 0.65 + sin(b) * 0.35;
        let dx = cos(a) * 1.17 - cos(b) * 0.245;
        let dz = cos(a) * 0.585 + cos(b) * 0.84;
        let n = vec3<f32>(
            -dx * water_waves * 0.14,
            1.0,
            -dz * water_waves * 0.14,
        );
        let nx = normalize(n);

        // Fresnel: flat under the eye, mirror at a grazing angle.
        let f = pow(1.0 - max(dot(v, nx), 0.0), 4.0);

        var water = input.albedo.rgb * input.tint.rgb * lm * (1.0 + h * water_waves * 0.16);
        let deep = vec3<f32>(0.03, 0.12, 0.20) * (0.25 + 0.75 * daylight());
        let sky_ref = mix(frame.fog_color, frame.sky_color, 0.55);
        let mirror = clamp(f * 1.9 + 0.12, 0.0, 0.8);
        water = mix(water, mix(deep, sky_ref, clamp(f * 1.35, 0.0, 0.75)), water_depth * mirror);

        // The sun and moon ride the small waves: a tight glint and a rim.
        let lit = mix(frame.moon_direction, frame.sun_direction, daylight());
        let half_v = normalize(v + lit);
        let facing = max(dot(nx, half_v), 0.0);
        let glint_c = mix(vec3<f32>(0.62, 0.72, 0.92), vec3<f32>(1.0, 0.80, 0.48), daylight());
        let glint = (pow(facing, 90.0) + pow(facing, 18.0) * 0.12) * water_glint * (1.0 - frame.rain * 0.55);
        water += glint_c * glint;

        // Light bands where the waves fold the sky's light.
        water += vec3<f32>(0.16, 0.14, 0.10) * pow(abs(sin(a) * sin(b)), 3.0) * daylight() * water_bands;

        color = vec4<f32>(mix(color.rgb, clamp(water, vec3<f32>(0.0), vec3<f32>(1.0)), water_depth), color.a);
    }

    return Surface(color);
}
