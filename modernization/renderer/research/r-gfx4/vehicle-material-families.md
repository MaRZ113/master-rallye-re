# Vehicle material families

Pinned vendor/d3d8/d3d8types.h is the authoritative source for FVF bit values, TCI0x10000/0x30000, D3DTA and texture ops. Header assertions are tested. Every layout below uses XYZ; there are no tangents or skinning weights in these observed FVF values.

| FVF | Stride | Normal | Diffuse | UV sets | Observed scope |
|---|---:|---|---|---:|---|
|0x102|20|no|no|1|shared-world sample; vehicle identity unproven|
|0x142|24|no|yes|1|Tata body8 draws/652 triangles, stage1 disabled|
|0x152|36|yes|yes|1|Tata body22 opaque env draws/1304 triangles plus4 alpha env draws/16 triangles|
|0x112|32|yes|no|1|Tata wheels4 draws/252 triangles each, opaque env|
|0x242|32|no|yes|2|shared-world sample79 draws/2540 triangles; vehicle identity unproven|
|0x252|44|yes|yes|2|shared-world sample1 draw/132 triangles; vehicle identity unproven|

Vehicle numbers are OFFLINE_RUNTIME_CORRELATION from canonical Broker20261006-165332_gfx3-c_racefov-80.json + frame43240/34271, matched by transform error rather than draw order; exact input hashes and errors are in vehicle-material-families.json. Body asset has39 physical draws/2022 triangles; the visible frame has34/1972. Do not invent a LOD/culling explanation or conflate all asset draws with visible draws. Layout00242/00252 observations are from the final R-GFX3 race7346 and are not vehicle proof.

All correlated Tata families have native LIGHTING137=0, alpha-test15=0, depth write14=1. Opaque families blend27=0; attached alpha-env family blend27=1. The latter is not conclusively glass. Semantic labels: BASE_PRELIT is only a risk label for diffuse-fed0x142; ENV_NORMAL_DIFFUSE for opaque0x152; ENV_NORMAL_TEXTURED for0x112; VEHICLE_ALPHA_ENV for the attached alpha0x152 subset.

Stage0 color/alpha MODULATE4, ARG1 TEXTURE2, ARG2 DIFFUSE0. Env stage1 color op18 MODULATEALPHA_ADDCOLOR, ARG1 CURRENT1, ARG2 TEXTURE2; alpha op4 with the same args. TCI=CAMERASPACENORMAL0x10000, texture-transform COUNT2=2. This is a 2D env map, not a cubemap. Existing pass construction VA0x005860A0 /RVA0x001860A0 supplies XY0.5 scale and0.5 bias. Setup owner VA0x00586150 /RVA0x00186150; source diffuse copy VA0x00577DD0 /RVA0x00177DD0 (frozen R-MAT1 / R-GFX1 references).

For stock env: C0=texture0.rgb*diffuse.rgb; A0=texture0.a*diffuse.a; C1=C0+A0*texture1.rgb; A1=A0*texture1.a, followed by native saturation/blending. The op18 expression is also documented in [Microsoft's texture-operation definition](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dtextureop); actual D3D8 IDs/arguments are verified from pinned headers and trace, not inferred from D3D9 compatibility.

Raw slot0/slot1/Null identity is preserved. Source flag byte2 controls diffuse descriptor consumption; source normal arrays do not guarantee a NORMAL-containing compiled FVF. The six-model source analysis is not a six-model runtime FVF validation. Unknown families and inherited states remain explicit.

## Continuation scope

Object-level BODY/WHEEL identity is independent of the family table. All seven supplied pre-Reset chassis groups pass the four-wheel predicate. Opaque 0x152 body subset is the sole modifier target. In the Tata 34-draw/1972-triangle group, 26 FVF152 draws total1320 triangles include **22 opaque draws/1304 triangles and4 alpha draws/16 triangles**; the latter remain stock. The task's approximate 26/1320 example must not be interpreted as 26 opaque candidates. Other observed chassis have17/13/18 opaque152 draws; coverage is model-dependent. See constellation-runtime-evidence.json for structural evidence and the existing matched Broker snapshot for material attribution.
