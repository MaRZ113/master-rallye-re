# Master Rallye renderer — R-GFX5-6

**READY_FOR_HUMAN_RUNTIME.** This candidate replaces persistent PreserveMargins packet edits with a draw-local native WORLD copy and immediate exact restore. True Exclusive validates/preserves its chosen display mode across Reset and leaves window ownership to the game/D3D8. HUD stability and real Exclusive startup/Alt+Tab still need manual testing.

[Findings](research/r-gfx5/findings.md), [UI architecture](research/r-gfx5/render-local-ui.md), [Exclusive lifecycle](research/r-gfx5/exclusive-lifecycle.md), [handoff](research/r-gfx5/runtime-handoff.md), [validation](research/r-gfx5/validation.md). Backdrop remains **BACKDROP_ASSET_EXTENSION_REQUIRED**.

Canonical checkout master-rallye-re-general / master. Default new visual features stay Stock; restart after INI edits. [Numeric example](MRRRenderer.ini.example), [opt-in stock-plus preset](research/r-gfx5/stock-plus.ini). Windowed/maximize/restore, Borderless, Centered4x3/preview, AF MIN-only, MSAA, freeze, synchronized FOV, vehicle semantics, native reflection restore and pool/COM lifetime remain covered.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization
```

Run Python capture checks after the native build completes. Generated binaries/logs are ignored; no game deployment occurred. Await P1–P4, D1–D6 and Combined acceptance before R-GFX5 closeout. R-CAM1, photography and HD UI have not begun.

PC-VISUAL-PILOT1: [read-only France1 bush01 diagnostic checkpoint](research/pc-visual-pilot1/final-report.md), **BLOCKED_ON_DRAW_IDENTITY**. `PS2FoliagePilot.Mode=0` and `Diagnostics=0` by default; requested Mode1 remains Stock. F10 content/native-state capture is opt-in and does not authorize an override. [Runtime capture instructions](research/pc-visual-pilot1/runtime-test-plan.md).
