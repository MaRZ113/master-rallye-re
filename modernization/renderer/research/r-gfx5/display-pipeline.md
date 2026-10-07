# Display, resolution and Reset

ConfigVersion1 is required. Display is D3D/Win32-generic and does not require the pristine SHA. Invalid individual display settings choose displayStock locally. Width/height both0 or nonzero320x200..16384x16384; actual native device is the final legality check.

| Mode | Behavior |
|---|---|
| Stock | Original presentation/HWND/styles; no new window/caps/surface calls for disabled display/AA. |
| Windowed | Existing device HWND or focus HWND; WindowedTRUE, desktop-compatible format, fixed configured **client** dimensions. 0/0 pins the first valid requested backbuffer size, or initial client when the request is zero. Later game Reset or manual resize cannot redefine it. |
| Borderless | Same HWND; WindowedTRUE, popup style preserving visibility/clip flags, no caption/borders, exact monitor rcMonitor. 0/0 uses native desktop. Explicit nonnative dimensions currently resolve to monitor-native with logged reason; no supersampling/scaler. |
| ExclusiveFullscreen | WindowedFALSE; enumerate actual adapter modes, match dimensions/format/explicit refresh, CheckDeviceType. Unsupported falls back to original Stock. Refresh0 requests native default. |

Save style/exstyle/menu/outer/client before changes. Borderless uses MonitorFromWindow + GetMonitorInfoW `rcMonitor`, including secondary-monitor offsets. Decorated Windowed uses `rcWork`: derive outer dimensions with AdjustWindowRectEx and clamp outer placement within the work area while retaining the configured client size. An oversized requested client falls back to Stock with a reason; there is no silent scale-down. No forced activation, visibility or DPI-awareness change.

R-GFX5-1 runtime: three Borderless logs stop before CreateDevice completion; Windowed auto sizing grew through several sizes, reaching 2013x1073 in the PreserveMargins session. [Hashed evidence](continuation-runtime-evidence.json). Early synchronous HWND mutation is a **STRONG HYPOTHESIS**, not a proven crash cause.

R-GFX5-2 order is **PLAN -> native CreateDevice/Reset -> successful native result -> HWND COMMIT**. PLAN queries/snapshots and computes parameters without SetWindowLong, SetMenu, SetWindowPos or restoration. Failed native calls never commit/restore HWND and failed Reset retains the preceding accepted descriptors/window/domain. Native AA/display retries remain bounded at three; DEVICELOST/DEVICENOTRESET do not retry. Only successful Stock fallback restores a previously owned window.

COMMIT compares current HWND/style/menu/client/outer geometry with the committed state; unchanged placement skips Win32 mutations. Manual resize/maximize is corrected to the pinned client dimensions on the next successful Reset. The selected monitor rectangle remains authoritative for Borderless. A guard rejects a synchronous reentrant Reset during window mutation before it can start a second native transaction.

If Win32 commit fails after native success, restore the pre-commit window snapshot and log `window_commit_failed_native_parameters_retained`. Keep the real accepted presentation parameters/HRESULT visible: do not pretend a Stock-sized device was created. Unverified rollback is separately logged and restoration remains owned for a later attempt/destruction. Human runtime must reject a commit failure; this is diagnostic recovery, not a successful Borderless result.

Compact breadcrumbs cover plan, monitor selection, transformed PP, every native CreateDevice/Reset begin/end, commit begin/end or unchanged, both SetWindowLong calls, SetMenu and SetWindowPos begin/end. Logs expose the last completed step after a crash. No per-frame repositioning.

Same per-device planner handles CreateDevice and Reset. Trace raw `requested`, unmixed `logical_baseline`, accepted `effective`, pinned Windowed target, commit status, monitor/reasons/attempts. Successful PP returns native effective values. An echoed Reset field still exactly equal to our previous override is unmixed to its original value; fresh game requests remain in the logical baseline, but cannot redefine a pinned Windowed target. Thus AA fallback cannot inherit our DISCARD/MSAA from the preceding successful call.

Attempt1 display+AA, ordinary failure retry without our AA, then without our display: maximum3 native calls. DEVICELOST/DEVICENOTRESET return immediately. Final native HRESULT preserved. Successful Reset invokes existing pool-aware observer once: DEFAULT metadata invalidated, MANAGED retained, object/learned vehicle proof cleared and relearned. GetDesc observations hold/release transient native surface references only.

| Pristine owner | VA / RVA | EXE-confirmed role |
|---|---|---|
| Window creation | 0x005590C0 / 0x001590C0 | HWND+0x5C,focus+0x60; style+0x164,outer/client+0x168/+0x178 |
| Mode/style owner | 0x0055AED0 / 0x0015AED0 | Original window/fullscreen handling |
| Device creation | 0x0055AB90 / 0x0015AB90 | CreateDevice site0x0055ACD7/RVA0x0015ACD7, existing behavior flags |
| Client dimensions | 0x0064DD10 / 0x0024DD10 | GetClientRect returns width/height |
| Frame dimensions | 0x00653080 / 0x00253080 | Current client copied to camera+0x80/+0x84 before submission |
| Projection | 0x005614A0 / 0x001614A0 | Camera aspect; existing R-GFX4 gameplay VFOV/frustum seam |

New native client dimensions therefore feed the stock camera; no second90/45 FOV patch. Frontend preview remains excluded from configurable gameplay VFOV.

Viewport scales endpoints, preserving partial/split/quarter regions and MinZ/MaxZ. Recognizable full viewport establishes logical or already-physical coordinates; physical quarters pass through to avoid double scaling. Ambiguous partial before that stays Stock. Reset resets domain, using unmixed baseline even when incoming PP echoed physical size. GetViewport virtualizes logical; F10 shows both.

Active display/AA logs actual backbuffer/depth GetDesc dimensions/format/sample type after Create/Reset. High resolution must be proved by these plus viewport, not PP request or enlarged window alone. DPI awareness unchanged; high/mixed DPI, monitor migration, user resize and split-screen image placement still need runtime testing. Native-monitor Borderless prioritizes a coherent window/client/backbuffer over arbitrary nonnative size.
