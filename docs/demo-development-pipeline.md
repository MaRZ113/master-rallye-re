# R-DEMO development asset pipeline: current evidence

This branch is isolated from `master` and reads the external `demo-8.4.1`, `demo-9.3.1`, and `retail` corpora without modifying them. Generated manifests retain `corpus_id` and `relative_path`. Raw game resources remain outside Git; controlled candidates and runtime outputs are under ignored `.research-output/`.

## Image path

GXI, GXB, and the November-only GXP share an eight-byte `0x00013039` / u16 width / u16 height / RGBA-sized payload layout in the inspected corpus. They retain separate APIs because their loader roles differ or remain unproven. Strict readers cover 2,045/2,046 GXI in September (one malformed-length test resource), 677/677 GXI and 38/38 GXP in November, and 82/82 GXB across both builds.

For 1,450 of 1,483 same-build, same-stem GXI/DXT candidates, a top-down RGBA-to-bottom-up BGRA transform plus the observed DXT header and CRC32 recreates the complete DXT bytes. The 33 nonmatches are September font resources. This establishes **CONFIRMED_BY_CORPUS** build correspondence for exact pairs. A clean runtime-regenerated Trooper Black DXT also matches the shipped and offline-reconstructed bytes exactly (**CONFIRMED_BY_RUNTIME + CONFIRMED_BY_BYTES**); see `research/r-demo2/dxt-regeneration.md` and `research/r-demo2/runtime/procmon-findings.md`. GXP has no direct same-stem DXT/TGA pairs, but 31/38 GXP files reproduce 146 same-build DXT tiles byte-identically; the other seven have no same-stem tile set. Runtime GXP generation/loading remains **UNKNOWN**.

GXB CarSheet in September is pixel-identical to its supplied same-build TGA after row/channel conversion. The November CarSheet has changed dimensions and no same-stem TGA in the corpus.

## Model path

The 80 GXM files with the recognized material-table prefix (including one with zero materials) expose source-like material names, ordered texture references, indexed records, and three float3 arrays. The remaining 29 September GXM variants have a different post-header prefix, including course/test resources; their tail is opaque. Trooper sidecars match parsed GXM material counts, mesh record spans, and ordered suffix names. The indexed November Jump `$chull` points numerically match the retail Jump tag101 convex hull/AABB/radius to float precision after an axis transform (cross-build comparison). Same-build 9.3.1 `$chull` points also map to regenerated tag101 B vertices; source triangles are retriangulated. This supports source-to-compiled collision provenance, not an exact cooker recipe or safe hull-edit rule. `$cylinder` to tag102 remains **UNKNOWN**.

The demo DX draw grammar differs from the retail parser. Demo DX header/control words also differ (`127` predominant in September, `131` in November, `135` throughout retail). Existing retail DX parsing must not be used to invent demo draw/material semantics. Static extension strings in the retail EXE do not establish runtime source access.

## Runtime and cooker evidence

- **Demo 8.4.1:** tested Trooper GXM paths are source-first with persistent model caching disabled. DebugView captured OutputDebugString diagnostics and normal cooker stage order. In R-DEMO2.7, the pinned translated `$chull` candidate directly hits the edge-order no-match branch `005C447B`, later faulting through NULL at `005C3212`; the baseline did not hit that breakpoint in the controlled run and loaded the race. A source replay of exact 8.4.1 plane construction maps the candidate face 37 to an extra plane caused by the `005C3E10` offset-tolerance comparison after translation. This is Level B: the effective runtime tolerance and exact endpoint payload graph remain **UNKNOWN_FROM_CAPTURE**. See `research/r-demo2/r-demo2.7-first-divergence.md` and `research/r-demo2/r-demo2.7-runtime-followup.md`.
- **Demo 9.3.1:** ProcMon controlled timestamp cases confirm GXM-to-DX miss/rebuild, stale-cache rebuild, fresh-cache load, and source-missing DX fallback for the tested paths. Both-missing and equal-timestamp states remain **UNKNOWN**. No DebugView output was observed in the tested session; logger removal remains **UNKNOWN**. See `research/r-demo2/model-cache-state-machine.md` and `research/r-demo2/runtime/`.
- **Determinism and source edit:** two unchanged-GXM 9.3.1 rebuilds are byte-identical for this controlled pair. A safe Vector C `+0.15` edit changed one DX render position and recomputed marker bounds; the user confirmed visible DX-only loading. This is a bounded oracle result, not universal cooker determinism or a general write guarantee. See `research/r-demo2/rebuild-determinism.md` and `research/r-demo2/source-edit-oracle.md`.
- **Retail negative control:** the tested vehicle path did not consume demo GXM as a live model source; renaming it to DX did not produce a valid compiled body. This does not prove all development code was removed from retail.

## Evidence boundary and remaining unknowns

Corpus, executable, byte-comparison, controlled trace, and human runtime evidence are labeled separately in the linked findings. Still unresolved are universal GXM hierarchy controls, the exact `$cylinder` formula, the 8.4.1 `$chull` runtime tolerance and endpoint-object graph, the exact meaning of the bounded static file-time helper, and the untested cache states listed above. The 8.4.1 visual loader matrix did not receive a per-resource ProcMon file-access matrix; 9.3.1 cache traces must not be generalized to it. No R-DEMO2 result changes the retail authoring pipeline.

## Roadmap

R-DEMO2.1 closed its trace/oracle scope, R-DEMO2.2 its bounded collision analysis, and R-DEMO2.4 mapped the Trooper hierarchy. R-DEMO2.5 establishes Path B for the pinned 9.3.1 offline pair; it does not replace the exact 8.4.1 path. R-DEMO2.6 identifies the exact NULL producer and fault. R-DEMO2.7 replays the first 8.4.1 plane-equivalence divergence and maps it to captured candidate face 37, while preserving uncertainty about the live tolerance and endpoint graph. One bounded capture is specified in `research/r-demo2/r-demo2.7-runtime-followup.md`. Course/track work remains unstarted; R4G is frozen.
