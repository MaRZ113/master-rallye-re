# Legacy DX writer v1 analysis

## Experiment

The legacy DX -> OBJ exporter and v1 OBJ -> DX template injector were run on
external `Astero/complete.dx` (141,485 bytes, 2,657 vertices, 2,423 triangles,
24 tag-2 draws). All outputs stayed under ignored `.research-output/r2_5`.
The modern parser then compared geometry, topology, draw metadata, texture
slots, global tables, trailing data, and raw byte ranges.

Machine-readable evidence is in
`research/r2_5/legacy-dx-experiments.json`.

## Results

| Experiment | Modern parse | Modern validation | Byte result |
|---|---|---|---|
| v1 default zero-edit | PASS | PASS | 338 bytes differ; UV float bits and trailing/footer bytes changed |
| v1 `--positions-only --no-bounds` zero-edit | PASS | PASS | **byte-identical**, matching SHA-256 |
| v1 positions-only, vertex 0 X + 0.125 | PASS | PASS | one byte differs at absolute offset `0x12`; all other bytes identical |

The controlled edit changed source position 0 X from
`-0.9168009161949158` to `-0.7918009161949158`. Positions-only/no-bounds
preserved colors, normals, every UV, local and global indices, draw records,
tag hierarchy, texture strings, and trailing bytes exactly.

The default mode is not a safe bit-preserving baseline: textual OBJ UV
round-trip changes float bits, and its bounds updater treats the tail as a
40-byte footer while the modern format map recognizes the complete resource's
56-byte structure.

## Safe serialization principle

**HIGH confidence for same-topology template patching, not for general DX
writing:**

1. Start with the exact original DX bytes.
2. Parse and validate with the modern parser.
3. Require the original vertex count, topology, draw hierarchy, and source
   provenance to remain compatible.
4. Patch only explicitly authorized fixed-size fields (positions first).
5. Preserve colors, UVs, indices, draw records, strings, global tables, and
   unknown/trailing bytes byte-for-byte unless a later phase has evidence for
   changing them.
6. Reparse the produced file and require exact known-structure reconciliation.
7. Do not update the recognized 56-byte bounds structure until its field update
   policy is implemented and tested independently.

This is evidence for the planned R3.1 strategy. No production DX serializer or
Blender export-back operator is implemented in R2.5.
