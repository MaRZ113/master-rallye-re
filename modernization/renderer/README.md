# Master Rallye renderer — R-GFX5-1

**READY_FOR_HUMAN_RUNTIME.** R-GFX4 accepted by the human on2026-10-07. This candidate adds opt-in Stock/Windowed/Borderless/ExclusiveFullscreen presentation, modern dimensions, centered or margin-preserving widescreen UI, capability-checked native D3D8 MSAA and a separate exact-build process-memory freeze fix. Gamma and draw-distance controls are deferred after research.

Repository master-rallye-re-general, branch research/general-re, starting HEAD6ede833122bcd32ffb6223548c88587650d0539d. All changes under modernization; no new branch/worktree/push/deployment. Exact pristine SHA bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 gates new behavior. Unknown EXEs forward/trace with Stock effects. Game files and supplied patchers unchanged on disk.

[Findings](research/r-gfx5/findings.md), [display/Reset](research/r-gfx5/display-pipeline.md), [reference analysis](research/r-gfx5/third-party-widescreen-analysis.md), [UI](research/r-gfx5/widescreen-integration.md), [MSAA](research/r-gfx5/msaa.md), [freeze](research/r-gfx5/compatibility-freeze.md), [handoff](research/r-gfx5/runtime-handoff.md), [validation](research/r-gfx5/validation.md), [machine summary](research/r-gfx5/runtime-summary.json).

Missing config and example INI keep new features Stock/off. Restart after edits. [stock-plus.ini](research/r-gfx5/stock-plus.ini) is a comparison candidate. Previous AF MIN-only, gameplay VFOV/CPU culling, frontend exclusion, shadows and learned vehicle/native TCI contracts remain passing.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -m compileall -q modernization
```

Run Python capture tests after native suites finish; they verify current executable hashes. Build outputs, synthetic logs and analysis projects are ignored. Human native-resolution imagery/UI/hardware MSAA/task switching checks still required. Stop before R-CAM1/F-PHOTO1.
