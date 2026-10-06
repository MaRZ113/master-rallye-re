# R-GFX4-3 automated validation — continuation #2

**READY_FOR_HUMAN_RUNTIME.** Static analysis and synthetic execution support this candidate; A–E human results for this DLL are pending. Starting branch `research/general-re`, HEAD `25cb58dcf5ce652ae0b0a5e808ccc879596dd40b`, tracked tree clean. The only pre-existing untracked file, `modernization/renderer.zip`, is preserved and excluded from staging. No branch/worktree creation, push, game deployment, EXE/asset disk change or Ghidra database save. Every task file is inside `modernization/renderer/`.

| Check | Result |
|---|---|
| Win32 x86 Release `tools/build.py` | PASS |
| CTest native / visual / classifier / reflection / FOV-culling contracts | 5/5 PASS |
| Full renderer Python unittest discovery | 63 PASS, no skips |
| `python -m compileall -q modernization/renderer` | PASS |
| Pinned 16/97-method interface generation | Identical bytes on rerun |
| Read-only exact-build culling map regeneration | Identical JSON including 14 Ghidra function digests |
| Research/data JSON parsing | 20 valid documents |
| PE/import/export verifier | PE32/I386 DLL; exactly three required exports; no recursive d3d8 import |
| Scoped `git diff --check` | PASS |

DLL SHA256: `0669d8ac986088735d4f01fe545c3490a379db8eaf147fa247cf4d2b391c8942`. Size: **1084928 bytes**. Ignored local product: `modernization/renderer/.build-msvc/Release/d3d8.dll`, not committed or deployed. Exports: Direct3DCreate8@5, ValidateVertexShader@3, ValidatePixelShader@2. Imports: bcrypt.dll, USER32.dll, KERNEL32.dll. [Machine-readable build verification](../../data/build.json). Build evidence is separate from GPU compatibility and does not promise byte-identical rebuilds.

The new native full-frame timeline repeats race projection → body/four wheels → HUD ortho → Present. It proves increasing ages, stable IDs/epoch and positive mature reflection candidates through ordinary HUD-ending frames; HUD never enters vehicle classification. Menu-only history expires once. Successful Reset clears tracks while MANAGED metadata remains known; full HUD-ending frames relearn. Existing failed-Reset and pool-aware DEFAULT/MANAGED/SYSTEMMEM/SCRATCH contracts remain passing.

The FOV contract checks projection/CPU-plane agreement at640x480,1920x1027 and portrait dimensions, widened edge acceptance, inside/outside top/side bounds,110° widescreen safety, source45 exclusion, invalid/scaled/sheared camera rejection, five generic orientations plus reversal, exact48-byte restoration and expired camera proof. It is not execution of the five game presets. Failed install/remove/protection/write/cache-flush operations attempt and verify rollback in synthetic memory; foreign bytes are not overwritten. A real native x86 executable-memory fixture exercises the production CALL bridge's stock-forwarding path, preserving ECX/EDX, arguments, return PC, flags and defined x87/SSE environment/register payloads. It never executes the game or installs a hook in a game process.

Renderer-local `tools/inspect_fov_culling.py` refuses unknown hashes before PE parsing, validates pinned live-site byte expectations and relative CALL targets, and records read-only Ghidra provenance. Python tests cover each wrong signature and wrong image base. F10 tests inspect positive native synthetic captures from the current test executable hash, so preserved older test captures cannot contaminate the verdict. Actual supplied R-GFX4-2 captures are retained as failure evidence:190–286 known signatures per frame, but zero tracked/modified draws; their Reset summaries retain managed metadata. [Input digest](continuation2-runtime-evidence.json).

R-GFX3 regression contracts remain passing: AF stage0 MIN-only with MAG/MIP/stage1 stock; caps/config guards; FOV depth/aspect and source45 exclusion; shadow Stock/Off; dual logical/effective getters; native failure HRESULTs; Reset and COM forwarding. ViewDependent2D remains unchanged, body-only, strongly confidence-gated and exact-TCI-restoring; no appearance tuning, new lighting, shaders, assets or backend.

Canonical corpus and current `D:/Game/Master Rallye Pristine/MRallye.exe` both rehashed to `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. SHA/bytes/base/CPU/thread/camera proof gates the runtime-only CALL atVA006532DD/RVA002532DD. GameplayFOV=false installs no hook; missing proof keeps stock projection. Device-config exception, native projection rejection or unsupported scheduling fail closed. Normal restoration and hook removal have synthetic evidence; abnormal native memory/protection failure is not promised visually reversible and is a human FAIL.

**Still required:** human A classifier, B wheel/world edges at640/1920, C default/cam1–4 plus active lookback, D actual successful Reset/relearn, then E only with positive candidate/modified/native-write counters. Specific missing-wheel repair, real camera coverage, CPU cost, hardware reflection coordinate behavior and visual quality are unconfirmed. See [runtime handoff](runtime-handoff.md). R-GFX3 stays CLOSED. Stop after this candidate; wait for human evidence.

---

The following section is preserved as historical validation of R-GFX4-2. Its candidate hash, counts, starting HEAD and then-current unsupported test EXE describe that older run, not the current R-GFX4-3 state.

# Historical R-GFX4-2 automated validation

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
