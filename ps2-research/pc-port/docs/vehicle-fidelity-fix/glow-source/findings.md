# Terrano glow: original texture semantics explain the hard polygon

Evidence: CONFIRMED_BY_BYTES for the texture/mesh comparison; LIVE_PC_PROXY_OBSERVATION for admission and setter/draw/restore success. Screenshot correlation agrees with the numerical mechanism; no PS2 pixel parity claimed.

Original PS2 Terrano `root.24.0.1` at191404 owns20 glow faces and20 unique vertices, `$shader(carbrakelight)`, slot0 `commontextures\\breaklightsonglow-tga`, slot1 `commontextures\\perspex-tga`. Compare original PC `Terrano/car.dx` physical record31. Position matching under0.001 uniquely joins all20 vertices; UV residual0, normal residual1.1920928955078125e-7; both original colors are white. This is not a model-shape problem for the glow surface.

PS2 GXI is16x16 RGBA, SHA b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09. Alpha is zero throughout. RGB fades to black: range R0..255,G0..222,B0..78. Both corner samples are transparent black. The original executable mode14 blend is Cs+Cd; TEX0 TFX1DECAL/TCC1 and no secondary environment pass. Thus zero alpha does not eliminate the source RGB in this blend.

PC DXT is32x32 BGRA, SHA2fa12d48010bf763215d5bd02e35244da148dbb8bfa2da98d8da8dd651b654e3. Its red channel is255 in EVERY pixel; alpha0..249 stores the smooth coverage. All41 alpha-zero pixels retain full red RGB255,0,0. Under the original SRCALPHA/INVSRCALPHA draw, those pixels contribute zero source color. Under ONE/ONE with unchanged PC texture, they contribute full red. This directly explains loss of coverage smoothing; it is not proof MSAA was disabled. Do not adjust MSAA globally.

Smallest source-faithful repair: keep current verified native-emitted glow admission and source geometry/UV, bind the original local PS2 GXI, select its RGB directly, disable stage1 environment contribution, use proved additiveONE/ONE, no alpha multiplication (PS2 alpha is all zero). Preserve original PC brake conditional emission. Exact texture lifetime/Reset/state restoration and bounded logging remain required. Missing private asset must fail closed to stock, never silently retain the old PC texture with ONE/ONE.

Alternative PC-texture-only compatibility repair would premultiply RGB by original PC alpha before ONE/ONE, but this merely reconstructs the PC fade and is not the original PS2 RGB/color gradient; it should not be named PS2 parity. Prefer original PS2 resource now that geometry and UV correspondence are exact.

Current session30176 frame7503 glow arguments4,5850,20,14202,20. Session `ps2_brake_glow` events confirm current upload verification and apply/draw/restore HRESULT0. F10 captures logical states, not the temporary private native transaction. Runtime30176.json preserves source states, effective filtering and resource generations without treating IDs/ranges as persistent classifiers.

A/B: same Terrano, same camera, released versus held brake; verify fade-to-black edge and orange/yellow PS2 source coloration, restore after release, Reset/window resize, MSAA2x/4x. Do not infer PS2 timing/camera parity from these static checks.
