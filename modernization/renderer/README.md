# Master Rallye renderer — R-GFX5-8

**READY_FOR_DIAGNOSTIC_RUNTIME.** Windowed immediate startup resize is causally corrected in source and temporal/hidden-HWND tests: admission now compares the original Reset with the HWND before removing echoed overrides from an unchanged axis. PreserveMargins v2 remains user-confirmed and draw-local. True Exclusive recovery remains unresolved; paired WndProc observations, exact-retail read-only mode-owner validation, and a native cooperative probe immediately before Reset now expose its missing ordering evidence.

[R-GFX5-8 implementation](docs/r-gfx5-8/implementation.md), [Exclusive evidence](docs/r-gfx5-8/exclusive-static-analysis.md), [runtime handoff](docs/r-gfx5-8/runtime-handoff.md), [validation](docs/r-gfx5-8/validation.md). [R-GFX5-7](docs/r-gfx5-7/implementation.md) and `research/r-*` remain historical inputs. Backdrop remains **BACKDROP_ASSET_EXTENSION_REQUIRED**.

Canonical checkout master-rallye-re-general / master, based on the PC-VISUAL-PILOT1 CPU upload provenance handoff. Default new visual features stay Stock; restart after INI edits. [Numeric example](MRRRenderer.ini.example), [opt-in stock-plus preset](research/r-gfx5/stock-plus.ini). Windowed live resize/maximize/restore, Borderless, Centered4x3/preview, AF MIN-only, MSAA, freeze, synchronized FOV, vehicle semantics, native reflection restore and pool/COM lifetime remain in the regression set.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization
```

Run Python capture checks after the native build completes. Generated binaries/logs are ignored; no game deployment occurred. Windowed remains pending a human drag/restore test; Exclusive is diagnostic-only until the next trace correlates cooperative level, Reset, and HWND state. R-GFX5 closeout, R-CAM1, photography and HD UI have not begun.

PC-VISUAL-PILOT1: [read-only France1 bush01 diagnostic checkpoint](research/pc-visual-pilot1/final-report.md), **BLOCKED_ON_DRAW_IDENTITY**. `PS2FoliagePilot.Mode=0` and `Diagnostics=0` by default; requested Mode1 remains Stock. F10 content/native-state capture is opt-in and does not authorize an override. [Runtime capture instructions](research/pc-visual-pilot1/runtime-test-plan.md).
