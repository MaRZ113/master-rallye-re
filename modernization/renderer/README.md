# Master Rallye renderer — R-GFX4-2

**READY_FOR_HUMAN_RUNTIME.** R-GFX3 stays CLOSED. R-GFX4 continuation fixes pool-aware Reset, classifies dynamic chassis/four-wheel constellations and adds opt-in opaque FVF152 body reflection-vector lookup. Stock remains default; the new candidate has no human runtime pass yet.

Canonical repo master-rallye-re-general, branch research/general-re. Edits only modernization/renderer; frozen reconnaissance/proxy and retired trees stay read-only. [Findings](research/r-gfx4/findings.md), [classifier](research/r-gfx4/vehicle-classification.md), [Reset](research/r-gfx4/reset-resource-lifetime.md), [reflection](research/r-gfx4/reflection-prototype.md), [handoff](research/r-gfx4/runtime-handoff.md), [validation](research/r-gfx4/validation.md).

MRRRenderer.ini beside DLL is read once. ConfigVersion1; missing/invalid/unknown version=Stock. AF stage0 MIN-only, source90 gameplay FOV/preview45 exclusion and Shadow Stock/Off retain tested R-GFX3 behavior. VehicleReflections.Mode=Stock or ViewDependent2D. Only exact EXE SHA bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 supports target-specific behavior; unknown builds forward/generically trace with no semantic classification/reflection.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -m compileall modernization/renderer
```

F10 schema1 fields are additive: draw-time and completed-frame identity, material/constellation, requested/effective TCI, temporary native setter and restore result. Normal gameplay keeps bounded state/tracking/counters without per-draw GPU queries or draw JSON. Classifier and restore remain independent of trace recording availability. Tools read external logs/assets and print derived summaries. Build/log products are ignored; no game deployment, new lighting, resource wrapping, vertex rewrite, shader, backend, cubemap, weather, postFX or freecam is included.

Human sequence: Stock A Reset/relearn **must pass first**; then opt-in B normal-view, C look-back, D unchanged scenery, E multiple cars. Do not tune reflection aesthetics before recording evidence.
