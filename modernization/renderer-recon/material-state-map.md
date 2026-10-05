# Material to D3D state

**CONFIRMED_BY_EXISTING_RESEARCH:** retain R-MAT1's
[runtime map](../../research/r-mat1/runtime-material-map.md),
[ordered binding](../../research/r-mat1/texture-stage-binding.md) and
[sort model](../../research/r-mat1/transparent-ordering.md).
Loader/deserializer VA `0x005528B0` maps core bytes0/1/2/3 to runtime+0x22/+0x23/
+0x20/+0x21; word+0x24 to runtime+0x34, ordered texture slots+0x38/+0x3C/+0x40.
Selector `0x00580360` combines flags, slot presence and options; compiled bindings
`0x00577620` retain Nulls and stage positions. Reflections enables slot1/env family
through the known mask; no texture-alpha-only family inference is substituted.

**CONFIRMED_BY_EXE**, fresh setup exports:

| Owner VA | Main D3D behavior |
|---|---|
| `0x005867A0` base | LIGHTING0; ZENABLE1; opaque ZWRITE1/blend0; base_alpha ZWRITE0/blend1; blend5/6; alpha-test REF128/FUNC5 |
| `0x00586150` env | LIGHTING0, ZENABLE1, ZWRITE1 even alpha setup; blend5/6; optional alpha-test; stage1 op18 CURRENT/TEXTURE, camera-space normal0x10000, COUNT2 matrix |
| `0x00585AC0` noise | unlit, depth enabled/write1; optional blend5/6 or alpha-test; stage1 COLOR/ALPHA MODULATE2X5 |
| `0x005854D0` water | unlit, depth enabled/write1; optional blend5/6; stage0 alpha SELECTARG2; stage1 COLOR ADD7 / ALPHA SELECTARG1 |
| `0x00584EA0` particles | unlit, ZENABLE1; solid depth write1; other modes write0; blend, add, color/density absorb modes |

Base stage0 is MODULATE4(TEXTURE2, DIFFUSE0), including alpha in the usual base
branch. Env stage1 op18 is MODULATEALPHA_ADDCOLOR, not a modern physical reflection
model; texcoord source is a camera-space normal, not reflection vector. Env texture
matrix scales/biases normal coordinates. Cull is generally inherited; common draw
can force CULL_NONE in its camera branch. A material document must not invent a
per-family cull override that setup does not write.

Emission `ApplyDraw_00576970` invokes setup, then overrides ZENABLE/ZWRITEENABLE
from instance+0xA8/+0xA9. It supplies per-instance fog gating and per-compiled
addressing flags (WRAP1/CLAMP3). Material setup values are consequently not the
whole final draw signature. No SetMaterial diffuse/specular/emissive call has been
established in these paths: packed vertex diffuse feeds the combiner.

Opaque and alpha queues flush in that order in `0x00562810`. Alpha-test joins
opaque. Alpha uses the composite quantized bound-depth/pass/counter/shader/texture
key documented by R-MAT1, not per-triangle sorting. Tie stability and all scene
grouping callers remain bounded. [material JSON](data/material-state-map.json)
keeps setup states and final instance overrides separate.
