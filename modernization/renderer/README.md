# Master Rallye renderer — R-GFX5-3

**READY_FOR_HUMAN_RUNTIME.** Previous human run accepted Borderless/Alt+Tab, native resolution, Centered4x3, AF16/MSAA4 and MenuFreezeFix. This candidate fixes Reset echoes/final shutdown, centers Windowed, adds optional cursor idle hiding and numeric INI, corrects the separate preview camera and moves HUD margins to actual packet consumption. Hardened EXE FOV/vehicle owners validate locally; runtime remains pending.

Backdrop coverage is separately **BACKDROP_ASSET_EXTENSION_REQUIRED**: four-bank content identity and replacement seam are documented; side artwork is unchanged. [Findings](research/r-gfx5/findings.md), [display lifecycle](research/r-gfx5/display-pipeline.md), [UI](research/r-gfx5/widescreen-integration.md), [compatibility](research/r-gfx5/compatibility-fingerprints.md), [backdrop](research/r-gfx5/menu-backdrop.md), [handoff A-H](research/r-gfx5/runtime-handoff.md), [validation](research/r-gfx5/validation.md).

Repository master-rallye-re-general / research/general-re. Only modernization changed. Default new features stay Stock; restart after INI edits. [Numeric example](MRRRenderer.ini.example), [opt-in stock-plus preset](research/r-gfx5/stock-plus.ini). AF MIN-only, synchronized FOV, shadows, pool Reset, learned vehicle/current material proof and exact draw-local TCI restoration remain covered.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -m compileall -q modernization
```

Python capture checks run after the native build completes; generated binaries/logs are ignored. Await human A-H. Next accepted priority: R-CAM1 -> F-PHOTO1 -> HD UI. None starts in this continuation.
