# Master Rallye renderer — R-GFX5-7

**READY_FOR_DIAGNOSTIC_RUNTIME.** PreserveMargins v2 is confirmed by the user's runtime retest and keeps animated UI placement stable through a draw-local native WORLD copy and immediate exact restore. Windowed now distinguishes the latest accepted normal client target from the OS-owned maximized client and admits live resizing only when the HWND and game Reset agree. Exclusive still needs a bounded runtime capture: the latest report has CreateDevice and an initial Reset succeeding, followed by `D3DERR_DEVICELOST` from `TestCooperativeLevel` and the game's Reset.

[R-GFX5-7 implementation](docs/r-gfx5-7/implementation.md), [Exclusive evidence](docs/r-gfx5-7/exclusive-static-analysis.md), [runtime handoff](docs/r-gfx5-7/runtime-handoff.md), [validation](docs/r-gfx5-7/validation.md). Earlier [findings](research/r-gfx5/findings.md), [UI architecture](research/r-gfx5/render-local-ui.md), and [Exclusive lifecycle](research/r-gfx5/exclusive-lifecycle.md) remain historical inputs. Backdrop remains **BACKDROP_ASSET_EXTENSION_REQUIRED**.

Canonical checkout master-rallye-re-general / master, based on the PC-VISUAL-PILOT1 CPU upload provenance handoff. Default new visual features stay Stock; restart after INI edits. [Numeric example](MRRRenderer.ini.example), [opt-in stock-plus preset](research/r-gfx5/stock-plus.ini). Windowed live resize/maximize/restore, Borderless, Centered4x3/preview, AF MIN-only, MSAA, freeze, synchronized FOV, vehicle semantics, native reflection restore and pool/COM lifetime remain in the regression set.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization
```

Run Python capture checks after the native build completes. Generated binaries/logs are ignored; no game deployment occurred. Windowed remains pending a human drag/restore test; Exclusive is diagnostic-only until the next trace correlates cooperative level, Reset, and HWND state. R-GFX5 closeout, R-CAM1, photography and HD UI have not begun.

PC-VISUAL-PILOT1: [read-only France1 bush01 diagnostic checkpoint](research/pc-visual-pilot1/final-report.md), **BLOCKED_ON_DRAW_IDENTITY**. `PS2FoliagePilot.Mode=0` and `Diagnostics=0` by default; requested Mode1 remains Stock. F10 content/native-state capture is opt-in and does not authorize an override. [Runtime capture instructions](research/pc-visual-pilot1/runtime-test-plan.md).
