# R-GFX5-1 automated validation â€” 2026-10-07

**READY_FOR_HUMAN_RUNTIME.** No game, GPU visual test, deployment or real Alt+Tab performed. R-GFX4 human acceptance is separate from this candidate's automated evidence.

Repository master-rallye-re-general, branch research/general-re, starting HEAD6ede833122bcd32ffb6223548c88587650d0539d. Tracked preflight clean, user modernization/input untracked and preserved. All changes modernization; no new branch/worktree/push; retired trees and game/inputs unchanged.

| Check | Executed result |
|---|---|
| Win32 x86 Release tools/build.py | PASS; MSVC, Visual Studio18 2026 |
| Native/visual/classifier/reflection/FOV-culling/quality/identity contracts | **7/7 PASS**,3.19s |
| Full current renderer Python suite | **83 PASS**, no skips,114.852s |
| python -m compileall -q modernization | PASS |
| PE/export/import verifier | PASS,PE32/I386,3 direct exports,no recursive d3d8 import |
| Git diff-check | PASS |

DLL SHA256 `0fdd037c5fc0542df85f31b471eb121e739a5b7e128fe4d4c460d727c3392471`, size **1,150,976 bytes**. Ignored candidate .build-msvc/Release/d3d8.dll, not committed/deployed. Direct3DCreate8@5,ValidateVertexShader@3,ValidatePixelShader@2; imports bcrypt.dll,USER32.dll,KERNEL32.dll. [Build manifest](../../data/build.json). No byte-identical rebuild claim.

New native contracts test original Stock forwarding, display fallback/hidden real HWND client1280x720 and monitor-popup exact rectangle/restoration, secondary-monitor mock offset, mode/refresh rejection, color/depth capability descent8->4->2->Stock, native Create/Reset bounded retry/lost errors, echoed effective PP unmix, full/split/quarter viewport and already-physical quarter,4:3/16:9/16:10/21:9 UI, coordinate mutation/overflow/restore, exact byte/jump failure rollback, real production x86 bridge on synthetic executable bytes, native surface GetDesc/Release and physical/logical production-wrapper capture. UI native-failure regression restores UIStock while AF remains enabled. No new test edits game memory.

Previous assertions remain: COM/ABI/FPU,32MiB boundedF10 and overflow, native HRESULT, AF MIN-only, preview exclusion/five cameras/backview/culling, shadow modes, resource poolReset, sticky brakes/stationary identity/raceHUD lifetime, vehicle discovery/learned proof/generation/static exclusions and nativeTCI restoration. Three Python capture filters update producer label R-GFX4-5 ->R-GFX5-1; assertions are retained. One native config assertion updates only the diagnostic reason from per-draw live proof to live-or-learned proof. New quality/UI metadata preserves the caller rounding mode and exception flags; the native FPU regression passes.

Initial failures retained in ignored logs: wrong synthetic branch-target fixture corrected; a Python run overlapped a new native build and saw stale executable hashes/incomplete newest capture set. Final native completed before full Python, all pass. Ghidra first attempts rejected relative project path and dot-prefixed project component; corrected absolute read-only pristine path and new ordinary-named ignored scratch project. No failed attempt recast as runtime success.

Read-only pristine Ghidra exports report rolled-back transactions/query_errors=[]; reference main pcode_errors=[]. Short hash-locked curated data committed, no raw DB/decompile/log/binary. Human remaining: display actual rasterization/Alt+Tab/Reset/high-DPI, UI all menus/HUD/split timing, hardware MSAA/COPY preservation, optional freeze A/B. Gamma and distance prototype deferred with evidence, not failed feature promises.

Final diagnostic closeout: the old visual-device effective config now also reports unknown-build display/UI/MSAA/freeze as Stock/off, preserving requested fields. The quality planner already gated the actual behavior. Added native unknown-build config assertions pass; all83 Python/7 native suites rerun for the final candidate. One feature commit plus one diagnostic closeout commit; no push.
