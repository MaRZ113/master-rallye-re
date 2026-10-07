# R-GFX5-5 narrow pass - 2026-10-07

**READY_FOR_CLOSEOUT_WITH_EXPERIMENTAL_PRESERVEMARGINS.** Branch master; starting HEAD68e5f10f51cf2d5524ac15b41787beeba1f28d44. Tracked preflight clean; untracked ps2-research preserved. Existing R-GFX5-4 Windowed/maximize/restore is human-confirmed and unchanged. Packet anchors work, but remaining logical HUD/menu splitting is still HUMAN_REPORTED_FAIL.

Read-only native ownership investigation did not establish a robust cross-packet widget root. Candidate entity/packet/content pointers each identify one entity in the bounded52-entity capture; camera lists and dispatcher are too broad, cached packet matrix is not a proven root. No fake groups, inheritance, new XY rules or sort hook. [Investigation](ui-group-ownership.md), [curated evidence](ui-group-ownership.json).

Added two completed absent-frame grace, immediate structural/epoch/Reset invalidation, bounded candidate membership/conflict diagnostics and strict Trace booleans. Canonical example/preset INIs use numeric selectors with vertical option comments, preserving text compatibility. General example retains Stock defaults; opt-in stock-plus recommends Centered4x3, native MSAA4/AF16, MenuFreezeFix=1. PreserveMargins remains experimental / legacy compatibility; Centered4x3 is stable and recommended.

Validation:96/96 Python,8/8 native, compileall modernization, PE verifier and diff-check PASS. No GPU/game execution or deployment. Centered control/combined human regression remains pending for this binary. Backdrop remains BACKDROP_ASSET_EXTENSION_REQUIRED. No later phase, new branch/worktree or push.

## Historical R-GFX5-4 record (current policy above supersedes status/lifetime)

# R-GFX5-4 final fix - 2026-10-07

READY_FOR_HUMAN_RUNTIME. Starting HEAD7267053eeb498e18d8f54ce73c8151993d6a629c, research/general-re, same master-rallye-re-general checkout. Tracked preflight clean; untracked modernization/input and modernization/PS2 preserved. Only renderer changes. No branch/worktree/push or game deployment/disk patch.

Human reports R-GFX5-3 broadly successful for Borderless/AltTab/high resolution/Centered4x3/preview/AF16/MSAA4/freeze/FOV/vehicle capability/cursor/shutdown. Two remaining visible defects: Windowed maximize snaps back and animated PreserveMargins packets jitter. [Captured baseline](finalfix-runtime-evidence.json) preserves H-hard VFOV75/culling sync/failures0, four constellations and reflection68/68, plus actual animated packet rewrites. Those captures do not test this candidate.

Windowed configured/pinned size now owns NORMAL only. Native IsZoomed plus actual client size controls temporary maximized effective backbuffer; no placement write while maximized. Restore replans to the same normal target and the existing centered commit. Genuine user resize Reset runs outside commit-echo suppression.

Historical 51 points and left text bands now admit a bounded semantic direction registry, separate from frame-owned edits. Exact entity/packet/point/content-allocation/mode identity plus UI epoch retains direction through XYZ animation (valid Z0 only). No coordinate ranges were broadened. Final consumer0056D110 and Present restore boundary remain. Unknown packets remain centered. See [UI identity/lifetime](widescreen-integration.md).

F10 adds anchor provenance/current rule/current engine XY and retained_anchor_without_current_rule_match. No new artwork; BACKDROP_ASSET_EXTENSION_REQUIRED unchanged. Await Normal/Maximize/Restore/HUD/Menu/Combined handoff. R-CAM1/F-PHOTO1/HD UI not begun.

## Historical R-GFX5-3 findings

# R-GFX5-3 lifecycle and widescreen continuation

Status: READY_FOR_HUMAN_RUNTIME for the code candidate; backdrop is separately **BACKDROP_ASSET_EXTENSION_REQUIRED**. No visual PASS is inferred from automated tests.

Human acceptance supplied on 2026-10-07 confirms R-GFX5-2 Borderless rendering/Alt+Tab, native resolution, Centered4x3, AF16, native MSAA4 and MenuFreezeFix. Human failures remain historical evidence: exit error sound/crash, Windowed Error2010, oversized Quick Race preview and alternating PreserveMargins HUD. [25 compact capture audits](lifecycle-runtime-evidence.json) preserve observed reset HRESULT 0x8876086C and breadcrumbs; raw logs are not committed.

| Issue | R-GFX5-3 change | Evidence / remaining boundary |
|---|---|---|
| Reset echo | Same planner, field-wise effective equivalence, S_OK without native Reset or metadata invalidation | Native synthetic equivalent/different/reset-failure cases; real Windowed retest pending |
| Final exit | Enter shutdown before final native Release, skip cosmetic window restore | Native wrapper destructor/window-operation counts; Alt+F4/menu Quit pending |
| Windowed placement | Center adjusted outer rectangle in rcWork; keep pinned client size | Hidden native HWND and planner tests |
| Cursor | Optional foreground/inside idle hide, movement/focus restoration; SetCursor, no ShowCursor/ClipCursor | Deterministic transition tests; desktop behavior pending |
| Preview | Separate source45 family with original source/aspect math and 4:3 reference VFOV | Read-only Ghidra 004F2350; 4:3/16:9/16:10/21:9 math tests |
| HUD alternating | Sort walk skips list head; shift at actual packet consumer entry instead | CONFIRMED_BY_EXE structural defect; bounded lifetime trace and x86 entry ABI tests; visual causality pending |
| Modified EXE FOV / vehicles | Independent complete local owner groups, image data/global placement plus runtime sanity/proof | Hardened 391d5d86… static SUPPORTED; runtime pending |
| Backdrop | XML/bank/tile content identity manifest and undistorted replacement contract | Four distinct banks; native texture-generation association UNKNOWN; artwork extension required |

No reflection appearance, lighting, vertex diffuse, shaders, weather, postFX or game disk bytes changed. Preserve R-GFX4 learning/material gates and R-GFX3 AF/culling/shadow behavior. Next after human acceptance: R-CAM1, then F-PHOTO1, then HD UI. Do not start them in this continuation.

## Historical R-GFX5-2 record (superseded where stated above)

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
