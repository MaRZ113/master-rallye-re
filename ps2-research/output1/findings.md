# PS2-OUTPUT1 — where the soft PS2 picture comes from

Read-only EE research (SLES_509.06, Ghidra 12.1.4 + EER, Rabbitizer byte checks). Trigger: the user
sees a soft "bloom" on PS2 (strongest in the frontend Vehicle Select), while PC with PS2Color=1 looks
darker. Evidence labels as in binary-diff1: NEW-DECOMP = Ghidra pseudocode, NEW-BYTES = original bytes.

## 1. The 3D frame is never displayed directly (NEW-DECOMP, NEW-BYTES)

Display object `0x42a950`, init `2f4400(obj, 3)` (`3` = PAL), buffer setup `2f01c8`, per-frame kick
`2f5528`:

| | value | source |
|---|---|---|
| draw buffer | **640 x 512, PSMCT16** (Z PSMZ16), `0x294c/0x2950`, psm table `0x296c[7]=2` | `2f4400`, `2f01c8 -> 3c8820` |
| display buffer | **512 x 256 per field, PSMCT32**, `0x2940/0x2944`, psm `0x2968[7]=0`, interlaced field mode | `2f4400`, `2f01c8 -> 3c76f0/3c7890` |
| copy | GIF A+D packet per frame: DTHE 0, PABE 0, XYOFFSET, SCISSOR, FRAME=display, TEX0=draw buffer TFX DECAL TCC0, **TEX1 MMAG/MMIN LINEAR**, CLAMP, TEST(colour only), **ALPHA 0x64 = (Cs-Cd)*FIX+Cd**, SPRITE UV (0,0)-(640,512) -> 512x256 | template `2f4400` (obj+0x23f0/+0x24f0) |
| field alternation | packet 2 = packet 1 with Y +8/16 (half display line); `2f5528` kicks list `0x42d2d0` on even, `0x42d2e8` on odd frames | `2f01c8`, `2f5528` |
| FIX | default 0x80 (no trail); `PS2/MotionBlur` broker value -> `2ef870` rewrites both packets | `32f988`, `2ef870` |

So every frame is: render at 640x512 in 16 bit -> **bilinear resample 640->512 horizontally and
2:1 vertically with alternating half-line offset** -> 512x256 field -> TV. That is a low-pass
filter over the whole picture (HUD and menus included, they are drawn into the same buffer).
Bright edges bleed into dark neighbours; this is the "soft bloom". There is **no** bloom/glow
pass, no gamma/tone curve and no colour matrix in the output path (`AnalogGamma` is a
controller setting next to `AnalogBrakeFallRate`; `carglow` is a glassy car shader, mode 20/21 with
windscreen-reflect/rendertarget64, 0.3).

CT16 detail: RGB is quantised to 5 bits and the GS expands it by `<<3`, so white tops at 248.

## 2. MotionBlur is a transient, not the constant softness

* Race (`32f988`): FIX = broker `PS2/MotionBlur` if present.
* Showroom camera `291580`: `b = sqrt(|cam+0x54 - target|) * 0.95` (camera angle still to travel),
  `MotionBlur = (1 - b) * 128` — a trail only while the camera swings to the next car. A static
  Vehicle Select uses FIX 128 (no trail).

## 3. Frontend car

Same body lighting as the race (`322220` grayscale, x0.5 for GS MODULATE, already in LIGHT1).
Measured paint (Schlesser buggy, blue pixels): PS2 mean (72,89,124), p10/50/90 33/94/155;
PC (PS2Color=1) mean (68,85,101), 47/83/122. PS2 has wider range (deeper shadows, brighter
highlights) and more blue. PS2Color darkens the PC frontend even though the PS2 frontend has
no curve — PS2Color has no PS2 counterpart; the darker PS2 courses must come from course
content (prelight vertex colours / fog), not from the output.

## 4. Offline check

`ps2_output_sim.py` applies §1 to a PC screenshot (640x512 CT16 -> two 512x256 bilinear fields,
+0.5 line, woven -> upscale to the PCSX2 window). On the PC Vehicle Select shot it reproduces the
soft highlights and halo of the white bar and headlights seen on PS2.

Open: scene DTHE (dither) state for the CT16 draw buffer not traced; PCSX2 post-filters
(FXAA/shade boost/TV shader, deinterlace mode) on the user's emulator not known.
