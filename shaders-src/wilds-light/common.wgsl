// Helpers shared by the Wilds Light stages.

fn luminance(c: vec3<f32>) -> f32 {
    return dot(c, vec3<f32>(0.2126, 0.7152, 0.0722));
}

// 1 while the sun is up in the Overworld, fading out around the horizon.
fn daylight() -> f32 {
    return select(0.0, smoothstep(-0.06, 0.14, frame.sun_direction.y), frame.dimension == 0);
}

// 1 when the sun sits on the horizon, 0 by a third of the way up.
fn sun_low() -> f32 {
    return 1.0 - smoothstep(0.05, 0.32, abs(frame.sun_direction.y));
}

// 1 deep in the night of the Overworld, 0 by dawn.
fn nightfall() -> f32 {
    return select(0.0, 1.0 - smoothstep(-0.14, 0.10, frame.sun_direction.y), frame.dimension == 0);
}

// The weather as one number: 0 clear, 1 storm.
fn overcast() -> f32 {
    return clamp(frame.rain * 1.25 + frame.thunder * 0.35, 0.0, 1.0);
}

// A pseudorandom 0..1 from a float, the cheap-and-stable way.
fn hash01(s: f32) -> f32 {
    return fract(sin(s * 12.9898) * 43758.5453);
}

// The same from a point.
fn hash12(p: vec2<f32>) -> f32 {
    return fract(sin(dot(p, vec2<f32>(127.1, 311.7))) * 43758.5453);
}
