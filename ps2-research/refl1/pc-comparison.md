# PS2 versus PC: native evidence and proxy experiments

PC references were inspected read-only in
`modernization/renderer/research/r-gfx4/`: findings, reflection-prototype,
vehicle-material-families and vehicle-classification. No PC code or source asset
was changed. Prior PC observations are reported as prior evidence, not a fresh
PCSX2/PC runtime experiment in REFL1.

| Dimension | Original PS2, this static reverse | Original PC, existing R-GFX4 evidence |
|---|---|---|
|Source|Mixed static ENV64 plus flipped current framebuffer into64x64 target|Recorded native stage1 2D environment texture; image producer/update cadence not established by those stage records|
|Coordinates|Selector1 source-normal times object/view orientation, xy scale/bias|CAMERASPACENORMAL0x10000, COUNT2; XY scale/bias .5 |
|True reflected view vector|Not in selected PS2 helper|Native observed mode is NORMAL, not proxy REFLECTIONVECTOR|
|Body RGB|Primary MODULATE with prepared local-normal grayscale; secondary DECAL added with FIX128|Stage0 MODULATE(texture,diffuse); stage1 MODULATEALPHA_ADDCOLOR|
|Body equation|Cb + Cenv, subject GS saturation/depth/fog|C0=T0.rgb*D.rgb;A0=T0.a*D.a;C1=C0+A0*T1.rgb;A1=A0*T1.a|
|Body alpha/blend|Primary ABE0, secondary ABE1 FIX; no texture-alpha coefficient in second body layer|Recorded opaque native family ALPHABLENDENABLE0 and ZWRITE1; combination occurs in texture stages|
|Normals/colors|Source normals;322220 writes RGB clamp2..254 andA254, cache halves bytes|Recorded FVF0x152 normal+diffuse; native LIGHTING0, copied source diffuse is relevant|
|Glass|Dedicated20: alpha primary, static highlight FIX96; both depth writes masked|Alpha-env families recorded; not all conclusively identified as glass|
|Chrome|Selected Kia carshiny secondary chrome replaced by common target|Separate PC material-family/classifier evidence; not proof of a PS2 chrome shader|
|Texture update|Shared first-eligible-call gate per presentation reset, disabled by split-screen|UNKNOWN from bounded R-GFX4 stage/source records|

PC Tata observations retained in R-GFX4 separate source39draws/2022faces from
recorded34draws/1972faces;22opaque env0x152 draws/1304faces and4alpha draws/16faces
were observed in that capture. These are not one-to-one matches to the31PS2 mesh
records, which include conditional variants. No topology identity is inferred.

The PC proxy's ViewDependent2D uses REFLECTIONVECTOR0x30000 on selected opaque
body draws and restores the native state afterwards. This is **PC_PROXY_EXPERIMENT**,
not ORIGINAL_PC_ENGINE_BEHAVIOR and not the recovered PS2 equation. A proxy
test's appearance cannot prove the PS2 sampling input or source image.

The native PC stage observations are prior RUNTIME_CONFIRMED_PC_OBSERVATION;
the accompanying EXE interpretation is prior STATIC_PC_INFERENCE / original
engine research. PS2 results here are CONFIRMED_BY_EXE/BOTH with no captured live
frame. These categories remain independently labelled.

The strongest portable differences are source image generation and per-material
color/blend strength rather than simply switching PC normal coordinates to a
reflection vector. Exact visual attribution remains STATIC_INFERENCE until a
controlled comparison. Native PC producer provenance and live PS2 target pixels
are missing; neither side is casually classified “static” from its stage name.
