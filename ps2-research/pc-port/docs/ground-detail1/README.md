# GROUND-DETAIL1 — PS2 ground detail contract (opt-in `GroundDetail=1`)

Evidence: `ps2-research/course-light1/findings.md` (EE shader mode 4 / dispatch `312610`, PC
`shader/base_noise` pass `585ac0`, two PCSX2 GS dumps). Prelight and fog are already identical on
both platforms; the ground detail pass is the one course-shading difference.

| | PC (Stock) | PS2 | GroundDetail=1 |
|---|---|---|---|
| ground | tex x prelight x **2 x noise-tga** (stage1 MODULATE2X, avg x0.954) | fog(tex x prelight) **- CommonTextures/NOISE** (DECAL, ALPHA Cd-Cs, avg -0.108, unfogged) | pass 1: original draw, stage1 off; pass 2: dest - PS2 noise (BLENDOP REVSUBTRACT ONE/ONE), same geometry, PC noise UV set, no fog, no Z write, ZFUNC LESSEQUAL |

Turkey check from screenshots: PC ground 176 / 0.954 - 27.6 = 157 = PS2 measured 157.
Noise tiling: PC noise UV/ground UV edge ratio p10/50/90 0.235/0.522/1.029 (France1) vs PS2 dump
0.229/0.506/1.187 — the PC noise UV set is used as is.

## Admission (all required, else the original draw)

* `GroundDetail=1`, pinned asset `PS2GroundNoise.gxi` (sha `a9311356…`, `tools/prepare_ground_noise_asset.py`);
* scene open, render thread, no state-block recording, caller = course draw loop `0x57707e`;
* native stage contract of `base_noise`: stage0 TEXTURE x DIFFUSE MODULATE, stage1 CURRENT x TEXTURE
  MODULATE2X, no texture transform, stage2 off, no pixel shader; opaque variant (no alpha blend or
  test), Z on, BLENDOP ADD;
* stage1 texture = exact PC noise-tga: 128x128 32-bit, lockable, level-0 SHA-256 `4325c7d4…`
  (identical in all 36 courses), cached per resource generation;
* caps: BLENDOP, ONE/ONE, SELECTARG1.

All 22 touched states are captured and restored in reverse; a failed restore stays pending and the
existing `repair_reflection()` chain finishes it. Grass/course-object depth observers still see the
draw. Session log: `ps2_ground_detail` once per distinct outcome (`ground_detail_applied`, or the
rejection reason such as `pc_noise_format_not_32bit`).

Integration: patch 0001 (visual_wrappers include + `groundintegration::draw` after the brake lamp
hook, `ps2_ground_detail_contracts` test); lock updated.
