# R-GFX2 final report

**Status: READY FOR HUMAN RUNTIME.** No game runtime/visual parity pass is claimed.
Branch: `modernization/d3d8-proxy`; starting HEAD:
`0caf0a21c5e1a9a72cb11c3e6a83991ece003e56`.

Target: verified pristine retail,3121214 bytes, ImageBase0x00400000, I386/PE32;
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

Proxy: native Windows forwarding, `.build-msvc/Release/d3d8.dll`, MSVC x86
19.50.35729 / VS18 BuildTools + SDK10.0.26100.0 / CMake4.4.3. Verified952832 bytes;
SHA256 `b21ae8c587f6d6a14809c5c4715e557307e045a5db6d147d460d1f1537c6a5d5`.
The ignored binary is identified by [proxy-build.json](data/proxy-build.json).

| Requested area | Result / evidence |
|---|---|
| Load | Lazy explicit GetSystemDirectoryW + d3d8.dll; self-handle rejected; no heavy DllMain work; system module pinned |
| Exports | Direct3DCreate8 @5; ValidateVertexShader @3; ValidatePixelShader @2; typed WINAPI native forwarding; two unrelated host exports omitted |
| IDirect3D8 | Complete16 slots; stable known QI; CreateDevice receives original pointer/parameters, adopts wrapped output; no graphics override |
| IDirect3DDevice8 | Complete97 slots; all methods forward; known QI stable; GetDirect3D returns wrapped parent on native match |
| COM identity | Native QI ref adopted; local atomic refs; one native AddRef/Release per owned call; parent held until device wrapper destruction; mock-tested |
| Child resources | Raw; mapped-flow audit SAFE_TO_KEEP_RAW / STATIC_INFERENCE. GetDevice/unknown supported IID remains an explicit possible escape; runtime coverage required |
| Transparency | Modified graphics arguments NONE; added draws NONE; game-memory hooks NONE; no resource replacement/backend/FOV/filter changes |
| Trace | Periodic counters and provenance; F10 next full Present-to-Present interval; schema1 JSONL;8192 draws/16384 events/≤32MiB native/64MiB output; marked truncation |
| Tracker | RS/TSS, matrices, viewport, VS/FVF/PS,8 textures,16 streams/strides,IB/base,RT/depth; unknowns staynull; successful Reset clears; state blocks conservative |
| Caller | NoInline methods capture _ReturnAddress; GetModuleHandleEx locates owner without AddRef; module/base/return_rva recorded; offline exact SHA/path/method join |
| Resources | Create texture/cube/volume/VB/IB/RT/depth/image surface raw arguments and output pointer; per-device serial metadata; raw Release unobserved |
| Provenance | Actual EXE path/size/SHA; proxy SHA/path; real system requested/actual path; incoming SDK logged unchanged,120 expected for retail |
| Tools | verify_proxy stdlib PE; annotate_trace narrow return-RVA join; summarize_trace state/count/signature/owner summaries; deterministic ABI generator; normalized x86 build; read-only bridge queries |
| Tests | Native mock suite PASS;32 Python tests PASS; compileall PASS; PE verifier PASS; diff/path audit PASS. No game/GPU test claimed |
| Handoff A | Boot/menu/QuickRace/race/results/frontend/clean-exit parity with actual provenance |
| Handoff B | Exactly3 labeled F10 frames: menu, active race, results; raw captures plus session and concise observations |
| Handoff C | Optional Alt-Tab/reset and multi-camera observations after basic parity |
| Files | Source/build definitions, headers/manifests, tools/tests, docs/readiness; all new paths under modernization/d3d8-proxy |
| Commit / tree | Source-only local commit `feat: add transparent d3d8 research proxy`; final response records commit ID and clean status |

Read [runtime-handoff.md](runtime-handoff.md) for exact installation/rollback and
PASS/FAIL criteria. Return one session log plus menu/race/results frames and notes
on load/boot/frontend/race/results/exit/F10/performance. Screenshots are needed only
to document a visual regression; optional reset evidence is separate.

After **human** parity and trace acceptance, close R-GFX2 as TRANSPARENT NATIVE
D3D8 PROXY / CONFIRMED_BY_RUNTIME. R-GFX3 Classic+ is a separate future request.
It has not begun. No push, game patch, existing-research edit or installed-game
deployment was performed.
