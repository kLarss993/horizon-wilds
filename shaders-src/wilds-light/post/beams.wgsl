// Wilds Light — the sun's light reaching down the screen. Seven short
// marching steps toward the sun's place on the screen: the sky's own light
// leaks along the way, and where terrain stands it stops. Dawn and dusk
// lean it out; rain and night shut it off.
override beams: f32 = 0.55;

fn ray_step(p: vec2<f32>) -> f32 {
    if depth_at(p) == 0.0 {
        let c = textureSampleLevel(previous, linear_sampler, p, 0.0).rgb;
        return luminance(c);
    }
    return 0.0;
}

fn post(input: PostInput) -> vec4<f32> {
    let strength = beams * daylight() * (1.0 - frame.rain * 0.8);
    if strength <= 0.0 {
        return input.color;
    }
    // Where the sun sits: 100 m along its direction, projected.
    let clip = frame.projection * frame.view * vec4<f32>(frame.sun_direction * 100.0, 1.0);
    if clip.w <= 0.2 {
        return input.color; // the sun is behind the camera
    }
    let ndc = clip.xy / clip.w;
    let sun_uv = vec2<f32>(ndc.x * 0.5 + 0.5, 0.5 - ndc.y * 0.5);
    let to_sun = (sun_uv - input.uv) * 0.7;
    var sum = 0.0;
    for (var i = 1; i <= 7; i++) {
        sum += ray_step(input.uv + to_sun * f32(i) / 7.0);
    }
    let fall = exp(-length(to_sun) * 5.0);
    let tint = mix(vec3<f32>(1.0, 0.85, 0.60), vec3<f32>(1.0, 0.72, 0.45), sun_low());
    return vec4<f32>(input.color.rgb + sum * 0.154 * fall * strength * tint, input.color.a);
}
