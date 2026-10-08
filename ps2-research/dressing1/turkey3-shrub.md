# turkey3-shrub case card

Source: `\TNG\DATAPSM\COURSE\TURKEY3\TURKEY3.PSM`.
Decoded SHA256: `dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc`.
Node byte offset: 3620664; material bytes at 3620723.
Material: `TURshrub2 $alphatest() $shader(treeblend)`.
Texture slots: `['Course\\turkey3\\shrubtrig2-tga', 'Null', 'Null']`. Serialized flags: `[True, True, True, True]`;
opaque mesh word is retained as `0x3ed7cf2d` and never treated as a transform.

```text
tag1 @ 3403224 (root) -> tag6 @ 3403232 (root.0) -> tag5 @ 3617911 (root.0.63) -> tag2 @ 3620664 (root.0.63.11)
```

One material mesh owns 14 source strips and 256 faces.
Bounds X 1769.264160..1877.363525;
Y 30.159233..57.838039;
Z -78.139091..30.376247, in game source coordinates.
Decomposition: source_index=64, coordinate_vertex=16, coordinate_edge=16. Full-edge component bounds and stable source IDs
are in [novel-candidates.json](novel-candidates.json).

The tag5 parent contains 12 material meshes of several
families. No matrix payload or independent object carrier belongs to this leaf.
Runtime tag6 child selection and inserted bound gates are documented in
[hierarchy-runtime.md](hierarchy-runtime.md). A source bound or component does not
prove a distinct live instance. Precise active selection remains UNKNOWN.

Sixteen whole-edge components each contain16 faces and18 distinct positions.
Their source extent is a region, not one plant. All16 components survive welding
sensitivity decimals3/4/5. No paired PC shrubtrig2 texture draw is found; broader
foliage/reference searches do not prove family absence. Material treeblend and
alpha-test tokens are authored facts; their complete foliage vertex semantics
are deferred. SOURCE_MESH_GROUP and GEOMETRIC_COMPONENT are confirmed;16 shrubs,
independent transform instances and current visible population are UNKNOWN.

Original exact-world comparison: 0/256 triangles at0.001;
identity coordinates independently anchored by GEOM1, without registration fit.
PC DX: `DataGx\Course\Turkey3\turkey3.dx`, SHA256 `724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8`.
The complete paired DX is searched, then same-family draw geometry is inspected
separately; broader standalone/TXT/XML scope is in [pc-counterpart-search.md](pc-counterpart-search.md).

Evidence: source binding CONFIRMED_BY_BYTES; source-to-runtime hierarchy
CONFIRMED_BY_BOTH; fitted geometry relations STATIC_INFERENCE; live rendering
UNKNOWN. Comparable instance count UNKNOWN. Future implementation NOT_READY.
