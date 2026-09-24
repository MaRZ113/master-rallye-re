# R-DEMO development asset pipeline: current evidence

This branch is isolated from `master` and reads the external `demo-8.4.1`, `demo-9.3.1`, and `retail` corpora without modifying them. All generated manifests retain `corpus_id` and `relative_path`. Raw game resources remain outside Git; the one controlled GXM candidate is under ignored `.research-output/r-demo/scratch`.

## Image path

GXI, GXB, and the November-only GXP share an eight-byte `0x00013039` / u16 width / u16 height / RGBA-sized payload layout in the inspected corpus. They retain separate APIs because their loader roles differ or remain unproven. The strict readers cover 2,045/2,046 GXI in September (one malformed-length test resource), 677/677 GXI and 38/38 GXP in November, and 82/82 GXB across both builds.

For 1,450 of 1,483 same-build, same-stem GXI/DXT candidates, a top-down RGBA-to-bottom-up BGRA transform plus the observed DXT header with CRC32 of the transformed payload recreates the complete DXT bytes. The 33 nonmatches are September font resources. This establishes **CONFIRMED_BY_CORPUS** build correspondence for exact pairs. A clean runtime-regenerated Trooper Black DXT was later supplied and matches the shipped and offline-reconstructed bytes exactly (**CONFIRMED_BY_RUNTIME + CONFIRMED_BY_BYTES**); see `research/r-demo2/dxt-regeneration.md`. Targeted demo EXE xrefs confirm source/cache code paths, but not the result for a specific file.

GXB CarSheet in September is pixel-identical to the supplied same-build TGA after the same row/channel conversion. The November CarSheet has changed dimensions and no same-stem TGA in the corpus. GXP has no direct same-stem DXT/TGA pairs, but 31/38 GXP files reproduce 146 same-build DXT tiles byte-identically after rectangle extraction, row/channel conversion, zero padding, and CRC32 wrapping. The other seven have no same-stem tile set. This establishes static tiled-image correspondence, while runtime generation/loading remains **UNKNOWN**.

## Model path

The 80 GXM files with the recognized material-table prefix (including one with zero materials) expose source-like material names, ordered texture references, indexed records, and three float3 arrays. The remaining 29 September GXM variants have a different post-header prefix, including course/test resources; their tail is opaque. Trooper sidecars match parsed GXM material counts, mesh record spans, and ordered suffix names. The indexed `$chull(Jump)` source points in November numerically match the retail Jump tag101 convex hull/AABB/radius to float precision after an axis transform. This supports a source-to-compiled collision path, but it is a cross-build comparison, not proof of the exact historical compiler.

The demo DX draw grammar differs from the retail parser. Demo DX header/control words also differ (`127` predominant in September, `131` in November, `135` throughout retail). Existing retail DX parsing must not be used to invent demo draw/material semantics. The static EXEs contain GXM/GXI/GXB extension strings even in retail, which does not establish actual retail file access.

## Human runtime and loader continuation

First-pass human tests in `demo-8.4.1` show that the identified Trooper GXM Vector C field changes live body geometry. In the tested Trooper matrix, `car.gxm` supplies the race body and is involved in primary collision, `complete.gxm` supplies the presentation model, and `wheel.gxm` supplies visual wheels (**CONFIRMED_BY_RUNTIME**). Removing their same-stem DX files caused no visible change; this does not prove the DX files are never opened. Wheel physics persisted without visual wheels. The result is specific to the tested build and resource paths; see `research/r-demo/runtime/loader-matrix.md`.

Trooper `Black-tga.gxi` now recreates its DXT byte-identically in both the offline converter and the original runtime. The isolated `$chull`-only source edit crashed both demos (**CRASHED_IN_RUNTIME**), so a new hull mutation waits for crash-stage localization. In 9.3.1, user tests confirm GXM→persistent DX generation and DX-only fallback for observed complete/wheel paths; the original-vs-regenerated car DX pair has identical render topology but float and secondary collision-descriptor differences. Two separate 9.3.1 rebuilds from unchanged GXM are byte-identical. A one-coordinate source edit generated a DX with one changed render position and recomputed bounds; the user confirmed the custom DX loads without GXM and shows the edit. The Win32 Debug-window helper failed in user testing; DebugView and ProcMon file-order traces remain pending. See `research/r-demo2/`.

## Evidence and integration boundary

- **CONFIRMED_BY_BYTES / CORPUS:** manifest hashes, image layouts, exact conversions for listed pairs, GXM prefix/index bounds, Trooper sidecar agreement, and Jump collision numeric match.
- **SOURCE_SIDE_EVIDENCE:** `$paint`, `$glass`, `$perspex`, `$rubber`, `$chull`, and `$cylinder` strings. They do not override R4D/R4D.1 renderer evidence.
- **CONFIRMED_BY_RUNTIME (human demo tests):** 8.4.1 live GXM geometry and car/complete/wheel matrix; clean byte-identical DXT regeneration; 9.3.1 GXM→DX generation and DX-only fallback; `$chull` candidate crash.
- **UNKNOWN:** universal GXM hierarchy controls, exact `$cylinder` formula, cache file-access order/invalidation, DebugView channel and `$chull` crash stage.

No R-DEMO2 result changes the retail authoring pipeline yet. `research/r-demo2/findings.md` tracks cooker reconstruction and remaining gates.
