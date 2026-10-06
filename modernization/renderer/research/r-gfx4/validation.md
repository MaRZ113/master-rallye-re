# R-GFX4-2 automated validation

READY_FOR_HUMAN_RUNTIME. New DLL human A–E results remain pending. Started clean on research/general-re HEAD9c3a353a4838f6b19c2ab50d663b389acc64531c. No new branch/worktree/push or game deployment. All changes under modernization/renderer; frozen research/retired trees preserved.

| Check | Result |
|---|---|
|Win32 x86 Release tools/build.py|PASS|
|CTest native_contracts / visual_contracts / classifier_contracts / reflection_contracts|4/4 PASS|
|Full renderer Python unittest discovery|59 PASS, no skips|
|python -m compileall -q modernization/renderer|PASS|
|Pinned interface generation,16/97 methods, identical bytes on rerun|PASS|
|PE/import/export verifier|PE32/I386 DLL, required exports, no d3d8 self-import|
|Protected twelve-asset retail lighting analysis|exact structural equality with tracked JSON|
|Research JSON parsing and scoped Git diff-check|PASS|

DLL SHA256: `ff8a95bdb80961fbba65f41f16e0686792aae98d60740c7a3e9f480c16d852c3`. Size: 1067520 bytes. Product modernization/renderer/.build-msvc/Release/d3d8.dll is ignored, not committed/deployed. Exports Direct3DCreate8@5, ValidateVertexShader@3, ValidatePixelShader@2. Imports bcrypt.dll, USER32.dll, KERNEL32.dll. Build verification is distinct from GPU/visual compatibility and does not promise byte-identical rebuilds.

New native contracts cover managed texture/VB/IB unchanged serials; DEFAULT texture/VB, RT/depth removal; SYSTEMMEM/SCRATCH/ImageSurface persistence; cube/volume pool arguments; fresh serials on recreation; failed Reset preservation. The real wrapper mock timeline learns a constellation, succeeds Reset, loses temporal confidence, preserves managed resources and relearns using their unchanged generations.

Geometry tests cover varied widths/wheelbases, permutation, cold wheels, static chassis, three-wheel rejection, five-wheel ambiguity, shared-wheel conflict, two rotated cars sharing resource signatures, saturation/overflow and invalidated draw-time leases. All seven supplied pre-Reset rectangles pass retrospective offline analysis; this is not a new native runtime pass.

Reflection contracts establish original native indexed draw once; exact temporary NORMAL-to-REFLECTIONVECTOR-to-NORMAL and low bits; logical state unchanged; effective state restored; draw failure HRESULT preserved; failed temporary setter stock fallback; tracing disabled and logger disabled during draw; failed restore reported/feature disabled/pending repair with later draws failing closed until repair. Native mock F10 captures positive modifications and successful restoration. DrawPrimitive is excluded: no mapped positive vehicle DP owner exists. VIEW reversal preserves race context; source45 preview projection at the shared helper clears it.

Closed R-GFX3 AF MIN-only/MAG/MIP/stage1, caps, FOV depth bits/aspect/preview exclusion, stock shadow, dual getters, failed setters, Reset and full COM forwarding remain passing. No new lighting, cubemap, shader, vertex rewrite, child resource wrapping or backend.

Python checks cover rectangle/ambiguity/cold-wheel analysis, Reset pool segmentation, F10 additive fields and actual modified TCI/restore, strict reflection provenance audit, legacy/unknown/incomplete frames and lighting heuristics. The lighting tool prevents bytecode writes into frozen src/. Human validation still needs actual Reset/relearn, CPU cost, visibility/LOD coverage, scenery rejection, hardware coordinate behavior and normal/look-back visual comparison. The previous-complete-frame proof lease is explicit; later classification never retroactively authorizes a draw.

Canonical corpus EXE rehashed bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4. Current test-install EXE fb11754c0c6d56b02c175a261e36d0768a72bba6d5a0fd74cbd7c7ad9d34be7b is UNKNOWN_BUILD. Historical supplied captures are canonical; no current-install address equivalence or R-GFX4-2 human pass is claimed. runtime-handoff.md requires Stock Reset/relearn Stage A before B–E.
