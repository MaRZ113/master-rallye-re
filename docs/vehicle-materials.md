# Vehicle material semantics (R4D.1)

The canonical R4D inventory is research/r4d/material-corpus.json; focused R4D.1 source recomputation is research/r4d_1/corpus-hardening.json. It covers 1,478 physical draws in 78 vehicle DX resources. Every draw stores three ordered texture slots, with slot 2 always Null in this corpus. Slot 0 is populated in 1,473 draws; three draws have Null in slot 0 but a texture in slot 1; two have no texture. Slot 1 contains shared helper families in many draws.

## Evidence-based model

A material binding should retain ordered DX slots, raw core/prefix control words, sidecar candidates and nullable HasAlpha/UsesAlpha/IsNoise values, per-texture DXT alpha statistics, source vertex colors, and distinct confidence/evidence labels. A derived preview_base_texture may be chosen independently. UNKNOWN is a valid semantic category.

**CONFIRMED_BY_EXECUTABLE:** the paired tag-2 serializer/deserializer maps DX flag bytes 0/1/2/3 to runtime material +0x22/+0x23/+0x20/+0x21, DX unknown_0x24 directly to +0x34, and three ordered texture names to handles +0x38/+0x3C/+0x40. The shader selector reads +0x22/+0x23/+0x34. Byte 0 enables the alpha family; byte 1 chooses alpha test when nonzero (all observed vehicle byte-1 values are zero). The base alpha shader uses source-alpha blending with Z writes off; its alpha-test variant uses a >128 test with Z writes on.

**CONFIRMED_BY_CORPUS:** the serialized mask is exactly (slot0?1:0)|(flag_byte2?2:0)|(slot1?4:0) in 1,478/1,478 draws. Flag byte 0 agrees with sidecar slot-0 UsesAlpha in 1,364/1,365 unique bindings; the exception is Kamaz/complete.dx draw 19. HasAlpha, UsesAlpha, and pixel alpha remain distinct. The R4D alpha table's 2,395 values count texture entries, not physical draws.

## Material families

- Opaque body/paint: the base shader's stage 0 modulates its bound texture with vertex diffuse. Slot-1 helper textures make the env shader available when Reflections is enabled; the in-game effect of whitepaint/silverpaint is confirmed by M1 as a continuous body/helmet reflection helper; absent with Reflections OFF.
- Decals: sticker/body tuples recur, but a distinct decal operation is still UNKNOWN.
- Glass: windscreen+glass tuples generally request the _alpha blend path and disable Z writes. M2 confirms continuous source-alpha transparency; sorting remains untested.
- Chrome/envmap: slot-1 presence sets runtime mask bit 0x4; the env shader uses stage 1 with camera-space normals, a COUNT2 transform, and a MODULATEALPHA_ADDCOLOR operation. A reflection-vector coordinate claim would be incorrect.
- Light/glow: brake/glow-like alpha draws also request _alpha; byte 2 is not the alpha-test selector. M4 confirms active brake-light glow alpha response while the base lamp remains. Additive blending, emission, and dynamic lights remain UNKNOWN.

R4E provides restricted template-preserving fixed-field material edits. See research/r4d_1/dx-to-runtime-material.md, alpha-path.md, texture-stage-map.md, and runtime-test-plan.md for exact evidence and next tests.

## R4D.1 in-game closeout

M1 and M3 confirm distinct body/helmet and chrome/trim reflection helpers; both are gated by Reflections. M2 confirms glass source-alpha blending. M4 confirms active brake-glow alpha strength. See research/r4d_1/runtime-results.md and JSON for candidate hashes and human evidence. These observations do not prove exact transparent sorting or damage fade.

## R4E fixed-field authoring

Existing draw alpha enable (flag byte 0) can be toggled on draws whose
alpha-test selector is zero. An existing slot-1 helper permits toggling mask
bit 4; this control is structurally checked but still awaits an isolated
runtime test. Existing texture content can be replaced under the same DXT
name. Flag bytes 1-3, unknown controls, texture strings and new material
creation remain untouched. E4 probes the windscreen alpha-enable change.\n
