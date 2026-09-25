# Same-build 9.3.1 `$chull` to regenerated tag101

Source: read-only 9.3.1 Trooper `car.gxm` plus `Trooper.txt`; compiled oracle: two independent 9.3.1 runtime rebuilds of unchanged `car.gxm`, both SHA256 `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1`. The shared output is **BYTE_IDENTICAL** across rebuild-A/B.

The sidecar identifies `$chull(Trooper)` records 1911–1978 (68 records), whose indexed triples reference 36 distinct Vector C positions. Under `(x,y,z) → (x,z,-y)`, convex-hull enumeration finds 28 points; regenerated tag101 Representation B also contains 28 vertices and 52 triangles. Nearest-neighbor mapping is bijective, with maximum distance `6.677050543111643e-6` each direction. This is same-build source-to-original-cooker output evidence (**CONFIRMED_BY_CORPUS** plus **CONFIRMED_BY_BYTES**).

Tag101 Representation A has eight AABB-helper corners; its extrema differ from transformed source-hull extrema by at most about `1.19e-7`. Center-to-corner distance differs from stored base scalar `2.6045312881469727` by about `4.3e-8`. Of 68 source triangle triples, the compiled hull has 52, only 16 of which match source unordered triples after point mapping. The cooker retriangulates the hull rather than copying source triangles. Exact face/winding/plane rules and which source dependencies cause the `$chull` crash remain **UNKNOWN**. Marker-1339 also includes render geometry and is not attributed only to `$chull`.

This mapping establishes source provenance; it does not make source-only hull translation safe. The captured 8.4.1 candidate crashes inside convex-hull construction. Do not perform a second blind mutation. `$cylinder`→tag102 remains **UNKNOWN**; the current source/target association is described in `cylinder-to-tag102.md`.

Reproduce with `tools/scanner/r_demo2_chull_map.py` using the 9.3.1 source, sibling sidecar, and ignored `input/rebuild-A/car.dx`; report stays under ignored `.research-output/r-demo2/same-build-chull-map.json`.
