# COURSE-LIGHT1 — why PS2 courses look darker than PC

Read-only research (PS2 EE SLES_509.06 Ghidra/EER + Rabbitizer; PC MRallye.exe REA/Ghidra + objdump;
data through tngtool/geometry_delta and the Course SDK). Context: PS2Color (global curve) fits the
environment but darkens the already-matched car; PS2-OUTPUT1 showed the PS2 output path has no
curve. So the difference must be in course content or course shading.

## 1. Prelight data: identical (CONFIRMED_BY_BYTES)

PS2 course PSM source vertex (52 B): normal +0, control +12, **colour word +16 (bytes A,B,G,R)**,
UV +20, XYZ +36. PC course DX keeps a 4-byte D3DCOLOR per vertex. Matching vertices by exact
position (`compare_prelight.py`):

| course | matched vertices | PS2 R/G/B median | PC R/G/B median | PS2/PC ratio p10/50/90 |
|---|---|---|---|---|
| TURKEY3 | 52 842 | 235/235/203 | 235/235/203 | 1.0/1.0/1.5 |
| FRANCE1 | 63 750 | 210/210/188 | 210/210/187 | 1.0/1.1/1.6 |
| ITALY_S1 | 65 979 | 222/216/187 | 228/221/191 | 1.0/1.0/1.6 |

The baked course lighting is the same data. (p90 > 1 = a few PS2-only/re-lit vertices.)

## 2. Course shaders (NEW-DECOMP, shader table `3a6f18..3a7c2f`, setup methods `3ae…`)

| shader | mode | extra | GS (dispatch `312610`, table `0x4850c0`) |
|---|---|---|---|
| ground | 4 | `CommonTextures/noise`, value .4 | pass 1: tex x prelight, TFX MODULATE, Gouraud, **FGE 1**; pass 2: CommonTextures/noise, TFX DECAL TCC0 (confirmed by dump), ABE, **ALPHA 0x62 FIX 128 = Cd - Cs** (subtract), no fog, TEX1 K from 0.04 |
| object / sign | 15 | .5 / .25 | tex x prelight, MODULATE, **FGE 1**, opaque |
| tree | 6 | .2 | MODULATE, FGE 1, TEST variant |
| sky | 12 | .01 | TFX HIGHLIGHT, no fog |
| metal / dull | 3 | env | car-style env add (ALPHA 0x29) |

No course shader uses a lighting auxiliary (`322220` is car only), so prelight goes straight to
the GS.

## 3. PC ground detail pass (NEW-BYTES)

PC `shader/base_noise` (`565da0` -> class `585880`, pass `585ac0`): one pass, stage0 TEXTURE x
DIFFUSE (MODULATE), **stage1 CURRENT x noise-tga MODULATE2X**, linear/linear/point filters.
Course `noise-tga` (PC 128x128 DXT mean 121.6; the PS2 course NOISE-TGA.GXI 64x64 mean 121.2 is
the same image) -> ground x0.954 on average, brightening above 0.5 and darkening below.

## 4. GS dump confirmation (CONFIRMED_BY_RUNTIME, PCSX2 GSDump v9)

Two single-frame dumps by the user (SeatBuggy, standing start): Turkey2 (`...143139.gs.zst`,
191 504 vertex kicks) and France1 (`...143210.gs.zst`, 88 288 kicks). Reader: `gsdump.py`
(header, screenshot, GIF PACKED/REGLIST replay; VRAM = freeze state + 373 bytes, CT32 unswizzle);
grouping: `gsgroups.py`. Draw buffer FRAME FBP 0, FBW 10, **PSMCT16** (as in PS2-OUTPUT1).

### 4.1 Ground second pass

| | value |
|---|---|
| context | 2, PRIM IIP TME ABE, no FGE |
| texture | TBP 0x1e00, TBW 2, **CT32 128x128**, mipmapped = `TNG/DATAPSM/COMMONTEXTURES/NOISE.GXI` (mean 27.59 matches exactly) |
| TFX / TCC | **DECAL**, TCC 0: Cs = texel RGB, vertex colour unused |
| ALPHA_2 | 0x62, FIX 128: **Cd - Cs** |
| noise texel | mean **27.6/255 = 0.108**, p10/50/90 17/27/40, max 54 |

PS2 ground = `fog(tex x prelight) - noise`. Check against the user's Turkey screenshots:
PC 176 / 0.954 - 27.6 = **157**, measured PS2 157.

### 4.2 Prelight

Course pass-1 vertex RGB is the PSM byte halved (max 127 = 254/2); GS MODULATE `Ct*Cf>>7`
equals PC `tex*diffuse/255`. No difference.

### 4.3 Fog

PS2 fogged vertices give F against w = 1/Q identically on both courses: F=255 up to w~48, then
linear ~0.547/unit, F=0 at w~514 (w = 64/128/256/362/430 -> F = 247/211/141/81/47).
PC trace (proxy F10 frames): FOGVERTEXMODE LINEAR, FOGSTART **50**, FOGEND **500** on every
course. Same curve within measurement. FOGCOL: Turkey2 (160,183,213), France1 (124,137,153); PC
colours come from the same cloud set-up per course (not yet compared one to one). The PS2 noise
pass is unfogged, so it also darkens fogged distance.

## 5. What this means

* The course difference is **one mechanism**: the ground detail pass. PS2 subtracts a dark noise
  (about -28 levels, also on fogged ground); PC multiplies by 2x a mid-grey noise (about -5 %).
  Prelight and fog match. This explains ground -15 % and rock -8 % (rock is `$shader(ground)`
  terrain with a brighter base, so the constant subtraction is relatively smaller); sky (no
  detail pass) only -4 %.
* PS2Color (global curve) is the wrong tool: it also darkens car, sky and menus.

## 6. Proposed port (overlay only, opt-in, identity-gated)

On PC draws that use `shader/base_noise` (stage1 = noise-tga, COLOROP MODULATE2X):
1. draw the original with stage1 disabled (tex x prelight, PC fog unchanged);
2. private second pass on the same geometry: texture = PS2 `CommonTextures/NOISE.GXI` (PS2 asset,
   like the other PS2 assets), COLOROP SELECTARG1 TEXTURE, `BLENDOP REVSUBTRACT, ONE, ONE`
   (dest - src), ZFUNC EQUAL / no Z write, fog off, the noise texcoord set.

Open before coding: PS2 noise UV scale vs the PC noise texcoord set (dump ST vs PSM UVs) and
the caps path when D3DPMISCCAPS_BLENDOP is missing (then Stock).

## 7. Car tint check (user A/B, 2026-10-17)

Measured (unsaturated pixels): sticker PS2 (215,236,244) vs PC (209,205,217); body blue PS2
(102,117,158) vs PC (98,109,137). From the Turkey2 dump:

* the "bagoo" decal is texture 0x3c80 (128x128 CT16, rear decal sheet), drawn by the normal body
  contract: TFX MODULATE x prelight 50..79/128 (the `322220` gray, as LIGHT1) + env layer
  (0x3d00, DECAL, ALPHA 0x29 = Cd + Cs);
* the env target is built exactly as on PC: static 0x3840 (= PS2EnvSource64x64, VRAM avg 30/31/32
  vs asset 33/34/35) x80/128, then the whole 640x512 draw buffer flipped x48/128 in 20 strips;
  it is built after all terrain, just before the car (no early capture);
* no other pass touches the car and the output path has no colour stage (PS2-OUTPUT1).

0.617 x 248 + env must give the PS2 sticker; R fits with the reconstructed env (62), G/B need
+20..40 more, so the panel samples a bluer part of the env on PS2 than on PC. Remaining cause:
the env UV basis (binary-diff1 lists it as "residual coefficient/basis approx."). The dump has the
real env UV for every car vertex; next step is to compare them with the PC env UV of the same
vertices.

## 8. Env UV check against the PC formula (2026-10-17)

PS2 formula (refl1): `UV = (0.5,0.5) + n.(0.5*M[:,0], -0.5*M[:,1])`, M = object x view. PC (our
fleet/frontend env layer): stage1 `TCI_CAMERASPACENORMAL`, `TTFF_COUNT2`, D3DTS_TEXTURE1 taken from
the game = diag(0.5,0.5) + translation (0.5,0.5) (F10 trace), i.e. `u = .5+.5 nx_cam, v = .5+.5 ny_cam`
(D3D camera space: x right, y up).

Dump env-layer ST/Q of the car (target 0x3d00), both dumps:

* by screen row: roof (y 280..300) v = 0.97, rear panel (y 340..360) v ~ 0.50, low parts v < 0.5;
* by screen column: left flank u ~ 0.05..0.20, right flank u ~ 0.80..0.90 (clamped at 0/1).

So the PS2 view y axis points down and x right, giving `u = .5+.5 nx_right, v = .5+.5 ny_up` —
the same mapping, sign and scale as PC. **No divergence; nothing to change.** The env target layout
(static unflipped, frame flipped) also matches (section 7).

The bluish car tint therefore is not the UV formula. Open: the env *content* (PS2 draw buffer
copied at capture time in CT16) — the HW-renderer dump keeps the target stale in VRAM. A GS dump
taken with the PCSX2 **software** renderer keeps the real 64x64 target and the frame in VRAM and
would settle it.

## 9. Software-renderer dump: the car tint is the sky in the reflection (2026-10-17)

User SW dump (`...152841.gs.zst`, Turkey start). In SW mode VRAM holds real render targets.
Decoder notes: CT16 targets decode cleanly at freeze offset 373 with the canonical GSdx tables,
CT32 at 372 (`gsdump.py`; offset of the VRAM copy is not yet pinned exactly — colours are reliable).

* Env target 0x3d00 (64x64 CT16) rows: top (frame bottom, ground) warm (35..51, 30..43, 19..26);
  bottom (frame top, sky) bluish (64..67, 72..75, 80..81).
* Draw buffer top rows (the PS2 sky): (147..154, 164..174, 164..183) — a blue sky; 0.625 x static
  bottom (15,12,10) + 0.375 x that = (71,75,79), matching the target.
* The sticker vertices sample the env at **v ~ 0.84** (u ~ 0.49): the panel reflects the sky.
  PS2 env there (80,80,88); with prelight 70..79/128 x white 248 this gives the measured cyan-white.
* PC order is the same (clear -> course -> env capture -> car), mapping and layout are the same
  (sections 7, 8). The PC A/B shot has a grey-white overcast sky (frame top 222,221,226).

Cause: the sky itself differs between the two runs. Both builds share `gaAiCloudSetUp`
(`Cloud Type 0 - 5`, 0 in the Turkey2 scene) and the broker value `CloudNumber`, which `1973d8`
advances by one per race and wraps after 5 (`CloudNumberUsed` = the set in use; textures
`Misc/Sky/cloud%d/...`). Each race gets the next of six skies, so the PS2 and PC screenshots were
taken under different skies. **No post-processing and no shader difference**; nothing to port.
A like-for-like comparison needs the same cloud set on both (same race count since launch).

## 10. "Chrome on PC, metallic on PS2" + race MotionBlur (SW dump `...153853`, user A/B 14/15)

Same cloud set on both. Measured car (blue pixels): PC median (97,111,147), lum p10/50/90 82/118/144;
PS2 (78,101,144), 67/108/204 — PS2 has darker lower/side surfaces; the PC rear bumper is light
grey-blue where PS2 is dark navy.

Verified identical on both (this dump):
* mesh -> env routing: all carshiny body meshes use the captured target 0x3d00 (= PC `mixed`), root.17
  MHelmet uses its static whitepaint (0x3e50), as on PC; a static CHROME-TGA env (0x29d0, VRAM =
  GXI x 80/128) is used by non-body parts (wheels/rims) only;
* prelight per mesh (seat06/seat07 70/128, sbshade 48/128), base textures (VRAM = source GXI
  minus CT16 truncation), no lighting/specular on the PC car draws (F10: LIGHTING 0, SPECULAR 0);
* env target content: rebuilding 0.625 x static + 0.375 x flipped draw buffer reproduces the real
  PS2 target exactly (62,67,69 vs 62,66,69 at the car's env UVs); PC view matrix is y-up (no flip).

Not explained offline: the PC bumper colour equals base + the *sky* rows of the env, PS2's equals
base + the *ground* rows. Either the PC env layout/orientation differs from the PS2 target at runtime
or the PC env content differs; a PC screenshot cannot separate the two (the car is in it).
Next step needs PC ground truth: a diagnostic env pattern (top half / bottom half coloured) or an
F10 dump of the PC 64x64 target.

Race MotionBlur: the display copy in this dump uses FIX **103** (display = 0.805 new + 0.195
previous). Source: camera set-up `1b1e70`: `MotionBlur = 128 - clamp(camera+0x20,0,1)*128`; the
value interpolates (`1b2b90`) to a per-camera-preset target (`1baa80`, preset +0xbc). Not present
in the PC Cameras.xml or as a PS2 data string — engine preset. Chase camera = 0.195 (measured);
other cameras need their own dump. Showroom: `1 - sqrt(|delta angle|)*0.95` (output1).

## 11. Chrome cause found: static env rows reversed on PC (2026-10-17)

PC ReflectionDebug=1/2 runs: env UV and frame pass match PS2; the PS2 static 0x3840 (PSMCT16, sampled
unflipped by two 32x64 sprites) is `PS2EnvSource64x64.gxi` with its rows reversed (error 12.8 vs 27.4).
The PC uploaded it as stored, putting the chrome-ball sky highlight into the ground half of the
target. Fixed in `convert_static_env`; evidence and scripts in `pc-port/docs/reflection-static1`.
