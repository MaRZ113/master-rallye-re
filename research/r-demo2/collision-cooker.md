# R-DEMO2.2 — collision cooker semantics

## Scope and provenance

This note compares 9.3.1 `car.gxm` `$chull` regions with tag101 from the same demo build. Original corpora remain read-only. The only runtime-regenerated DX in the cohort is Trooper `car.dx`, rebuilt twice from unchanged GXM (A/B are byte-identical). Jump, NewRav and Tata use same-build corpus-shipped DX; those are association controls, not proof of runtime regeneration. The raw pair inputs and expanded per-vertex/per-face measurements are under ignored `.research-output/r-demo2/same-build-collision-oracle/` and are not committed.

| Vehicle | GXM relative path | DX relative path | Provenance | `$chull` | Records | Extreme C → Rep-B | Rep-B faces | Max point error |
|---|---|---|---|---|---:|---:|---:|---:|
| Trooper | `DataGx/Vehicles/Trooper/car.gxm` | `input/rebuild-A/car.dx` | runtime-regenerated, two rebuilds byte-identical | `$chull(Trooper)` | 1911–1978 | 28 ↔ 28 | 52 | 6.67705054e-6 |
| Jump | `DataGx/Vehicles/Jump/car.gxm` | corpus `DataGx/Vehicles/Jump/car.dx` | corpus-shipped | `$chull(Jump)` | 1808–1871 | 26 ↔ 26 | 48 | 6.19429639e-7 |
| NewRav | `DataGx/Vehicles/NewRav/car.gxm` | corpus `DataGx/Vehicles/NewRav/car.dx` | corpus-shipped | `$chull(Nrav)` | 2029–2096 | 26 ↔ 26 | 48 | 1.13874514e-6 |
| Tata | `DataGx/Vehicles/Tata/car.gxm` | corpus `DataGx/Vehicles/Tata/car.dx` | corpus-shipped | `$chull(Tata)` | 1973–2004 | 18 ↔ 18 | 32 | 9.68460846e-7 |

Half-open GXM record intervals are `[1911,1979)`, `[1808,1872)`, `[2029,2097)`, and `[1973,2005)`. Every row is from 9.3.1; shipped DX rows remain explicitly distinct from regenerated output.

### Input hashes

The JSON files record full source, sidecar and compiled-DX SHA256 values, paths, index maps, every target face map, and every tested A-normal record. Key pairs:

| Vehicle | Source GXM SHA256 | Compiled DX SHA256 |
|---|---|---|
| Trooper | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` | `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1` |
| Jump | `55bd09e1f8c9c647c82381dba463bb555dfcc51c6b2d63b9e8e39c55231da17e` | `e92b9b093cfd62cb1dc2a9401b300e86b372ec5ea2df15a1d760c2faed5a771b` |
| NewRav | `fc8208f7e23db49b6d3452eaad95475edbb933ba2774ec02e721fd178464ca0a` | `959641244de3cddc83d062b32a5700ba33b1f80f1ca8168899b75456864cb67c` |
| Tata | `5db78fe87243ffae696a2b55fbd825f0f16182e32c8dce46942adabfce32dd0d` | `4cb609296e496db671c6e8ccaafa95119e16f4fff2fca78c08e2d71e0cfaa120` |

## Vector C → tag101 Representation B

The source-to-DX axis transform tested is `(x,y,z) → (x,z,-y)`, the same orientation-preserving permutation/sign transform used by the demo vehicle path. For each sample, the unique C positions referenced by the sidecar `$chull` record interval were reduced to the candidate extreme set; target Rep-B points were matched back to C indices by unique nearest point. Counts agree and every target vertex maps to a distinct source index. The mapping rows are explicit in each JSON report.

This is a bijection at the tested geometric tolerance, but it is not bit-exact float reproduction: Trooper, Jump and NewRav have zero exactly equal f32 tuples; Tata has 6/18. Maximum point residuals are shown above. No extra centering or translation is needed to explain the mapping at that tolerance. This is **CONFIRMED_BY_BYTES** for Trooper's same-build runtime rebuild and **CONFIRMED_BY_CORPUS** for the other shipped associations. It is strong source provenance, not a safe authoring recipe.

## Source records → Rep-B triangles

The compiler does not copy source `$chull` triangles one-for-one. Source record triples map to the target C-index triples. Unordered face overlaps are Trooper 16/52, Jump 10/48, NewRav 10/48 and Tata 9/32. Each overlapping target face has the same cyclic orientation as its matching source triple; no reversed match was found. Most target faces have no exact source-triangle set match, consistent with hull retriangulation. Per-target-face mapped C indices and matching source record IDs are in the JSON reports.

The corpus parser observes every Vector-B triple in these four `$chull` intervals as `FFFFFFFF FFFFFFFF FFFFFFFF`. That rejects a per-record Vector-B index dependency for these examples, but does not explain the meaning of the global Vector-B array or all possible hierarchy variants.

## Vector A

For every source face record, the geometric normal from its referenced C triple and the three referenced A vectors were transformed into the demo DX basis and compared. All 232 tested records are nondegenerate. Their signed dot products are positive; maximum angular error by sample is Trooper 7.934°, Jump 8.798°, NewRav 7.974°, Tata 18.889°. Trooper and NewRav have near-identical A vectors across each record's three corners (maximum pairwise distance 7.76e-8 and 8.56e-8 respectively); Jump and Tata have outlier records (0.09474 and 0.004604 maximum spread).

This supports Vector A as a face/plane-normal candidate in the tested hull records, especially Trooper and NewRav, but not an exact geometric-normal encoding. The corpus does not prove whether the builder consumes A: the demo 9.3.1 recursive hull-input collector directly copies indexed triangle positions, and its internal record offsets have not been mapped to serialized GXM words. Classification: **HIGH_CONFIDENCE_INFERENCE** for Trooper/NewRav source semantics; builder consumption remains **UNKNOWN**.

## Vector B

All four selected `$chull` intervals have sentinel B indices for every face. That makes per-face B points/offsets an implausible missing dependency in these samples. No numerical plane-point/centroid/support-point test is possible for a record with no B index. Global B-array meaning remains **UNKNOWN**.

## Demo 9.3.1 builder input and crash boundary

A fresh Ghidra 12.0.4 analysis was run on the exact demo 9.3.1 executable, SHA256 `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680`. The earlier Ghidra exports were retail and were not used. Relevant demo 9.3.1 functions:

- `FUN_005430c0` emits the compiler stages, configures the vertex welder tolerance field to float32 `0.01`, then invokes the hull stage.
- `FUN_005de630` locates a node whose name contains `$chull`, parses its extension, gathers counts from child nodes, allocates a point input, recursively invokes `FUN_005df370`, then calls the following hull-processing functions `FUN_005f1310`, `FUN_005f21e0` and `FUN_005f2200`.
- `FUN_005df370` walks the selected node's child chain recursively. For each internal mesh record it reads three indexed Vector3 positions and appends them to the hull input. It does not directly read internal A or B fields in this collector.

The last statement concerns post-loader object offsets, not proven serialized GXM word offsets. The GXM loader's array remapping and hierarchy transforms remain unmapped. Therefore the static result identifies the recursive object/triangle input path, but not a complete serialized source dependency list or the failing subroutine.

The 8.4.1 runtime trace confirms normal Trooper reaches `Building convex hull - done`; the C-only candidate reaches `Vertex welder - done`, starts `Building convex hull -`, and crashes before completion (**CONFIRMED_BY_RUNTIME_TRACE**). The analogous 9.3.1 test also crashed, but its DebugView result was `NO_OUTPUT_OBSERVED`.

A rigid translation of a complete triangle point set preserves its internal shape and the tested A normals. Thus the crash cannot yet be assigned to an inherent changed hull shape. The static recursion means a `$chull` node can feed triangles from descendants, while current sidecar spans identify a serialized record range; no evidence yet proves those sets coincide one-to-one or that the candidate translated every descendant input and alias consistently. That subset/hierarchy mismatch is a plausible structural explanation, **not a confirmed cause**. No evidence-driven second runtime mutation was prepared or attempted.

## Representation A and base scalar

Rep-A contains eight corners. Its bounds reproduce the transformed extreme-C bounds within at most approximately `1.2e-7` across the cohort; Rep-B bounds have the same hull extrema. For all four samples, converting the maximum distance from `tag101.base_geometry.vertices[0]` to an Rep-A corner to float32 reproduces the stored base scalar exactly. This confirms the tested baseline rule as **CONFIRMED_BY_CORPUS**; it does not yet establish whether another source set participates for other model classes.

## Marker 1339

For each compiled sample the report tested marker-1339 against render positions alone, Rep-B alone, and their union using the existing R4G bounds routine. Neither render-only nor B-only reproduces the stored block. Render+Rep-B reproduces all fields exactly for Jump; NewRav and Tata differ only in radius by one float32 ULP (`2.3841858e-7`); Trooper center/radius differ by at most one ULP and extrema by at most one ULP. This supports a render-plus-collision point set for the marker (**CONFIRMED_BY_CORPUS**), consistent with the controlled visible GXM edit which caused marker recomputation. It does not show that a `$chull` edit alone changes the marker in the original cooker.

## `$cylinder` → tag102

No new cylinder mutation was run. Existing same-build evidence associates `$cylinder_0.766_0.39/40/41/42` in `complete.gxm` and one matching directive in `wheel.gxm` with tag102 `(0.40000000596, 0.20000000298)`, but does not identify which directive contributes which field. See `cylinder-to-tag102.md`; semantics remain **UNKNOWN**.

## Reproduction

Run from the repo root with its `src` and root on `PYTHONPATH`:

```powershell
py -3 tools/scanner/r_demo_collision_oracle.py `
  --gxm <read-only-9.3.1-vehicle-car.gxm> `
  --sidecar <matching-car.txt> `
  --compiled-dx <same-build-car.dx> `
  --dx-provenance runtime-regenerated `
  --directive '$chull(Trooper)' `
  --output .research-output/r-demo2/same-build-collision-oracle/trooper.json
```

Use `--dx-provenance corpus-shipped` for shipped controls. The required choice is preserved in output so a shipped file is never silently described as regenerated. The tool writes only JSON beneath ignored `.research-output/r-demo2`.

### Triangle records, polygon faces and material fields

The parsed tag101 Rep-B stores triangulated geometry plus polygon structures. Its face-loop table indexes edge IDs, not point IDs; the analyzer reconstructs each ordered vertex loop through the edge table. The four compiled hulls have the following counts:

| Vehicle | Source C ids → extreme ids | Rep-B edges | Polygon descriptors / loops / scalars | Rep-B triangles | Maximum polygon-area vs stored scalar error |
|---|---:|---:|---:|---:|---:|
| Trooper | 36 → 28 | 67 | 41 | 52 | 1.15e-7 |
| Jump | 34 → 26 | 61 | 37 | 48 | 1.68e-7 |
| NewRav | 36 → 26 | 62 | 38 | 48 | 1.98e-7 |
| Tata | 18 → 18 | 40 | 24 | 32 | 1.32e-7 |

For every compiled polygon, the ordered loop reconstructed from indexed edges has an area matching its stored face scalar within the maximum error above (**CONFIRMED_BY_CORPUS**, matching the known tag101 area interpretation). `V - E + F = 2` for each convex structure. Thus the compiled output has polygon-level adjacency/loop data and a triangulated geometry view; those are not one face per source GXM record.

Every source record in all four hull ranges has material field `FFFFFFFF`, has Vector-B triplet `FFFFFFFF`, and the selected ranges contain no duplicate unordered source triangles. Of 68 Trooper source records, only 26 have all three C vertices within one compiled polygon's extreme-vertex loop; analogous counts are Jump 24/64, NewRav 22/68, Tata 19/32. No record is assigned to two polygon loops by this strict vertex-subset test. The remaining records use non-extreme source points or otherwise need loader-level source-to-polygon mapping; do not describe those as mapped. At the triangle-set level, direct overlap counts remain the stricter 16/52, 10/48, 10/48 and 9/32 figures above.

## Offline invariant checker and second mutation gate

`tools/scanner/r_demo_hull_invariants.py` compares a baseline GXM with an offline candidate and fails closed unless the selected flat `$chull` range has the same record topology, all and only its referenced Vector-C points undergo one translation, no selected C index is shared by records outside that range, Vector A/B and all non-C bytes remain unchanged, and every source face stays nondegenerate with area/normal drift bounded to float32 noise.

A scratch-only 9.3.1 Trooper copy translating all 36 referenced C positions by +0.4 source X passes all eight checks. Candidate SHA256: `32fcbc212f226a307a3d71c43c3cbedabcf32526f86961a3bd1af16ad3c1aac4` (no runtime launch was made). It changes 126 byte values, has maximum translation residual `3.27e-8`, zero degenerate records, maximum normal angular drift `1.81e-5°`, and maximum triangle-area drift `9.250953e-8`. The generated JSON is ignored under `.research-output/r-demo2/same-build-collision-oracle/`.

This positive offline result narrows the crash: within the sidecar's flat 68-record/36-C-index interval, the candidate preserves topology and rigid geometry, and those C indices are not shared by outside GXM records. Yet the prior runtime candidate crashes. Therefore the flat serialized hull invariants checked here do not explain the crash. Static code separately shows the cooker consumes a recursive node-and-descendant mesh stream. Whether the runtime candidate omitted another descendant, encountered a loader/hierarchy remapping, or failed later hull validation is still unknown. The checker expressly does not establish runtime safety and is not an authorization to run a candidate.

No second `$chull` runtime mutation was attempted. The required narrow next step is to map the GXM hierarchy/loader output that feeds the recursive builder, then prove whether the runtime-edited 68 records span that entire input before preparing one coherent mutation.
