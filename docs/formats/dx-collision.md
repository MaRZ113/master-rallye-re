# DX vehicle collision sections (Phase R4B)

This document maps the collision-section prefix after the stored global index
table in Master Rallye **vehicle** DX resources. It does not cover Course DX
or claim the runtime collision algorithm.

All values are little-endian. The canonical, bounds-checked implementation is
`src/master_rallye/collision.py`. It is read-only: R4B adds no collision
writer.

## Evidence and boundary rule

Targeted reader/writer inspection established the call hierarchy and exact
serialization order:

- tag dispatch writes tag 101 through `FUN_0057cda0`;
- `FUN_0057cda0` writes a base geometry block, one float, then two calls to
  the same representation writer;
- `FUN_0057ce60` reads that exact sequence;
- `FUN_0057dbb0` / `FUN_0057dc80` write/read two counted integer lists for
  each face descriptor;
- the representation writer then serializes edge-face pairs, one counted edge
  loop per face, and one float per face.

The parser advances only through these counted structures. It does not search
for signatures or resynchronize heuristically. The resulting tag-101 end
offset lands exactly on optional tag 102 or on the separately preserved
remainder in every vehicle file.

## Tag 101 envelope

```text
u32 tag = 101
GeometryBlock base_geometry
f32 base_scalar
ConvexHullRepresentation representation_a
ConvexHullRepresentation representation_b
```

### GeometryBlock

```text
i32 vertex_count
i32 triangle_count
float32 vertices[vertex_count][3]
i32 triangles[triangle_count][3]
```

Counts must be non-negative and within safety limits. Every triangle index
must address the block's own vertex array. Every byte range is checked before
unpacking and every float must be finite in strict mode.

### ConvexHullRepresentation

```text
GeometryBlock geometry_a
GeometryBlock geometry_b

i32 referenced_vertex_count
i32 referenced_vertex_indices[referenced_vertex_count]

i32 edge_count
i32 edges[edge_count][2]

i32 face_count
FaceDescriptor face_descriptors[face_count]

i32 edge_face_adjacency[edge_count][2]

for each face:
    i32 face_loop_count
    i32 face_loop_edge_indices[face_loop_count]

float32 face_scalars[face_count]
```

`FaceDescriptor` is:

```text
i32 primary_count
i32 primary_vertex_indices[primary_count]
i32 secondary_count
i32 secondary_vertex_indices[secondary_count]
```

Primary and secondary descriptor lists index `geometry_a` vertices. Edge
pairs also index `geometry_a`; adjacency pairs index faces; per-face loops
index the edge table. The primary list is the polygon boundary used by the
stored area scalar. The exact purpose of the secondary list remains
**UNKNOWN**.

## Corpus semantics

Across 27 finite, non-empty tag-101 vehicle hulls:

- base geometry is one vertex and zero triangles;
- representation A `geometry_a` is an 8-vertex/12-triangle axis-aligned box;
- the base point is the box centre;
- `base_scalar` equals the maximum centre-to-box-corner distance within
  `2.1e-7`, supporting **bounding radius** at corpus-confirmed confidence;
- representation B `geometry_a` is a closed triangular manifold with Euler
  characteristic 2 and supporting-plane convexity;
- each face scalar equals the polygon area derived from the primary descriptor
  within `4.9e-7`.

Representation A is therefore a coarse AABB-related helper and representation
B is a detailed convex hull at **HIGH** confidence. The data does not support
calling them primal/dual structures, and it does not establish whether the
runtime uses GJK, SAT, or another collision algorithm.

Both representations normally contain a one-vertex/zero-triangle
`geometry_b`. Representation A's point equals its geometry-A arithmetic mean
and the base/AABB centre. Representation B's point equals its geometry-A
arithmetic mean in 27/27 finite hulls (maximum error `5.85e-8`). These are
therefore positional centroid/reference points for translation at
**CONFIRMED_BY_CORPUS** confidence; their deeper runtime purpose remains
**UNKNOWN**.

## Tags 100 and 102

- Tag 100 is dispatched as a distinct BSP-like family by the executable.
  Its payload length/schema is unresolved and it does not occur in the 78-file
  vehicle corpus. The parser identifies it and preserves the remaining bytes
  as raw data; it does not pretend to parse tag 100 as tag 101.
- Tag 102 has the exact observed wire form `u32 102, f32 value_0, f32
  value_1`. It occurs in 53 vehicle files; all observed values are
  approximately `(0.4, 0.2)`. Field semantics remain **UNKNOWN**.

## Corpus coverage and outlier

All 78 vehicle DX files parse. Tag 101 occurs in 28 resources: 26 `car.dx`,
`SeatBuggy/complete.dx`, and `megane/sus.dx`. Twenty-seven are finite and
fully validate.

`forklift/car.dx` is retained as a **STATIC_FORMAT_ONLY_OUTLIER**. Its exact
tag-101 structure consumes 108 bytes, but nine coordinate components are
non-finite: the base point and both representation `geometry_b` points. Its
two `geometry_a` blocks are empty. This is an asset anomaly, not evidence that
finite validation should be weakened.

The exact machine-readable evidence is in
`research/r4b/tag101-corpus.json`.

## Preservation and writer boundary

R3 position writing still patches only the leading render-position buffer.
R4B hashes the parsed tag-101 byte range and verifies it is unchanged after
every writer reparse. Corpus regression preserved 28/28 tag-101 hashes for
zero-edit and one-position tests.

R4C adds a canonical serializer and a translation-only template patcher:
28/28 tag-101 sections and full DX templates round-trip byte-identically, and
27/27 validated hulls pass in-memory translation. Only the five GeometryBlock
vertex families may change. Counts, topology, radius, areas, tag 102, and all
non-tag101 bytes remain unchanged. R4C translation was later confirmed by human runtime testing. R4G C1 also confirmed finite existing-tag101 per-axis scaling through widened wall contact with normal physics and damage. Arbitrary collision topology construction remains unsupported; see ../../research/r4g/runtime-results.md.
