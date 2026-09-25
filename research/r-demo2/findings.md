# R-DEMO2 cooker/cache and original-cooker oracle

## Status

**R-DEMO2.1 PASS for its trace/oracle scope; R-DEMO2.2 bounded collision oracle complete; R-DEMO2.4 hierarchy retained; R-DEMO2.5 PASS for bounded 9.3.1 pre-hull provenance (Path B).** The crash instruction remains unknown. Dedicated demo branch only; R5T unstarted.

## Runtime traces

- Demo 8.4.1 DebugView captured the OutputDebugString channel and normal Trooper cooker stage order. The `$chull` test ends after `Building convex hull -`; the stage is incomplete and this is **CRASHED_IN_RUNTIME**, localized inside hull build (**CONFIRMED_BY_RUNTIME_TRACE**).
- Demo 9.3.1 DebugView: **NO_OUTPUT_OBSERVED**. Logger removal remains **UNKNOWN**.
- Five real ProcMon exports parse and classify by file events, independent of their names: DX cache miss/build, source-missing compiled fallback, stale-cache rebuild, fresh-cache hit, and GXI→DXT miss. Tested source/cache LastWriteTime orderings select rebuild vs direct load (**CONFIRMED_BY_CONTROLLED_RUNTIME_TRACE**). Both missing and equal timestamps remain **UNKNOWN**.
- The separate 8-byte DX probe reads offset 0/4 and compares magic `0xD00D` and version `131` in the 9.3.1 reader (**CONFIRMED_BY_RUNTIME_TRACE + CONFIRMED_BY_EXE**).
- DX writer/reload IO traversals match 7,494/7,494 pairs; DXT matches 261/261. This supports mirrored serialization/deserialization traversal, not internal function identity.

## Original cooker oracle

- Unchanged-GXM 9.3.1 rebuild-A/B are byte-identical (124,568 bytes; SHA256 `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1`), while historical shipped DX differs. The same-build cooker is deterministic for these runs, not asserted universally.
- A safe Vector C `+0.15` visible-body source edit maps to one DX render vertex and recomputes marker-1339 bounds. Normals, tag101, topology and draw/index fields remain unchanged. User confirmed DX-only loading and the visible edit (**CONFIRMED_BY_RUNTIME**).
- Same-build `$chull` points map bijectively to regenerated tag101 B vertices; source triangles are retriangulated. This establishes provenance, not a safe hull-edit recipe.
- `$cylinder` to tag102 remains **UNKNOWN**. The current source/target association lacks a generated-output or controlled directive differential.

## Collision cooker semantics (R-DEMO2.2 current)

- Four 9.3.1 `$chull` cohorts show a bijective extreme Vector-C→tag101 Rep-B mapping under `(x,y,z) → (x,z,-y)`. Trooper uses a byte-identical runtime rebuild; Jump/NewRav/Tata remain shipped-DX controls.
- Tag101 stores polygon loops/adjacency alongside a triangulated view; direct source triangle overlap is sparse. Rep-A extrema and base scalar reproduce from the tested hull; marker-1339 requires render plus Rep-B points within at most one float32 ULP.
- R-DEMO2.5 establishes **Path B for the pinned 9.3.1 Trooper offline pair**: all 36 hull positions are isolated from the global welder, so 68 triangles / 204 corners retain their indices and translate uniformly (maximum residual `3.26e-8`). `FUN_005c9990/FUN_005ca370` are post-hull 2D processing and cannot explain the earlier crash. No new runtime mutation was made; see `vertex-welder.md` and `vertex-welder.json`. The actual fault instruction and the 8.4.1 post-weld stream remain unknown.

See `collision-cooker.md` for full cohort hashes, mappings, Vector A/B tests, area/topology records, bounds measurements and offline checker output.

## Runtime evolution

- 8.4.1: source-first, tested model path logs `Caching disabled`, reads GXM and cooks in memory; OutputDebugString stage trace active.
- 9.3.1: source plus persistent compiled cache; missing/stale DX is generated or overwritten and reloaded. Newer DX loads with metadata-only source check. GXI can generate persistent DXT.
- Retail: tested vehicle path does not consume demo GXM as a live model source; renaming it to DX does not produce a valid compiled body. No claim that all development code was removed.

See `model-cache-state-machine.md`, `runtime/`, `dx-regeneration.md`, `source-edit-oracle.md`, `gxm-to-tag101.md`, and `r4g-impact.md`. No broad ProcMon cache archaeology is needed for this state machine.

## Roadmap

R-DEMO2.5 rejects pre-hull hierarchy/welder incompleteness for the tested 9.3.1 offline analogue. The first bounded hull probe preserves all 7,140 triple classifications at the initial EXE plane thickness. Next, if requested: one narrow hull-library follow-up at the `005fc680` plane-equivalence transition, with actual configured thickness and crash address. This is a follow-up target, not a proven fault site. No repeated hull mutation, course/track archaeology, merge or push. R4G remains frozen.

## R-DEMO2.6 exact 8.4.1 hull NULL provenance

**Level C achieved; source-level failure condition remains OPEN.** Exact 8.4.1 EXE SHA256 `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be` identifies `005C3200` as an edge endpoint-overlap predicate. `005C447B` selects literal zero when the face edge-list search finds no edge sharing a vertex-object pointer; `005BC490` writes that zero into a local list-node payload `+8`, which a later iteration passes to `005C3200` and dereferences at `005C3212`. The candidate crash and baseline non-trigger are **user-reported runtime evidence**; exact writer/CFG are **CONFIRMED_BY_EXE**, while the first differing face/endpoint set is **UNKNOWN**. The pinned 8.4.1 GXM candidate changes only 126 bytes of the 36 hull source-X positions and preserves source records/hierarchy/A/B. Its absolute-space bounds and plane offsets change; no specific stale dependent field is proven. See `r-demo2.6-hull-null-provenance.md`, `r-demo2.6-structure-map.md`, and the single read-only `r-demo2.6-runtime-followup.md`.

This supersedes the older statement above that the crash instruction was unknown. No hull repair rule or new R4G writable-collision guarantee follows yet.
