# VEHICLE-LIGHT2: PS2 sampling of the framebuffer reflection term

LIGHT1 runtime (user, BFGoodrich car vs PS2): base clearly darker and closer, but the body
reflection still looks different: on PC a high-frequency, mottled sky/ground pattern; on PS2 a
smooth, broad metallic sheen.

## Checked and already matching (no change)

- Target weights: PS2 builds the 64x64 target as `.625*static` (ALPHA …a8, FIX 80) +
  `.375*flipped frame` (ALPHA …68, FIX 48). The PC static GXI is pre-weighted by 80/128 at upload
  (`reflection_pilot.cpp`) and the frame pass uses colour 0x60 (= .376). A first attempt to scale
  the static pass again was reverted (it would have applied .625 twice).
- Environment coordinates: PS2 `UV = (.5,.5) + n·(.5·M[*,0], −.5·M[*,1])` with `M = O·V`
  (view-space normal, no reflection vector), the same normal mapping the port uses.

## Changed

PS2 shrinks a 640x448 frame into the 64x64 target (≈10:1 per axis, bilinear, no mips). The PC
shrank the full backbuffer (e.g. 1920x1080, ≈30:1) in one bilinear pass, so each target texel
sampled a nearly random frame pixel: aliasing, a mottled pattern and frame-to-frame shimmer.
The capture now first draws the frame copy into a 640x448 render target (the PS2 frame size),
then mixes 64x64 from that intermediate. This reproduces the PS2 sampling ratio; GS 16-bit
quantization and exact PS2 filtering are still approximations.

Tests: capture mock (three private draws per capture: 640x448 then 64x64 static/frame,
resource release incl. the intermediate, allocation-failure paths), Python contract updated.

## Next candidates

- Glass: PS2 mode20 static WINDSCREEN-REFLECT at Cs*.75 + Cd, depth masked; the port's
  weighted glass layers (modes 21/5, TFACTOR .75) need a direct comparison (UFO dome).
- Primary fog (PS2 FGE=1) on the body layer.
- Live PS2 capture (PCSX2) for a pixel-level comparison; no pixel parity claimed.
