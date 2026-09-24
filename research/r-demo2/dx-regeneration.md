# Demo 9.3.1 Trooper car.dx: original vs one runtime rebuild

The user supplied both binaries under ignored `.research-output/r-demo2/input/`. The read-only `master_rallye.demo_dx.compare_demo_dx` inspector keeps the demo draw grammar raw. Its full metadata report is ignored at `.research-output/r-demo2/car-original-vs-regenerated.json`.

| Field | Shipped original | Runtime regenerated |
|---|---|---|
| Size | 124,568 | 124,568 |
| SHA256 | `bf644c0530b3908789676564b4761cd670cc2bb187b084983d414bba458fa041` | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` |
| Header | `0xD00D`, 131, 1337, 2,310 vertices | identical |

- Positions: 2,310 changed vertices, 2,399 changed float components, max absolute delta `1.7881393432617188e-7`, RMS `4.88203053342647e-8`.
- Normals: 2,258 changed vertices, 2,309 components, max `5.960464477539063e-8`, RMS `2.5772920820328873e-8`.
- Colors, the single UV set, all 5,733 local indices, the 1,638-byte raw draw/material region, and all 5,733 global indices (22,940 bytes): byte-identical.
- Tag101: both have base geometry and A 8-vertex/12-triangle and B 28-vertex/52-triangle structures. Triangles, referenced indices, edges, primary descriptors, adjacency and face loops match. Vertex/face scalar floats drift slightly; base scalar is exactly `2.6045312881469727`. Secondary descriptor sequences differ on 4 A faces and 10 B faces. All 10 B changes preserve each face's secondary-index multiset; the 4 A changes do not. After masking proven float fields and the secondary-index value arrays, every other collision-trailer byte matches. Their semantics are unresolved, so equality of collision behavior is not yet proven.
- Marker-1339: center and maximum match; minimum Y differs by `7.450580596923828e-8`. Radius is `2.5821101665496826` versus `2.5821099281311035` (delta `2.384185791015625e-7`). These fields were evidently recomputed or otherwise generated differently; the exact cause is unknown.

**Interpretation:** the pair has stable major structure and topology with float-scale variation, but is **NOT BYTE-IDENTICAL**. The formal comparator verdict is `UNRESOLVED` because secondary tag101 descriptor lists differ; describing this as highly structurally equivalent is supported, but declaring full collision semantic equivalence is premature. The later two-run rebuild-A/B test was byte-identical and matches this regenerated DX; see `rebuild-determinism.md`. This demonstrates repeatability for the tested fixed source/runs, while the historical shipped-DX difference still has no established cause.
