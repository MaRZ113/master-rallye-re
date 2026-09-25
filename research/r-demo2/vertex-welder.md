# R-DEMO2.5 — Pre-hull vertex welder and runtime mesh provenance

## Result and identity

**Path B for the pinned demo-9.3.1 Trooper baseline and its existing offline +0.4-X analogue. PRE-HULL HIERARCHY/WELDER INCOMPLETENESS REJECTED for this pair.** All 36 selected positions are isolated from every other global C position by more than the weld tolerance. Therefore they cannot be a source or destination of a weld, under any sort axis/order or guard outcome. This is an exact no-write control-flow proof; it does not require inventing non-hull weld representatives.

**R-DEMO2.5 PASS for this bounded pre-hull investigation.** The crash instruction remains **UNKNOWN**. This is not a runtime-safety claim and does not establish the same result for 8.4.1. No new candidate or runtime mutation was made.

| Input | SHA256 |
|---|---|
| 9.3.1 `MRallye.exe` | `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680` |
| 9.3.1 Trooper `car.gxm` | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` |
| Existing 9.3.1 offline +0.4-X GXM | `32fcbc212f226a307a3d71c43c3cbedabcf32526f86961a3bd1af16ad3c1aac4` |
| Historical traced 8.4.1 crash candidate, **different asset** | `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699` |

Worktree: `master-rallye-re-rdemo`, branch `research/r-demo-pipeline`, baseline commit `de1d157`. Baseline: **140 synthetic tests PASS**. README already contained staged user changes, retained separately from this phase's commit. All source corpus reads were immutable; raw decompilation and coordinate streams stay in ignored `.research-output/r-demo2/`.

## Correct cooker order

`FUN_005430c0` calls sort-plane insertion at `00543126`, welder at `00543269`, hull at `005432aa`, then BSP, cylinder and 2D processing at `005433ad`.

```text
005cab00 -> 005ca990 -> 005de630 -> 005df370 -> hull library
                                            then BSP / cylinder
                                            then 005c98d0 -> 005c9990 -> 005ca370
```

**CONFIRMED_BY_EXE.** The R-DEMO2.4 attribution of a pre-hull rewrite to `005c9990/005ca370` was incorrect. Their pair-processing/range-rewrite observation remains a finding about later 2D geometry only. The 8.4.1 runtime trace still establishes **CRASH_DURING_CONVEX_HULL_BUILD / CONFIRMED_BY_RUNTIME_TRACE**; it does not identify a failing 9.3.1 instruction.

## Loader and actual record provenance

**CONFIRMED_BY_BYTES + CONFIRMED_BY_EXE:** GXM header `0x00020702` is type 2, version 7, two root children. `005bea30` reads that header and dispatches the model reader `005bdf40`, then the name and two children. Thus the top-level root count is no longer merely inferred from tail EOF. The existing bounded tail parser still reads to its boundary; the oracle separately verifies the header count.

`005bdf40` populates model `+0x34` (global 0x34-byte records) and `+0x38` (global float3 C positions). `005be940` reads a native record as 12 + 4 + 12 + 12 + 12 bytes. The earlier parser's `record_offset` names the material word, **12 bytes into the native record**, after the leading sentinel triplet. Consequently raw parser words 4/5/6, at material-relative +16/+20/+24, are the same bytes as native record +0x1c/+0x20/+0x24. This is a boundary convention, not an additional index permutation or allocation.

C vectors are read by `005be870`, then rotated by `005b64d0(-90)` before the cooker. It uses the binary32 constant `0x3c8efa35` at `006504b8`, stores sine/cosine as binary32, and writes `(x, y*cos-z*sin, z*cos+y*sin)` as binary32. The ideal convention is `(x,z,-y)`; the executable's cosine is not exactly zero. X remains unchanged. The optional auxiliary arrays are absent in this Trooper header.

| Field | Pre-weld | Post-weld / pre-hull |
|---|---|---|
| Hull node start / count | 1911 / 68 | 1911 / 68 |
| Global record count | 1979 | 1979 |
| Record vector / data | model+0x34 / vector+4 | Same pointers, no replacement |
| C vector / data | model+0x38 / vector+4 | Same pointers, in-place coordinate writes possible globally |
| C position count | 1353 | 1353, no compaction |
| Hull C indices | 1317..1352 | Same 36 indices |
| Collector | record +0x1c/+0x20/+0x24 | Same indices into same position storage |
| Hull coordinates | loader-rotated C | Unchanged by welder for this pair |

Native pointer values were not captured; the table records pointer **identity/data flow**, not fabricated addresses. The hull leaf has no children, so `005df370` emits exactly the 68 records in range order, three corners per record.

## FUN_005ca990 semantics

The wrapper receives the **model data object**, not a selected hull node. Constructor `005ca960` sets scale=1, scale-enabled=0, tolerance=0.01f, weld-enabled=0. The caller writes tolerance bits `0x3c23d70a` and weld-enabled=1. The independent scaler `005ca9e0` stays disabled.

Active chain: `005ca990 -> 005ce590 -> 005ceac0 -> 005cec00`.

- `005ce590` enumerates **every global C position**, without node type, material, name or `$chull` filtering. It allocates temporary 16-byte coordinate/index entries, a pair list and later a per-position written bitmap. These are scratch allocations, not replacement model arrays.
- `005ce7a0` selects one of three axes by extent comparisons. Its assembly reads six stack extrema without initializing them in the function. The observed stack contents / selected axis are **UNKNOWN**. This is not promoted to a crash cause.
- `005cfa70` partitions on the primary coordinate (median-of-three pivot, cutoff 16); `005d00a0` and the caller complete insertion sorting. Equal-coordinate order is not a promise of original-index order. No lowest-index or union-find representative rule is justified.
- `005ceac0` scans earlier/later sorted entries. It stops a later scan when `abs(primary_delta) >= tolerance`. A pair is queued only when **squared Euclidean distance < tolerance squared**, both strict comparisons. The actual tolerance is `0.009999999776482582`. The pair means **later original index <- earlier original index**. Pair selection uses the pre-write coordinate snapshot.
- `005cec00` applies pairs in queue order. A destination already successfully written is skipped. It gathers **all global records** referencing that destination, without per-node filtering.
- `005cf0c0` vetoes if any such record already references the proposed source index. `005cf110` substitutes indices in a scratch record only and vetoes a negative old/new geometric-normal dot product. `005cf220` computes normals from current C positions; squared cross magnitude must exceed `2^-23` to normalize, otherwise it yields zero. A zero-normal dot of zero is not a guaranteed degeneracy veto.
- If both guards permit, it copies three current float words from source position to destination position and marks the destination written. The source itself may already have been copied earlier. **It never writes the model's C indices, mesh ranges, counts, winding, node links or position-buffer pointers.** Position coincidence changes effective geometry without changing index identity.

Evidence-backed pseudocode (not a general optimizer):

```text
snapshot = all_global_C_positions_with_original_ids
order = native_axis_sort(snapshot)
pairs = []
for earlier in order:
    for later after earlier, while primary_distance < 0.01f:
        if squared_distance(snapshot[earlier], snapshot[later]) < (0.01f)^2:
            pairs.append(destination=later.id, source=earlier.id)
for destination, source in pairs:
    if destination_already_written: continue
    affected = all_global_records_referencing(destination)
    if any_record_already_references(affected, source): continue
    if any_old_new_normal_dot_is_negative(affected, destination, source): continue
    C[destination] = C[source]  # current coordinates, not snapshot coordinates
    destination_already_written = true
```

Proximity is non-transitive and the guards are order-sensitive. A proximity connected component is **not** automatically a welded equivalence class.

## Other pre-hull stages

`005cab00` collects `$sortplane` nodes and calls `005cabc0` only for matches. That callee expects a two-triangle plane and `$side_plus_` / `$side_minus_` children, builds a replacement plane node and rewires children. It can change which mesh/hierarchy the collector reaches for other inputs. **Trooper has zero matches**, so the mutating callee is not entered; this excludes it for both pinned files, not for all GXM.

The preceding node-removal calls (`$limits`, `$raceline`, `startpoint`) also have zero matches. The optional `\car` / `\complete` name branch calls `005ec020`: it appends color float4 values to model+0x20 and changes internal record color-index words +0/+4/+8. Its geometry reads use A indices +0x28 onward; C positions and C indices are not written. Even if the runtime model name has become the filename, that branch does not change this hull input.

## Bounded offline reproduction and fail-closed gate

`src/master_rallye/vertex_welder.py` and `tools/scanner/r_demo_vertex_weld_oracle.py` reconstruct the **selected hull projection**. They prove no candidate pair can touch any selected index, using every global position, a conservative `1e-6` margin around the native tolerance, and both wide and single-intermediate loader arithmetic. This avoids guessing the unobserved native axis/tie order while producing exact singleton representatives for the required hull. It does **not** claim to reproduce weld classes of the other 1,317 positions or their possibly order-dependent render effects.

A near neighbour, unhandled pre-hull node, unknown model/header, changed non-C bytes, external use of selected raw indices, or incomplete proof prevents Path B. No unions or guessed representative coordinates are returned for unresolved selections. Synthetic completed-map comparisons exercise A/B/U classification; the corpus scanner itself only certifies this isolated domain.

The mathematical no-write proof is independent of floating-point control state. Published coordinate streams are **REPRODUCED_OFFLINE**, not byte-exact native memory dumps: the loader's actual x87 control word was not captured. Wide and single-intermediate variants both pass with ample isolation margins, and the source X translation leaves each variant's Y/Z calculations identical between inputs. Neither variant is represented as a controlled runtime observation.

## Baseline versus existing candidate

| Measurement | Baseline | Old +0.4-X analogue |
|---|---:|---:|
| Global position slots, before -> after | 1353 -> 1353 | 1353 -> 1353 |
| Selected positions / singleton weld classes | 36 / 36 | 36 / 36 |
| Hull-to-hull welds | 0 | 0 |
| Hull-to-external welds, either direction | 0 | 0 |
| Maximum hull merge distance | 0 | 0 |
| Nearest other global position after wide loader | 0.05888202730 | 0.05281336702 |
| Emitted triangles / corners | 68 / 204 | 68 / 204 |
| Unique emitted positions | 36 | 36 |
| Degenerate / duplicate triangles | 0 / 0 | 0 / 0 |

All old indices 1317..1352 map to themselves. No class changes, effective index changes, mixed unmoved dependency, or external record sharing that involves a hull representative occurs. Full per-index source/pre/post coordinates, representatives, node-level record use, ordered corner stream, bounds and centroids are in the ignored report. No weld affects a hull triangle. Whether other render nodes change due to native global sort order is outside this exact hull projection and remains unmeasured.

Expected runtime translation `(0.4,0,0)`, fitted corner-weighted translation `(0.400000003184758,0,0)`:

- maximum rigid-fit residual: **3.25780289e-8**;
- maximum residual against exactly +0.4: **3.57627868e-8**;
- maximum area change: **9.25095316e-8**;
- maximum unit-normal vector change: **3.15726e-7**;
- identical indexed topology, winding, adjacency, triangle count and unique-position count.

All 12 fail-closed checks pass in both arithmetic variants. Residuals are binary32 edit noise. **Path B**, no improved candidate is warranted. This rejects pre-hull remapping for the 9.3.1 analogue; it does not substitute that file for the differently hashed 8.4.1 runtime crash source.

## First hull-library consumers and translation mathematics

`005de630` allocates 204 points via `005f1200`, fills them through `005df370`, then calls `005f1310`. `005f21e0` is an identity accessor; `005f2200` copies constructed representations into the output. Neither is established as the faulting instruction.

The useful narrow chain inside `005f1310` is:

```text
005f2f00 -> 005f2fc0
    005f3190  ordered proximity suppression of double3 points
    005f3630  current AABB midpoint
    005f2fc0  twice max distance from that current midpoint
    005f37c0  enumerate point triples
        005fc2b0  construct/orient plane using current points and center
        005fc680  plane equivalence filter (next unresolved transition)
        005fca60  signed point-plane classification
    005f3b40 / 005f3f60 / 005f4290  later construction (not expanded here)
```

`005f3190` was checked in assembly: it keeps first occurrences when squared distance to every retained point is not below the squared plane-thickness setting. A decompiler erroneously collapses the temporary vector to zero; its apparent zero-count result is **not** executable evidence. The initial EXE thickness at `0067c6f0` is `0.0005000000237487257`, and `005f1310` can override it from configuration (`ConvexHull_PlaneThickness`); the crashing session's value is unknown.

`005f3630` recomputes midpoint `(min+max)/2` from current points. Its centered radius should remain constant under translation. `005fc2b0` constructs the normal from point differences, orients it against the current center, and stores **k = n dot p0**. `005fca60` tests `n dot p - k` against +/-thickness. Under translation, **k' = k + n dot t** (equivalently d' = d - n dot t for `n dot x + d = 0`). The inspected constructor recomputes k; stale source A normals or plane constants were not found in this chain.

`early_hull_probe` is a bounded binary64 mathematical probe, not an x87 emulator. At the initial EXE thickness, both loader variants produce:

- 204 corners -> 36 points, identical first-occurrence order;
- **7,140 triples** checked; **zero changed cross-length / signed-side classifications**;
- **74 supporting triples before plane-equivalence filtering** in each input (not the final face count);
- minimum epsilon-boundary margin approximately `4.09e-6` (wide variant);
- centered diameter `5.20318186489 -> 5.20318188629`, binary32 edit noise;
- maximum correctly translated fixed-normal plane residual `3.57560e-8`; reusing stale baseline constants would give `0.399924` residual.

Absolute origin radius changes `2.79727048202 -> 2.82710988749`, as expected, but the inspected early builder uses the recomputed center, so this is not evidence of an origin-radius bug. `005f1c40` later rebuilds AABB corners; `005f1e70/005f1f60` derive a point centroid and max distance from it. Their existence does not locate the crash.

**Next bounded target:** capture/compare accepted plane count and constants across `005fc680` in the first `005f37c0` pass, with the actual configured thickness and fault address. No failure is asserted in that function; it is the first untested transition of this probe. No debugger capture was performed in R-DEMO2.5, and no repeat of the unchanged hull mutation is requested. R5T remains unstarted.

## Reproduction and artifacts

```powershell
python tools/scanner/r_demo_vertex_weld_oracle.py --baseline "../corpora/demo-9.3.1/DataGx/Vehicles/Trooper/car.gxm" --candidate ".research-output/r-demo2/invariant-candidate/Trooper/car.gxm" --exe "../corpora/demo-9.3.1/MRallye.exe" --output ".research-output/r-demo2/pre-hull-weld/trooper-post-weld.json"
$env:PYTHONPATH='src'
python -m unittest discover -s tests/synthetic
```

- Ignored full coordinate/usage/stream report: `.research-output/r-demo2/pre-hull-weld/trooper-post-weld.json`.
- Tracked numerical/evidence summary: `vertex-welder.json` (no mesh arrays).
- Ignored static function exports: `.research-output/r-demo2/pre-hull-static/`.
- Synthetic regression tests: `tests/synthetic/test_vertex_welder.py`; existing exact/tolerance bijection tests are retained.

Stop at R-DEMO2.5. **ONE NARROW HULL-LIBRARY FOLLOW-UP**, only when requested.

## Validation closeout

Full synthetic suite: **163 tests PASS** (140 baseline + 23 new regressions). Existing exact/tolerance statuses remain `EXACT_BIJECTION` and `BIJECTION_WITHIN_TOLERANCE`. New tests cover strict float32 tolerance boundaries, non-transitive proximity, singleton classes and identity maps, deterministic selected representatives, external dependencies returning U, ordered corner emission, changed representatives/topology, degenerates, rigid translation, missing gates and A/B/U classification, plus early hull mathematics. Near-neighbour welding itself is deliberately not certified by this no-write oracle.

`git diff --check`, UTF-8 sanity and phase asset audit pass. Full coordinate streams, EXE decompilation and game resources are excluded from the phase commit. The overview update is committed without the pre-existing unrelated staged README edits.
