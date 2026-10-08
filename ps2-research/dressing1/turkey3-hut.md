# turkey3-hut case card

Source: `\TNG\DATAPSM\COURSE\TURKEY3\TURKEY3.PSM`.
Decoded SHA256: `dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc`.
Node byte offset: 3429766; material bytes at 3429821.
Material: `rustic Hut $clamp(uv) $shader(object)`.
Texture slots: `['Course\\turkey3\\hut_01-tga', 'Null', 'Null']`. Serialized flags: `[False, True, True, True]`;
opaque mesh word is retained as `0x3e0598eb` and never treated as a transform.

```text
tag1 @ 3403224 (root) -> tag6 @ 3403232 (root.0) -> tag5 @ 3429589 (root.0.9) -> tag2 @ 3429766 (root.0.9.1)
```

One material mesh owns 13 source strips and 139 faces.
Bounds X 2257.134033..2421.170898;
Y 33.534225..50.598125;
Z -957.746887..-835.967163, in game source coordinates.
Decomposition: source_index=53, coordinate_vertex=11, coordinate_edge=12. Full-edge component bounds and stable source IDs
are in [novel-candidates.json](novel-candidates.json).

The tag5 parent contains 24 material meshes of several
families. No matrix payload or independent object carrier belongs to this leaf.
Runtime tag6 child selection and inserted bound gates are documented in
[hierarchy-runtime.md](hierarchy-runtime.md). A source bound or component does not
prove a distinct live instance. Precise active selection remains UNKNOWN.

Twelve edge components have face counts20x3,9x4,12x1,10x3 and1x1.
Vertex welding merges one point-connected pair, giving11 components. These are
multiple separated subparts, not a proved single hut or twelve huts. Ten tested
components (126 source faces) have unit-scale rotated/translated PC subpart fits;
three20-face components fit PC draw627. The12-face component and1-face fragment
have no accepted counterpart in the bounded family search. Repeated fits to a
prototype do not count distinct PC instances. Texture hut_01 is positively
present in six compiled draws at other positions. Whole-object partition and
placement relation remain UNKNOWN.

Original exact-world comparison: 0/139 triangles at0.001;
identity coordinates independently anchored by GEOM1, without registration fit.
PC DX: `DataGx\Course\Turkey3\turkey3.dx`, SHA256 `724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8`.
The complete paired DX is searched, then same-family draw geometry is inspected
separately; broader standalone/TXT/XML scope is in [pc-counterpart-search.md](pc-counterpart-search.md).

Evidence: source binding CONFIRMED_BY_BYTES; source-to-runtime hierarchy
CONFIRMED_BY_BOTH; fitted geometry relations STATIC_INFERENCE; live rendering
UNKNOWN. Comparable instance count UNKNOWN. Future implementation NOT_READY.
