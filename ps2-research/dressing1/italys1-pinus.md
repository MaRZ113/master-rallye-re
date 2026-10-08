# italys1-pinus case card

Source: `\TNG\DATAPSM\COURSE\ITALY_S1\ITALY_S1.PSM`.
Decoded SHA256: `f74854a0789c1d3bb416cef8d70a02c65141a2d7afc5a150068c047b94bc30a0`.
Node byte offset: 3706566; material bytes at 3706622.
Material: `bush $alphatest() $shader(tree) $mip(1.0) $clamp(v)`.
Texture slots: `['Course\\Italy_S1\\pinus2-tga', 'Null', 'Null']`. Serialized flags: `[True, True, True, True]`;
opaque mesh word is retained as `0x3d064c45` and never treated as a transform.

```text
tag1 @ 3618036 (root) -> tag6 @ 3618044 (root.0) -> tag5 @ 3705466 (root.0.32) -> tag2 @ 3706566 (root.0.32.5)
```

One material mesh owns 5 source strips and 64 faces.
Bounds X -1219.896851..-926.994446;
Y -43.444035..26.185669;
Z -74.782951..219.225037, in game source coordinates.
Decomposition: source_index=28, coordinate_vertex=3, coordinate_edge=4. Full-edge component bounds and stable source IDs
are in [novel-candidates.json](novel-candidates.json).

The tag5 parent contains 16 material meshes of several
families. No matrix payload or independent object carrier belongs to this leaf.
Runtime tag6 child selection and inserted bound gates are documented in
[hierarchy-runtime.md](hierarchy-runtime.md). A source bound or component does not
prove a distinct live instance. Precise active selection remains UNKNOWN.

Whole-edge components have9/38/16/1 faces; vertex welding produces three
groups. Some source components span approximately169-200 source units and the
group extends below the surrounding nominal surface heights. Such source fields
cannot safely be called four normal-sized trees. The authored shader(tree)
consumer's final vertex/camera interpretation remains UNKNOWN. PC has28 pinus2
texture-bearing compiled draws, with trees shader(tree)/shader(object) material
candidates. Exact world triangles do not match, but the image family is present.
No extra placed-pine population or straightforward geometry-port readiness is
claimed. Foliage renderer semantics are the high-value next dependency.

Original exact-world comparison: 0/64 triangles at0.001;
identity coordinates independently anchored by GEOM1, without registration fit.
PC DX: `DataGx\Course\Italy_S1\italy_s1.dx`, SHA256 `5cd86704667cbdc95d4a3b1ff1444c885431fcdd0313cc0f15eca980e3965e8a`.
The complete paired DX is searched, then same-family draw geometry is inspected
separately; broader standalone/TXT/XML scope is in [pc-counterpart-search.md](pc-counterpart-search.md).

Evidence: source binding CONFIRMED_BY_BYTES; source-to-runtime hierarchy
CONFIRMED_BY_BOTH; fitted geometry relations STATIC_INFERENCE; live rendering
UNKNOWN. Comparable instance count UNKNOWN. Future implementation NOT_READY.
