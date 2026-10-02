# Complete model cook gate

## Required runtime evidence

The first runtime gate is one new loose file:

```text
research-output/r5v_f_2b/runtime-cook/DataGx/Vehicles/Mercedes/complete.dx
```

Before launch, the same directory must contain `complete.gxm` and no `complete.dx`.
Capture retail debug output showing the complete resource request, cache miss,
`Reading GXM`, `Making dx model`, `Saved cached model`, and `Loaded cached model`.
The file's creation time and hash must be recorded after exit. This excludes a
cache hit or a packaged old model as the cause of success.

The isolated retail archive index has no `DataGx/Vehicles/Mercedes/` members,
and no legacy Mercedes DX was copied into the loose runtime folder. The
complete model can therefore only come from a new loose cook or a runtime
failure. The source GXM and all its root historical DXT files are present.

## Cook A runtime result

The captured log proves a fresh retail cook. It reports a stale/missing cache,
reads the staged `vehicles\\mercedes\\complete.gxm`, builds
`vehicles\\mercedes\\complete`, saves the loose `complete.dx`, and reloads
it. The `complete.gxm` hash matches the source manifest. A preceding failed
empty-name resource request is unrelated; it is not counted as the Mercedes
cook. Full line references, hashes, and machine-readable parser evidence are
in `research-output/r5v_f_2b/cook-a/complete-cook-validation.md` and `.json`.

Output: 122,372 bytes, SHA-256
`ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b`.
The header reports revision 135 and 2,305 vertices. `parse_dx` and strict
`validate_existing_rev135` both accept it. It contains 2,096 triangles across
18 draw records; geometry arrays are finite and index coverage is complete.

The 56-byte recognized footer stores bounds matching vertex bounds exactly.
The collision parser accepts tag 102 and the 44-byte marker-1339 tail with no
warnings or errors. The DX has 20 unique non-null texture references; all have
staged DXT files and all 20 appear in the retail texture-load log. The source
description has 22 material records and 25 texture names; five of those names
are not referenced by this `complete` role. The rev127 DX draw table declares
18 records in a 1,342-byte region; a bounded scan consumed the whole region,
found all 18 terminal words equal to zero, and matched all 18 draw-core fields
and texture-slot tuples by index against rev135. The 22 source description
materials are not assumed to correspond one-to-one with those DX draw records.

Semantic comparison uses demo-8.4.1 `Copy of Mercedes/complete.dx` rev127:
2,305 vertices, 6,288 indices / 2,096 triangles, and exact AABB match. The
local and global index sequences match exactly, as do normals and UVs. Position
drift affects 32 components, maximum `1.42e-14`. Thirty of 9,220 vertex-color
bytes change by one code (`178→179`) across the RGB channels of ten vertices;
alpha is unchanged; the exact cause of this small drift is not independently
established. No topology, bounds, or texture dependency discrepancy was found.

## Next gate

The complete-only validation passed, so the isolated car/wheel cook is now
authorized. Before its offline Practice or Quick Race trigger, verify
`car.gxm` and `wheel.gxm` are present and both DX caches are absent. Exit once
both caches have been written. Then require revision 135, strict modern parser
PASS, finite geometry, valid draw/material and texture dependencies, and a
valid footer for each. Compare the geometry and collision semantics to the
matching rev127 legacy role before interpreting gameplay.

`car.dx` and `wheel.dx` are still absent, while both GXM files are staged.
Capture the separate car and wheel GXM-read/build/save log messages, exit once
both files are written, and validate each output before any gameplay
interpretation. This is not the full R5V-F.2b pass.
