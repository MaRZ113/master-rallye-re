# REFLECTION-STATIC1 — static env texture row order (the "chrome on PC" cause)

## Evidence

* DIAG-REFLECTION1 (ReflectionDebug=1, user screenshots): PC env UV/orientation == PS2.
* DIAG-REFLECTION2 (ReflectionDebug=2, user screenshot, Turkey SeatBuggy) vs PS2 target 0x3d00 in the
  SW GS dump `...153853`: bottom half (sky) similar; top half (ground side, sampled by bumper/flanks)
  PS2 dark brown (centre ~28,22,13), PC light grey-blue (~96,108,112).
* `env_split.py`: PC target − static(x80/128) gives a sane frame term (ground ~70..117, sky ~200), so
  the PC frame pass is right. For PS2 the same subtraction goes negative in the top half (1869
  texels) — the PS2 static term is laid out differently.
* `env_pass.py`: PS2 builds 0x3d00 from the static 0x3840 (PSMCT16) with two 32x64 SPRITEs, UV V
  0..64 (not flipped), FIX 80, then the 640x512 draw buffer V 512..0 (flipped), FIX 48, 20 strips.
* `static_vram.py`: VRAM 0x3840 matches `PS2EnvSource64x64.gxi` **with rows reversed** (mean abs
  error 12.8; as stored 27.4; mirrored 37.1). Picture: `env-asset-ps2vram-ps2target-pctarget.png`
  (asset | PS2 VRAM static | PS2 target | PC target, x1.5 brightness; VRAM decode shows swizzle seams).

So the PC uploaded the chrome ball upside down: its bright sky highlight landed in the top half of
the target, which lower and side surfaces sample — the "chrome" look.

## Fix

`convert_static_env` (renderer/reflection_pilot.cpp) reverses the rows when converting the verified
asset (asset bytes and sha gate unchanged). Applies wherever the static env is used (Reflection modes).
`predict.py` on the user's capture: target top-half luminance 60.8 -> 48.4 (PS2 34.1), bottom
79.5 -> 91.9 (PS2 80.4); top-centre becomes warm brown. The remaining top-half gap is frame content
(PC ground brighter than the PS2 CT16 ground at capture time).
