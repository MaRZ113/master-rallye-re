# Vehicle material runtime model (R-MAT1)

**CLOSED WITH NON-BLOCKING UNKNOWNS** for the observed retail vehicle branch.
The fresh [R-MAT1 corpus report](../research/r-mat1/corpus-validation.json)
covers 1478 physical draws in 78 resources. All are classified; slot0 is
populated 1473 times, slot1 1092 times, and slot2 is NULL 1478 times. This is
vehicle corpus evidence, not an engine-wide slot2 rule.

## Serialized and runtime semantics

| Raw flag byte | Runtime offset | Role | Confidence |
|---:|---|---|---|
| 0 | +22 | alpha family enable | CONFIRMED_BY_EXE |
| 1 | +23 | alpha-test selector when byte0 enabled | CONFIRMED_BY_EXE |
| 2 | +20 | pass vertex diffuse enable -> FVF DIFFUSE | CONFIRMED_BY_EXE |
| 3 | +21 | pass source UV enable -> FVF UV count | CONFIRMED_BY_EXE |

`unknown_0x24` copies directly to runtime mask+34. Mask01 gates the base
handle; mask&03 selects the base family; mask04 plus global Reflections>0
selects/binds env. Byte2's equality to mask02 is CONFIRMED_BY_CORPUS, while
its independent FVF consumer is CONFIRMED_BY_EXE. All observed masks are
1:21, 2:2, 3:363, 5:151, 6:3, 7:938.

The loader -> compiled fixed vector -> shader pass mapping -> SetTexture chain
proves slot0 (+38) -> stage0 and slot1 (+3C) -> stage1. NULL positions are
retained, never promoted. The three NULL-base/helper-present records retain
base_env when Reflections is ON. Blender suppresses their env preview under
the documented HIGH_CONFIDENCE_INFERENCE of the fixed-function NULL cascade;
no new in-game pixel observation is claimed. See
[texture-stage-binding](../research/r-mat1/texture-stage-binding.md).

Stage0 modulates texture with diffuse. Env stage1 uses camera-space normals,
COUNT2 and the constructor's XY scale0.5/bias0.5 matrix; color is
`current.rgb + current.a*env.rgb`, alpha `current.a*env.a`.
All eight observed helper filenames use this generic mechanism. Texture names
do not select shader families.

## Alpha, layering and ordering

1241 draws are opaque, 237 blended; no stock draw selects alphatest. The six
base/env and alpha/test families are statically established. Base_alpha setup
uses ZWRITE=0, blend=1, SRCALPHA/INVSRCALPHA, test=0. Base_alphatest setup uses
ZWRITE=1, blend=0, test=1, GREATER128. Env_alpha setup writes ZWRITE=1 and does
not explicitly reset alpha test. The emitter subsequently writes instance
ZENABLE/ZWRITE overrides. These explicit writes are distinguished from a
complete effective device-state snapshot in the typed model; see
[runtime-material-map](../research/r-mat1/runtime-material-map.md).

Alpha-blend submissions use a separate queue, after opaque/alphatest. The
64-bit key orders pass, descending quantized shared bound depth, order counter,
shader and texture. It is object/bound depth, not per-triangle sorting. Equal
full keys and all scene grouping configurations are not promised stable.
See [transparent-ordering](../research/r-mat1/transparent-ordering.md).

The observed sticker/decal draws are ordinary opaque base/env geometry;
all 25 glow-name draws use ordinary source-alpha base/env families. There is
no distinct stock vehicle additive family in this selector/corpus evidence.
Dynamic lamp activation, physical emission and damage are separate questions.

HasAlpha, UsesAlpha, decoded pixel alpha and runtime alpha choice remain
distinct. Byte0 agrees with unique sidecar slot0 UsesAlpha in 1364/1365
bindings, retaining Kamaz/complete.dx draw19 as the exception. The older R4D
2395 alpha values counted texture entries, not physical draws.

## Existing human evidence and writer boundary

R4D.1 M1/M3 confirm the tested Astero reflection helpers and Reflections gate;
M2 confirms glass source-alpha response; M4 confirms active brake-glow alpha
strength. R4E E1/E3/E4 and R4E.1 N1/M1 retain their exact runtime labels for
UV/color/alpha/normal/env edits. The earlier E2 normal probe stays inconclusive.
See [R4D.1 runtime results](../research/r4d_1/runtime-results.md),
[R4E runtime results](../research/r4e/runtime-results.md), and
[R4E.1 runtime results](../research/r4e_1/runtime-results.md).

Existing-draw alpha enable can be toggled when byte1 is zero. An existing
slot1 helper permits toggling mask04. Supported source normals/UVs/colors and
same-size DXT content can be edited through the existing writers. Byte1/2/3,
unknown controls, texture strings and new material creation retain their
previous writer restrictions. Interpreting a field does not authorize its
writer or arbitrary material creation.

Damage RemoveEnvMap/EnvMapFadeStrength were traced only to configuration owned
by the renderer: **OUTSIDE STATIC MATERIAL PREVIEW**, non-blocking. Optional
variant objects/unknown controls and full effective scene state stay raw or
explicit UNKNOWN. [Remaining boundaries](../research/r-mat1/remaining-unknowns.md).
Historical R4D/R4E notes retain their original evidence and are superseded by
this current runtime/preview closeout where stated.
