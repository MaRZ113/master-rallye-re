# R-OBS1b — standard hook-free integration

Starting HEAD: `adbf1ab81d14a5f2be0abc9fe93ffb06450c774b`, clean canonical
`master-rallye-re-general`, branch `master`. No branch/worktree was created.

The user reported a completed controlled real-game comparison in the R-OBS1b
request. With the separately identified no-hooks DLL, Broker opens and native
Debug/Dump completes; Windowed/Borderless, cursor auto-hide, Alt+Tab,
minimize/restore/Reset, input and accepted visual features remain healthy.
The user also independently confirmed the R-ATTR1 Restart correction and
legitimate idle-main-menu Attract. These exercised behaviors are
**CONFIRMED_BY_RUNTIME**, based on the human report, not an agent game launch.

Those were separate binaries. The newly built combined source candidate is
**READY_FOR_COMBINED_RUNTIME_VALIDATION**, with gameplay result **PENDING**.
The exact internal mechanism of the old hook-enabled stall is **UNKNOWN**;
the controlled comparison supports the compatibility policy without proving
a Win32 deadlock cycle. Further root-cause research is deferred.

Standard source no longer contains installation, callbacks, owner state or
uninstall code for WH_CALLWNDPROC/WH_CALLWNDPROCRET. The diagnostic CMake option
and build.py flag are removed; an old cached option cannot enable missing code.
There is no replacement global hook, research hook-enabled build or INI toggle.

Present still calls the existing cursor_tick; foreground/inside checks gate
hiding, polling restores on observed focus loss, and shutdown restores a hidden
cursor. This is the tested non-hook polling/lifecycle path. It does not claim
immediate callback-time focus telemetry while Present is stopped.

Presentation planning, Windowed resize/maximize/restore and Reset reentrancy,
Borderless geometry, UI/carousels, FOV/culling, AF/MSAA, MenuFreezeFix,
reflections, foliage, F10/COM and the A3c observer remain intact. Exclusive
recovery remains deferred. No scene-epoch or Freecam work is included.

Current diagnostics explicitly report `thread_message_hooks_enabled=false`,
`display_watch=disabled_by_standard_policy`,
`cursor_handling=present_polling_and_shutdown`, and
`window_message_telemetry=unavailable_hooks_retired`. Legacy
`cursor_watch_installed=false` and message counters at zero are compatibility
fields, not evidence of missing events. Native D3D/Reset/window/resize records
remain real; pre/post messages are never invented from Present snapshots.
The offline auditor retains historical deferred-record support for old captures.

Observatory's verified menu-less HWND path, single allowlisted opener, exact
timeout/late-open outcomes, and separately verified Broker Dump are unchanged.
R-ATTR1 source and startup/byte/thread/rollback gates are unchanged: only the
approved retail Loading redirect is attempted in process memory before the
first native factory. The original EXE and legitimate idle Attract stay intact.

One standard Win32 DLL is built from this checkout, not assembled from old
binaries. See [validation](validation.md) and [short smoke test](runtime-handoff.md).
After integration acceptance, the next phase is **R-CAM1-A3d — Hierarchical
Scene Epoch Repair**; it was not started here.
