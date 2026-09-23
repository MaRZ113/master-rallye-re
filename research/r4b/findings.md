# R4B findings

## Checkpoint

- **CONFIRMED structural:** tag 101 is parsed to an exact counted boundary as
  base GeometryBlock + float + two repeated representations.
- **CONFIRMED_BY_CORPUS:** its scalar is the representation-A bounding radius;
  per-face scalars are polygon areas.
- **HIGH:** representation A is an AABB helper and representation B is a
  detailed closed convex hull.
- **CONFIRMED structural:** tag 102 is a tag followed by two float32 values;
  semantics remain unknown.
- **UNKNOWN:** tag-100 BSP grammar, nested `geometry_b` point semantics,
  secondary face-list semantics, and runtime collision algorithm.

## Coverage

The canonical scanner parsed 78/78 vehicle DX resources. Tag distribution is
100/101/102 = 0/28/53. Twenty-seven tag-101 resources validate as finite
non-empty PC vehicle hulls. Forklift parses structurally but fails finite
validation in nine coordinate components and is explicitly classified as a
static-only asset outlier.

## SeatBuggy runtime/binary cross-check

`SeatBuggy/car.dx` and `SeatBuggy/complete.dx` contain byte-identical tag-101
sections (3,760 bytes), both with SHA-256
`ea8ddbde932c548fbb09a6557caecb077094843abf228c860b3c28733569d8eb`.
The human runtime experiment also found that substituting SeatBuggy
`complete.dx` into the race role retained collision and damage. This is strong
combined binary/runtime evidence that tag 101 is central to the vehicle
collision path. It does **not** prove that tag 101 is the only condition needed
for collision or damage activation.

No original asset bytes appear in the reports. Reports contain paths relative
to the vehicle root, counts, offsets, hashes, measurements, and validation
diagnostics only.

## Integration

`DxModel.collision` exposes the parsed sections independently from the legacy
generic trailing classification. The R3 writer hashes and compares tag 101;
all 28 tag-101 hashes remain identical under the full zero-edit and safe
one-position corpus regression.

The Blender add-on creates a separate read-only collision-helper collection.
It uses the established source-to-Blender coordinate transform and does not
merge collision vertices into editable render meshes. R3 export ignores these
helpers and continues to write render positions only.

## Decision gate

R4B is ready for review. The schema boundary and corpus behavior are strong
enough to justify **R4C — conservative template-preserving collision editing**
as the next phase, beginning with zero-edit and rigid/same-topology patches.
R4B does not implement that writer and does not justify arbitrary collision
topology reconstruction.
