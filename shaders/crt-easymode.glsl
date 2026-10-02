//!HOOK MAIN
//!BIND HOOKED
//!DESC CRT Scanlines & Vignette for Raspberry Pi & MPV

vec4 hook() {
    vec2 pos = HOOKED_pos;
    vec4 color = HOOKED_tex(pos);

    // Subtle scanline generation
    float scanline = sin(pos.y * HOOKED_size.y * 3.14159265) * 0.12;
    color.rgb -= scanline;

    // Corner vignette / tube curvature shadow
    vec2 uv = pos - vec2(0.5);
    float vignette = clamp(1.0 - dot(uv, uv) * 0.35, 0.0, 1.0);
    color.rgb *= vignette;

    return color;
}
