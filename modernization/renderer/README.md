# Master Rallye renderer - R-GFX5-4

**READY_FOR_HUMAN_RUNTIME.** R-GFX5-3 was broadly healthy in the human run. This final fix separates normal Windowed target from OS maximize/restore, and historical margin admission from stable animated packet anchor identity. Only those fixes/diagnostics/regressions changed; see the current Normal/Maximize/Restore/HUD/Menu/Combined handoff.

Backdrop coverage is separately **BACKDROP_ASSET_EXTENSION_REQUIRED**: four-bank content identity and replacement seam are documented; side artwork is unchanged. [Findings](research/r-gfx5/findings.md), [display lifecycle](research/r-gfx5/display-pipeline.md), [UI](research/r-gfx5/widescreen-integration.md), [compatibility](research/r-gfx5/compatibility-fingerprints.md), [backdrop](research/r-gfx5/menu-backdrop.md), [handoff A-H](research/r-gfx5/runtime-handoff.md), [validation](research/r-gfx5/validation.md).

Repository master-rallye-re-general / research/general-re. Only modernization changed. Default new features stay Stock; restart after INI edits. [Numeric example](MRRRenderer.ini.example), [opt-in stock-plus preset](research/r-gfx5/stock-plus.ini). AF MIN-only, synchronized FOV, shadows, pool Reset, learned vehicle/current material proof and exact draw-local TCI restoration remain covered.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -m compileall -q modernization
```

Python capture checks run after the native build completes; generated binaries/logs are ignored. Await human A-H. Next accepted priority: R-CAM1 -> F-PHOTO1 -> HD UI. None starts in this continuation.
