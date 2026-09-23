# R4C corpus translation validation

The complete vehicle corpus was processed read-only. Modified bytes existed
only in memory.

## Results

- Tag-101 resources: **28**.
- Structurally parsed: **28**.
- Source-validated finite hulls: **27**.
- Static-only outliers: **1** (`forklift/car.dx`).
- Tag-101 zero-edit byte-identical: **28/28**.
- Full-DX zero-edit byte-identical: **28/28**.
- Tiny-vector translation dry-run: **27/27 PASS**, **1 SKIPPED**, **0 FAIL**.
- Unexpected changed ranges: **0**.
- Visual geometry changed bytes: **0**.

Dry-run vector: `(0.001, -0.002, 0.003)` in source coordinates. Each result
was serialized, inserted into its original in-memory DX, fully reparsed, and
checked for topology, adjacency, radius, face-area, centroid, pairwise-distance,
AABB-shift, and non-tag101 byte invariants.

Forklift was still serialized exactly at zero edit but was not translated;
its nine known non-finite coordinates remain a validation failure.

Detailed per-resource results are in `tag101-writer-corpus.json` and
`tag101-writer-corpus.md`.
