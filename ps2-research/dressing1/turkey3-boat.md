# turkey3-boat case card

Source: `\TNG\DATAPSM\COURSE\TURKEY3\TURKEY3.PSM`.
Decoded SHA256: `dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc`.
Node byte offset: 3583641; material bytes at 3583695.
Material: `boat1 $shader(object)`.
Texture slots: `['Course\\turkey3\\boat1-tga', 'Null', 'Null']`. Serialized flags: `[False, True, True, True]`;
opaque mesh word is retained as `0x3e63cbf8` and never treated as a transform.

```text
tag1 @ 3403224 (root) -> tag6 @ 3403232 (root.0) -> tag5 @ 3581812 (root.0.52) -> tag2 @ 3583641 (root.0.52.8)
```

One material mesh owns 12 source strips and 113 faces.
Bounds X 3244.027100..3275.188232;
Y 23.061644..34.054211;
Z 197.426758..218.914963, in game source coordinates.
Decomposition: source_index=51, coordinate_vertex=7, coordinate_edge=7. Full-edge component bounds and stable source IDs
are in [novel-candidates.json](novel-candidates.json).

The tag5 parent contains 26 material meshes of several
families. No matrix payload or independent object carrier belongs to this leaf.
Runtime tag6 child selection and inserted bound gates are documented in
[hierarchy-runtime.md](hierarchy-runtime.md). A source bound or component does not
prove a distinct live instance. Precise active selection remains UNKNOWN.

The113 faces split into a59-face component, five10-face components and one
4-face component. All seven have accepted unit-scale subpart fits against paired
boat1-textured PC geometry. The59-face component matches draw825, with maximum
corner error approximately0.000231 units. Subpart fits alone do not establish an
original authored boat instance or a seven-boat population. Small symmetric pieces have multiple fit
hypotheses; they may be unrelated authored subparts. PC family draws96/263/825
occupy other source positions. Turkey material boat1 is a compiled landscape
mesh, distinct from France1 Egg boat1 and its REDDINGHY resource/gaEntitySpline
owner. No separate spline owner is found in paired Turkey3 source scene.

The whole113-face source group also fits draw825 under one common proper rigid
transform at scale1. Maximum absolute corner-coordinate residual is0.000394.
All113 source triangles correspond uniquely to113 of its125 target records;
12 other PC draw records are outside this correspondence. This preserves the
relative placement of all seven disconnected source components, a stronger
result than isolated prototype reuse. Original authored instance identity
remains UNKNOWN. See [boat-congruency.json](boat-congruency.json) for the
compact transform and independent exhaustive target check.

Original exact-world comparison: 0/113 triangles at0.001;
identity coordinates independently anchored by GEOM1, without registration fit.
PC DX: `DataGx\Course\Turkey3\turkey3.dx`, SHA256 `724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8`.
The complete paired DX is searched, then same-family draw geometry is inspected
separately; broader standalone/TXT/XML scope is in [pc-counterpart-search.md](pc-counterpart-search.md).

Evidence: source binding CONFIRMED_BY_BYTES; source-to-runtime hierarchy
CONFIRMED_BY_BOTH; fitted geometry relations STATIC_INFERENCE; live rendering
UNKNOWN. Comparable instance count UNKNOWN. Future implementation NOT_READY.
