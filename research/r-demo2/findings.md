# R-DEMO2 cooker/cache and original-cooker oracle

## Status

**R-DEMO2.1 PASS for the defined trace/oracle scope.** Dedicated branch/worktree only; no master changes, merge, push, EXE patch, R4G implementation, or course/track reverse engineering.

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

## Runtime evolution

- 8.4.1: source-first, tested model path logs `Caching disabled`, reads GXM and cooks in memory; OutputDebugString stage trace active.
- 9.3.1: source plus persistent compiled cache; missing/stale DX is generated or overwritten and reloaded. Newer DX loads with metadata-only source check. GXI can generate persistent DXT.
- Retail: tested vehicle path does not consume demo GXM as a live model source; renaming it to DX does not produce a valid compiled body. No claim that all development code was removed.

See `model-cache-state-machine.md`, `runtime/`, `dx-regeneration.md`, `source-edit-oracle.md`, `gxm-to-tag101.md`, and `r4g-impact.md`. No broad ProcMon cache archaeology is needed for this state machine.

## Roadmap (not started)

The next demo-focused target is **R-DEMO2.2 — Collision Cooker Semantics**. Later course/track archaeology follows that target. This records sequencing only; neither phase has started. R4G is complete and frozen and is not the next unfinished phase.
