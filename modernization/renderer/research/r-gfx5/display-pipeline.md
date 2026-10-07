# Display, resolution and Reset

ConfigVersion1/exact pristine required. Invalid individual display settings choose displayStock locally. Width/height both0 or nonzero320x200..16384x16384; actual native device is final legality check. Unknown build forwards/traces with Stock effects.

| Mode | Behavior |
|---|---|
| Stock | Original presentation/HWND/styles; no new window/caps/surface calls for disabled display/AA. |
| Windowed | Existing device HWND or focus HWND; WindowedTRUE, desktop-compatible format, configured **client** dimensions. Caption/borders, AdjustWindowRectEx with menu, GetClientRect verification. 0/0 follows game dimensions/current client. |
| Borderless | Same HWND; WindowedTRUE, popup style preserving visibility/clip flags, no caption/borders, exact monitor rcMonitor. 0/0 uses native desktop. Explicit nonnative dimensions currently resolve to monitor-native with logged reason; no supersampling/scaler. |
| ExclusiveFullscreen | WindowedFALSE; enumerate actual adapter modes, match dimensions/format/explicit refresh, CheckDeviceType. Unsupported falls back to original Stock. Refresh0 requests native default. |

Save style/exstyle/menu/outer/client before changes. MonitorFromWindow(MONITOR_DEFAULTTONEAREST)+GetMonitorInfoW chooses rcMonitor, not taskbar workarea; initialize cbSize as required by [Win32 API](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmonitorinfow). No monitor-selection UI, forced activation or visibility. Failure, Stock fallback and policy destruction restore saved state; restore failure logged.

Same per-device planner handles CreateDevice and Reset. Trace raw `requested`, unmixed `logical_baseline`, accepted `effective`, monitor/reasons/attempts. Successful PP returns native effective values. An echoed Reset field still exactly equal to our previous override is unmixed to its original value; fresh game requests remain. Thus AA fallback cannot accidentally inherit our DISCARD/MSAA from the preceding successful call.

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
