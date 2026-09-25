# Build-specific development cache evolution

| Path | Demo 8.4.1 | Demo 9.3.1 | Retail |
|---|---|---|---|
| Vehicle GXM | Tested Trooper source-first live compilation; model cache reports `Caching disabled`. Captured OutputDebugString gives cooker stages (**CONFIRMED_BY_RUNTIME_TRACE**). | Present GXM can cook persistent DX; cache freshness selects rebuild/load per tested LastWriteTime ordering (**CONFIRMED_BY_CONTROLLED_RUNTIME_TRACE**). | Tested retail vehicle path does not load demo GXM as live source; do not infer all GXM code was removed. |
| Vehicle DX | Same-stem DX removal did not affect tested Trooper visuals; DX-only did not restore the tested roles. | DX persists to disk, is reloaded after cooking, and can load when GXM is absent. Safe edit output loads DX-only and visibly changes geometry. | Supplied GXM renamed to DX is not a valid body resource; body visual/collision absent while wheels remain. |
| Texture GXI/DXT | Earlier clean Black-tga byte comparison recorded in `dxt-regeneration.md`. | A ProcMon cache miss confirms GXI→persistent DXT creation, close/reopen and full read for Black-tga. | Existing compiled-resource behavior; no general development-cooker claim. |
| DebugView | OutputDebugString channel and captured stage order confirmed. `$chull` candidate crash ends inside convex-hull build. | **NO_OUTPUT_OBSERVED** for the tested session; logger implementation/removal remains **UNKNOWN**. | No claim. |

For tested 9.3.1 model cases, `GXM newer than DX → read/cook/overwrite/reload`; `DX newer than GXM → metadata-only GXM check/no writes/load DX`. Source-missing + DX-present falls back to DX. Both missing and equal timestamps are **UNKNOWN**. Full transition evidence and the state diagram are in `model-cache-state-machine.md`.

The source/cache ordering was deliberately controlled and is **CONFIRMED_BY_CONTROLLED_RUNTIME_TRACE**. The targeted EXE comparison does not establish that the compared helper values are specifically LastWriteTime; see `targeted-cache-xrefs.md`.

The deterministic 9.3.1 car rebuild A/B pair is byte-identical for the tested fixed source, while historical shipped DX differs at float and unresolved descriptor details. The safe +0.15 source edit maps to one render position and regenerated marker bounds; tag101 and topology stay unchanged. Same-build `$chull`→tag101 provenance is stronger, but the `$chull` source-only runtime edit crashes. These are oracle and safety boundaries, not changes to retail R4G.
