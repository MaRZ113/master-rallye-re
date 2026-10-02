# R5V-F.2c Mercedes car tag101 collision validation

## Structural validation

The cooked retail car.dx contains authentic Mercedes tag101 collision data. Its 5668-byte tag parses without collision warnings or errors. The 44-byte marker-1339 suffix is recognized. The legacy Copy of Mercedes car.dx also has a 5668-byte tag101 payload. Both source and cooked tags serialize back to their original tag bytes on a zero-edit roundtrip.

All tag geometry and face floats are finite. Indices are in range. Representation A has 8 vertices and 12 triangles; representation B has 34 vertices and 64 triangles. In both revisions, triangle meshes are closed, every edge has two incident triangles, Euler characteristic is 2, and convex supporting-plane tests pass. The base point and scalar are exactly equal. The representation A geometry, representation B triangle indices, primary face descriptors, edges, edge-face adjacency and face loops are exact. Representation B vertices differ by at most 6.92e-6 source units; signed volume changes from 9.9713116585 to 9.9713123778, a delta of 7.20e-7. The coarse representation volume is exactly equal at 13.0241730001.

## Bounded difference from legacy

A strict non-float comparison finds 36 changed bytes, all inside secondary face-descriptor index lists. Masking these parsed secondary indices makes all remaining collision bytes equal after parsed float fields are masked. Representation A has 2 of 6 secondary tuples changed. Representation B has 14 of 40 changed. Every secondary list remains a subset of its face's unchanged primary list. Eight changed face tuples represent alternate three-of-four selections on the same four-vertex face; the rest preserve membership but change ordering.

The source tool deliberately classifies changed secondary descriptor semantics as unresolved. Their runtime meaning has not been established, so this report does not erase that uncertainty or claim full byte-level semantic equivalence. At the same time, the native output is not missing, malformed, non-finite, open, non-convex, or replaced by donor geometry. Its core convex-hull geometry and topology match the legacy Mercedes control.

## Gate

Tag101 structural integrity: PASS.
Core collision geometry/topology comparison: PASS within measured float drift.
Auxiliary secondary descriptor comparison: OPEN; 36-byte delta, meaning unresolved.
Zero-edit tag101 serializer: PASS for legacy and cooked payloads.

Keep final Mercedes asset acceptance and cache-only portability blocked until the secondary descriptor delta is accepted by a documented native-rebuild semantic rule or its meaning is resolved. Cook B may proceed as a separate reproducibility experiment; it cannot by itself explain these legacy differences.

Evidence is machine-readable in cook-a/validation.json under cook_a_followup.collision_followup.
