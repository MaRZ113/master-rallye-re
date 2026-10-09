# R-GFX5-7 — Display Lifecycle Finalization

## Evidence boundary

This pass is based on `master` starting at `f43d720e08961791ad46875af0d15430ed555e02`, the PC-VISUAL-PILOT1 CPU-upload-provenance handoff. That commit is an ancestor of the implementation. The foliage provenance path and its synthetic tests remain in the current renderer. Source and mock behavior are reported as `CONFIRMED_BY_SOURCE` and `CONFIRMED_BY_SYNTHETIC_TEST`; no game run was performed for this pass.

Prior in-game validation confirms PreserveMargins v2 stability; that result remains `CONFIRMED_BY_RUNTIME`. Exclusive `D3DERR_DEVICELOST` is also a recorded runtime observation, but its causal owner was not captured in a new trace during R-GFX5-7.

## Windowed size ownership

The previous policy treated configured `Width` and `Height` as a permanent pinned target. A real drag-resize could therefore be reset to the startup size. R-GFX5-7 separates the initial setting from the currently accepted normal client size and from the temporary maximized client size.

On first Windowed CreateDevice, nonzero INI dimensions establish the initial client target. With `Width=0` and `Height=0`, the first valid game presentation size is used, with the current client size as the fallback. The first accepted target is committed only after native CreateDevice/Reset succeeds.

A later normal resize is admitted only when the HWND is valid, the window is neither maximized nor minimized, no renderer-owned window commit is active, the HWND is the last accepted device window, style/ex-style/menu identity is unchanged, and both actual client dimensions and the game's Reset request match. Only a successful native Reset replaces the normal target. An unrelated Reset request leaves the target unchanged. A failed Reset leaves both the accepted target and effective device parameters unchanged.

If a normal window already has the expected style/menu and its actual client matches the effective backbuffer, the current OS rectangle is accepted as application-owned placement. An outer-rectangle move alone does not recenter the window or call `SetWindowPos`. While maximized, the OS owns placement and the actual client dimensions drive the backbuffer, viewport, and effective aspect; they do not replace the normal target. Restore follows the latest accepted normal client size. Minimized or zero-sized clients never become normal targets.

Reset echo protection remains separate from live resize admission. A renderer-induced equivalent echo is suppressed without a native Reset. A real later resize is evaluated from fresh HWND state. Successful Reset epoch telemetry advances only after an actual successful native Reset; failed Reset and suppressed echoes do not advance it. The existing device wrapper remains responsible for the pool-aware resource transition, including conservative foliage mirror invalidation.

Implementation is in [`quality.cpp`](../../src/quality.cpp) and [`quality.hpp`](../../include/quality.hpp); deterministic mock coverage is in [`quality_tests.cpp`](../../tests/quality_tests.cpp).

## Exclusive fullscreen

The display-mode enumeration, format/depth checks, fullscreen MSAA capability query, bounded AA fallback, no-silent-Borderless policy, and native HRESULT forwarding remain unchanged. The proxy does not retry a genuine DEVICELOST internally and does not convert it to success.

The new bounded `display_cooperative_transition` and `display_native_attempt` records carry a device lifetime ID and successful Reset epoch. At a cooperative-level transition or native CreateDevice/Reset attempt they record requested/effective mode, exact HRESULT, presentation parameters, device/focus/foreground/active/focus HWNDs, styles, maximize/minimize state, window/client rectangles, and renderer-commit state. Records are transition-driven and capped. The internal game-mode field remains null until a runtime-safe owning pointer is proven.

Static analysis confirms that the game has a native window-mode byte and a real window transition owner; it does not prove that this owner caused the reported loss. Details and evidence grades are in [`exclusive-static-analysis.md`](exclusive-static-analysis.md). The Exclusive result is therefore `READY_FOR_DIAGNOSTIC_RUNTIME`, not a completed fix.

## Preserved renderer baseline

- PreserveMargins v2 remains draw-local: it uses a temporary native WORLD value and exact restoration; packet coordinates are not persistently rewritten.
- PC-VISUAL-PILOT1 CPU-upload provenance remains available. `PS2FoliagePilot.Mode=0` and `Diagnostics=0` stay the defaults; Mode 1 remains blocked and renders Stock.
- Existing resource-generation, COM ownership, FOV/culling, vehicle semantics/reflections, AF, MSAA, frontend preview, cursor, and shutdown paths remain in the regression suite.
- No game executable, proprietary asset, PS2 material, or rendering effect was changed.
