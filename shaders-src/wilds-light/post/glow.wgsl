// Wilds Light — the soft halo around the brightest things. Ten taps on two
// rings, scaled with the picture's height. The daytime sky is bright too,
// so it glows a fifth as much.
override glow: f32 = 0.5;

fn tap(uv: vec2<f32>) -> vec3<f32> {
    let c = textureSampleLevel(previous, linear_sampler, uv, 0.0).rgb;
    let in_sky = depth_at(uv) == 0.0;
    return c * smoothstep(0.72, 1.0, luminance(c)) * select(1.0, 0.2, in_sky);
}

fn post(input: PostInput) -> vec4<f32> {
    if glow <= 0.0 {
        return input.color;
    }
    let unit = frame.resolution.y * 0.0075;
    let inv = 1.0 / frame.resolution;
    var sum = vec3<f32>(0.0);
    for (var i = 0; i < 10; i++) {
        let ang = f32(i) * 0.6283;
        let rad = select(2.0, 5.2, (i & 1) == 1) * unit;
        sum += tap(input.uv + vec2<f32>(cos(ang), sin(ang)) * rad * inv);
    }
    // The same halo reads stronger in the dark, where it belongs.
    return vec4<f32>(input.color.rgb + sum * glow * (0.85 + 0.3 * nightfall()) * 0.22, input.color.a);
}
