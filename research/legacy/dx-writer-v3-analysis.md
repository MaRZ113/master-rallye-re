# Legacy DX writer v3 analysis

## Experiment

Legacy v3 rebuilt `Astero/complete.dx` from the legacy export of the same
resource. The output retained the original size (141,485 bytes), 2,657
vertices, 2,423 triangles, 24 tag-2 records, texture tuples, and stored global
table. It differed in 8,832 bytes.

The modern parser reached a structural stopping point but validation **FAILED**.

## Modern validation failures

- 12 draw-range errors report local indices exceeding the declared inclusive
  local maximum; two reconstructed vertices exceed the 2,657-vertex buffer.
- Reconstructed and stored global tables differ at **6,285** covered index
  positions; the first mismatch is at table position `0x2`.
- The stored global table happens to remain equal to the template, while v3
  rebuilt different local indices. The two representations therefore disagree.
- v3 appends `vertex_base + local_index` without the proven triangle swap.
  The modern relationship is
  `(local[1] + base, local[0] + base, local[2] + base)`.
- v3 assumes a 40-byte footer. Modern corpus evidence recognizes a 56-byte
  bounds form on this resource and additional opaque families elsewhere.

## Disposition

**CONTRADICTED.** A visually plausible mesh and a parseable envelope are not
sufficient. The v3 topology/draw reconstruction logic must not be migrated or
used as a starting point for R3. Topology-changing serialization still
requires additional format research and explicit tag-2/7/8 hierarchy
construction rules.
