# DIAG-REFLECTION1 — env orientation probe + PS2MotionBlur

## ReflectionDebug=1 (diagnostic only)

The static part of the 64x64 env target is replaced by four quadrants and the framebuffer term is
skipped, so every reflective car surface shows which part of the target it samples:

| target | colour | PS2 content there |
|---|---|---|
| top-left | red | ground / below horizon (frame bottom, flipped), left half |
| top-right | yellow | ground, right half |
| bottom-left | blue | sky (frame top), left half |
| bottom-right | cyan | sky, right half |

PS2 reference (`ps2-env-quadrant-reference.png`): every env-layer vertex of the car in the PCSX2
software dump (`...153853`, Turkey, chase camera) drawn in the quadrant its real env UV hits:
left flank blue/red, right flank yellow/cyan, roof and upper rear blue/cyan, lower rear and
bumper red/yellow. A PC screenshot with the same pattern means orientation matches and the
"chrome" difference is content; swapped top/bottom (blue on the bumper, red on the roof) means
the PC samples the target vertically flipped.

Code: `reflection_debug_pattern()` (reflection_pilot.cpp), `MixedReflectionCapture::debug_pattern`
(no framebuffer pass); test in `reflection_capture_tests.cpp` and `ps2_motion_blur_tests.cpp`.

## PS2MotionBlur=<b> (opt-in, default 0)

PS2: display = new*FIX/128 + previous display*(1-FIX/128), FIX = 128 - camera_blur*128 (EE 1b1e70,
per-camera preset +0xbc, interpolated 1b2b90). Chase camera measured FIX 103 -> b = 0.195.
PC (`renderer/ps2_motion_blur.hpp`): last Present stage (after PS2Color and PS2Output): the
previous shown frame is blended over the new one with alpha b (SRCALPHA/INVSRCALPHA, TFACTOR alpha),
then the result is copied into the history. Races only (`live_race_hud_context`, not attract, not
paused); outside, the history is dropped. One value for all cameras (other PS2 cameras not
measured). Session record `ps2_motion_blur` (`blended`, `history_primed`, `outside_race`, reasons).
