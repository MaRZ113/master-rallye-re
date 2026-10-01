# R5T-F.2 — tag100 physical grammar archaeology

## Status

**R5T-F.2 status: PASS, bounded.** The tag100 recursive wire structure and its plane-bearing record family are parsed read-only. The France1 source mesh's 12 distinct face planes match records inside the parsed tree in both source/cooked cohorts, and the `+20 X` translation follows the expected plane-distance equation. Runtime evidence remains bounded to the F.1 reciprocal suffix swap; the adjacent tag1400 block was not isolated by that test.

## Loader and wire layout

Retail rev135 SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

| Structure | Wire/allocation layout | Evidence |
|---|---|---|
| Header | 24 bytes: tag 100 + five little-endian uint32 values | `CONFIRMED_BY_EXECUTABLE` |
| Node prefix | 2 × uint32, then optional/list/child/sibling presence bytes | `CONFIRMED_BY_EXECUTABLE` |
| Optional record | 20 bytes: float32 × 4 + uint32 code | executable reader; source plane correlation |
| Optional list item | 20 bytes: float32 × 3 + float32 + uint32 | `CONFIRMED_BY_EXECUTABLE`; absent in this France1 pair |
| In-memory pools | two 8-byte allocation roles and one 36-byte role, chunked in groups of 0x400 | `CONFIRMED_BY_EXECUTABLE` |
| Links | recursive first-child / next-sibling serialization; one-byte bools | `CONFIRMED_BY_EXECUTABLE` |

Neutral role names are used because the two leading node fields and the uint32 record code have not been assigned runtime meanings. The repository's existing `CollisionSections.bsp` field is historical naming; it preserves the tag100-starting suffix raw and is not evidence that this grammar is a BSP.

## France1 structural counts

| Measure | Baseline | Modified | Delta |
|---|---:|---:|---:|
| Tag100 tree bytes | 8,293,376 | 8,289,972 | -3,404 |
| Tree nodes | 360,581 | 360,433 | -148 |
| Plane-bearing records | 180,290 | 180,216 | -74 |
| Plane-less terminal records | 180,291 | 180,217 | -74 |
| Max tree depth | 30 | 30 | +0 |
| Optional list items | 0 | 0 | +0 |

All decoded plane-bearing records have a first-three-component vector whose length is within `4.77e-08` of 1.0 in this pair. All pool8 nodes are plane-less terminals; pool36 nodes carry the 20-byte optional record and children. This supports a plane-bearing hierarchy, while link-side and full spatial semantics remain unknown.

## Source geometry binding

`COLLIDE_finishline03` has 24 source triangles and 12 distinct plane equations. All 12 plane groups match optional float4/code records in both tag100 trees within normal max-component 1e-05 and `d` 0.001 tolerances.

For `n·p + d = 0`, translation by `T=(20,0,0)` requires `d' = d - dot(n,T)`. Stable code-keyed records meet this relation with maximum residual `4.14371e-05`. Several planes have repeated copies at different tree offsets, so there is not a one-to-one mapping from 24 source triangles to 24 compiled records. The observed source/code numeric relation is recorded in the JSON; the code's actual meaning remains unknown.

Baseline runtime AABB: `{"min":[-1472.298828125,63.67451858520508,352.06646728515625],"max":[-1471.231689453125,73.11727142333984,353.04193115234375]}`.
Modified runtime AABB: `{"min":[-1452.298828125,63.67451858520508,352.06646728515625],"max":[-1451.231689453125,73.11727142333984,353.04193115234375]}`. No target-specific AABB record was identified in the decoded tree fields.

## F.1 boundary clarification

The F.1 donor region begins with tag 100 and extends to EOF. This loader-guided parse ends the tag100 tree before a 44-byte tag1339 record and a separate tag1400 region. Baseline tag100 starts at `0x00476044`, tree ends/tag1339 begins at `0x00C5EC44`, and tag1400 begins at `0x00C5EC70`. Modified tag100 starts at `0x00478AA1`, tree ends/tag1339 begins at `0x00C60955`, and tag1400 begins at `0x00C60981`. The tag1339 record is byte-identical in baseline/modified files. The later tag1400 region has the same size and 64 changed byte positions in 47 ranges. Therefore the reciprocal runtime result proves that the tested physical state follows the selected tag100-starting suffix donor; the run did not isolate the tag100 tree bytes from the following tag1400 region. The geometry-bound plane records themselves are inside the parsed tag100 tree.

The tree shrinks by 3,404 bytes while the loader-pool memory estimate changes by 3,256 bytes. The remaining 148-byte difference is not assigned a cause; the serializer is variable-length and the node topology is rebuilt.

## Retail corpus

Structural parse: 36/36 courses; status `PASS`.

Full per-course hashes, header words, node counts, depth, pool roles, trailing bytes, and failures are in `tag100-layout.json`. This is parser coverage only, not physical runtime validation across the retail corpus.

## Limits

- `tag100` is not globally renamed to collision data or BSP.
- `$bsp -> tag100` remains unknown.
- No AABB/triangle writer, source writer, Blender overlay, or course authoring was added.
- The tag1400 region and any target-specific runtime node/leaf selection remain unresolved.
