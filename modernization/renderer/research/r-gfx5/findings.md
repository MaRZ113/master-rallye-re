# R-GFX5 continuation - Classic+ display/UI fixes

**READY_FOR_HUMAN_RUNTIME, R-GFX5-2.** R-GFX4 remains CLOSED / CONFIRMED_BY_RUNTIME. The prior R-GFX5-1 candidate has mixed human results, retained in [hashed evidence](continuation-runtime-evidence.json):

| Previous feature | Human result | Current action |
|---|---|---|
| Native MSAA4 | CONFIRMED_BY_RUNTIME; smoother vehicle/preview/wheel edges; 8 successful Reset records in the main session | Preserve sample/caps/fallback algorithm; verify Borderless interaction only. |
| MenuFreezeFix on pristine | CONFIRMED_BY_RUNTIME; equivalent tested behavior to the historical standalone fix | Preserve transactional byte change; add feature-local discovery and already-patched detection. |
| Borderless | FAIL_STARTUP; three logs end before CreateDevice completion | PLAN without HWND mutation, native creation/reset, then COMMIT only on success. Early Win32 messages remain a crash hypothesis until human retest. |
| Windowed | FAIL_SIZE_OWNERSHIP; changing sizes including 2013x1073 | Explicit client size is authoritative; 0/0 pins the first valid initial target. |
| Centered4x3 | FAIL_NOT_APPLIED; actual UI setter returned at RVA0x00161ED3 | Replace wrong general/gameplay return0x0013FA75 with unique UI-owner fingerprint plus exact ortho semantics. |
| PreserveMargins | INVALID_TEST_STATE; wide projection missing beneath active packet shifts | Leave packet/rule/bridge implementation unchanged; retest only after Centered4x3 passes. |

Repository `D:\Game\Master Rallye\master-rallye-re-general`, branch `research/general-re`. Continuation began at `144470b9e7b378ef67fa7a04b227dc6cad4c12f5`, tracked clean with untracked user `modernization/input/`. Unrelated Observatory changes appeared during work: work stopped as instructed, then resumed after the user's commit `f9e91188641ea624554e9f3761f69a93592923a7`. Only graphics changes under modernization are staged/committed. No branch/worktree/push or retired-tree writes.

Pristine target: MRallye.exe, 3,121,214 bytes, ImageBase0x00400000, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. No game/patcher execution or disk EXE/asset change. The candidate DLL is built but not deployed by the agent.

[Compatibility](compatibility-fingerprints.md): SHA is provenance; display/MSAA/AF are generic; freeze/Centered UI owners are independently fingerprinted. Camera/culling, packet margins, shadows and vehicle semantics retain exact-profile requirements. Missing/ambiguous/changed owners disable only that feature. The historical MRallye_patched.exe fails its local freeze/UI checks and is not silently authorized.

[Display](display-pipeline.md) separates plan/native/commit and reports breadcrumbs/commit failures. [UI](widescreen-integration.md) records the corrected direct setter and requires live validated provenance before cached viewport rewrites. [MSAA](msaa.md) documents ModeStock ignoring Samples and clear effective sample/swap diagnostics. [Freeze](compatibility-freeze.md) retains process-only transactional/rollback behavior and the separate media/loading/Attract boundary.

Gamma and world-distance/LOD investigation are unchanged/deferred: [gamma](gamma.md), [distance](world-distance-map.md). No HD UI assets, new reflection appearance, lighting, vertex colors, shaders, postFX, weather or camera feature. Old reconnaissance's SwapEffect3 naming correction remains: COPY3, DISCARD1; original notes are read-only.

Current automated evidence is synthetic/static/build evidence, not a visual PASS for this candidate. [Validation](validation.md), [implementation](implementation.md), [runtime handoff](runtime-handoff.md), [machine summary](runtime-summary.json). Human A-G is deliberately narrow. Stop before HD UI / R-CAM1 / F-PHOTO1.
