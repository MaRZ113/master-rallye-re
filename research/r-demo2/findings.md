# R-DEMO2 cooker/cache and original-cooker oracle

## Status

**R-DEMO2.1 PASS for its trace/oracle scope; R-DEMO2.2 bounded collision oracle complete; R-DEMO2.4 hierarchy retained; R-DEMO2.5 PASS for bounded 9.3.1 pre-hull provenance (Path B); R-DEMO2.6 closes the exact NULL path; R-DEMO2.7 identifies the first upstream plane-decision divergence at Level B; R-DEMO2.8 prepares a hash-locked 9.3.1 +0.10 cooker candidate, with runtime DX comparison pending.** Dedicated demo branch only; R5T unstarted.

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
- R-DEMO2.5 establishes **Path B for the pinned 9.3.1 Trooper offline pair**: all 36 hull positions are isolated from the global welder, so 68 triangles / 204 corners retain their indices and translate uniformly (maximum residual `3.26e-8`). `FUN_005c9990/FUN_005ca370` are post-hull 2D processing and cannot explain the earlier crash. No new runtime mutation was made; see `vertex-welder.md` and `vertex-welder.json`. The exact 8.4.1 fault path was later established in R-DEMO2.6; do not substitute the 9.3.1 pre-hull stream for it.

See `collision-cooker.md` for full cohort hashes, mappings, Vector A/B tests, area/topology records, bounds measurements and offline checker output.

## Runtime evolution

- 8.4.1: source-first, tested model path logs `Caching disabled`, reads GXM and cooks in memory; OutputDebugString stage trace active.
- 9.3.1: source plus persistent compiled cache; missing/stale DX is generated or overwritten and reloaded. Newer DX loads with metadata-only source check. GXI can generate persistent DXT.
- Retail: tested vehicle path does not consume demo GXM as a live model source; renaming it to DX does not produce a valid compiled body. No claim that all development code was removed.

See `model-cache-state-machine.md`, `runtime/`, `dx-regeneration.md`, `source-edit-oracle.md`, `gxm-to-tag101.md`, and `r4g-impact.md`. No broad ProcMon cache archaeology is needed for this state machine.

## Roadmap (historical 8.4.1 follow-up superseded)

The earlier proposal for another 8.4.1 endpoint capture is superseded by the user's controlled result: stock `PlaneThickness` is approximately `0.0005000000237487257`; +0.4 X with stock tolerance crashes, while the same hull with `PlaneThickness = 0.00052` completes hull construction, continues loading, and visibly changes collision. The NULL-crash investigation is closed for now. The active bounded task is the 9.3.1 +0.10 X original-cooker oracle experiment in `r-demo2.8-931-chull-oracle.md`. No broad cache archaeology, track work, R5T, merge, or push is part of that task. R4G remains frozen.

## R-DEMO2.6 exact 8.4.1 hull NULL provenance

**R-DEMO2.6 established the exact 8.4.1 NULL producer and fault chain.** The candidate's `005C447B` execution is now directly supported by user-provided screenshots; the baseline had no hit in its controlled run and loaded the race. R-DEMO2.7 maps the candidate stop to face 37 and replays the first plane-equivalence divergence for source C indices `1317/1335/1337`: baseline deduplicates to face 25, translated candidate inserts face 37 under the static default thickness. The runtime face plane matches the replay to small residuals. Effective runtime thickness and live endpoint payloads remain unknown, so this is **Level B**, not a complete graph reconstruction. See `r-demo2.7-first-divergence.md`, `r-demo2.7-failing-face.md`, and the single-stop `r-demo2.7-runtime-followup.md`.

## R-DEMO2.7 first plane-divergence replay

The pinned 8.4.1 source pair differs only in 126 bytes from the 36 `$chull` source-X values; the candidate was regenerated in ignored scratch and verified against SHA256 `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699`. In the first-corner-order binary64 replay of the exact `005B9F10`/`005C3E10` branch sequence, source plane triple `C[1317], C[1335], C[1337]` changes from deduplicated face 25 to inserted face 37. The offset delta changes from `-0.0004948211223303467` to `-0.0005142677133753715` after `+0.4 X`; static default thickness `0.0005000000237487257` lies between them. Runtime face 37 has matching plane fields. The replay does not emulate x87 extended intermediates or include a direct dump of the 8.4.1 pre-hull point buffer; the loaded tolerance and endpoint identities still need one narrow capture.

This supersedes the older statement above that the crash instruction was unknown. No hull repair rule or new R4G writable-collision guarantee follows yet.

## R-DEMO2.8 demo 9.3.1 +0.10 X cooker oracle

The 9.3.1 original Trooper GXM was parsed independently: `$chull(Trooper)` is records `[1911,1979)` and derives 36 distinct Vector C indices `1317..1352`, with no overlap to other mesh records. An ignored candidate changes only those C.x fields by +0.10 source X. It is 222,754 bytes, SHA256 `b7a4da48f32ce0e4e9802e0656f79905b23af373d0dc0a397e8f2f64c973c5b3`; 117 byte values differ inside the 36 approved float fields. The byte audit is under `.research-output/r-demo2/931-chull-oracle/`. The existing native plane replay is 8.4.1 hash-pinned and is not applied to 9.3.1. Runtime DX results are pending; see `r-demo2.8-931-chull-oracle.md` and `tools/scanner/r_demo2_931_chull_dx_oracle.py`.
