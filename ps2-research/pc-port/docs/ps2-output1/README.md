# PS2-OUTPUT1 — PS2 display filter (opt-in `PS2Output=1`)

Evidence: `ps2-research/output1/findings.md` (EE display object `0x42a950`: init `2f4400`, buffers
`2f01c8`, per-frame kick `2f5528`; offline simulator `ps2-research/output1/ps2_output_sim.py`).

PS2: the scene is drawn into a 640x512 PSMCT16 buffer; every frame a SPRITE with bilinear TEX1 copies
it to a 512x256 PSMCT32 field buffer, ALPHA (Cs-Cd)*FIX+Cd (FIX = PS2/MotionBlur, 128 = plain copy);
the odd-frame packet adds XYOFFSET +8/16 = half a display line = one source row. Woven over two fields,
every output line averages two adjacent source rows; every column is a 640->512 bilinear resample.
There is no other output stage (no bloom, no gamma/colour curve).

PC (`renderer/ps2_output.hpp`), once per Present, fixed function, whole frame incl. HUD:

| pass | target | sample |
|---|---|---|
| copy | private copy of the backbuffer (CopyRects; MSAA only as same-size resolve) | — |
| 0 (only if > 1280x1024) | W/2 x H/2 | bilinear, avoids 3:1 bilinear aliasing |
| 1 | 640x512 (PS2 draw buffer size) | bilinear |
| 2 | 512x512 woven fields | bilinear, **+0.5 source row**: row r = (src r + src r+1)/2, 640->512 columns |
| 3 | backbuffer | bilinear upscale (TV/emulator stretch) |

State: `ReflectionCaptureTransaction` (render target, viewport, stream and 42 states captured and
restored); pending restores join `native_states_pending()` / `repair_reflection()`. Targets are DEFAULT
pool and released in `ps2_port_reset_begin` via `present_before_reset()`. Order with PS2Color: tone
curve first, then this filter. Session record `ps2_output` once per outcome (`filtered` or reason).

Not reproduced: PSMCT16 quantisation/dither of the draw buffer, PS2/MotionBlur trails (showroom
only while the camera swings), interlace flicker (both fields are shown at once).

Patch 0001: the Present hook now asks `present_pass_requested()`, reset calls
`present_before_reset()`, new test `ps2_output_contracts`; lock updated.
