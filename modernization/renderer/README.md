# Master Rallye renderer — R-GFX4-1

Status: **READY_FOR_HUMAN_RUNTIME for Stock classification A/B**. R-GFX3 is CLOSED by the user's final short retest. R-GFX4 adds bounded WORLD tracking and lighting-input research; ViewDependent2D is **BLOCKED_BY_CLASSIFICATION** and forwards Stock even when requested.

Canonical repository master-rallye-re-general, branch research/general-re. All graphics edits stay in modernization/renderer. Frozen R-GFX1/R-GFX2 and retired worktrees are read-only. [Findings](research/r-gfx4/findings.md), [classification](research/r-gfx4/vehicle-classification.md), [lighting decision](research/r-gfx4/lighting-input-decision.md), [human handoff](research/r-gfx4/runtime-handoff.md).

MRRRenderer.ini beside DLL is read once. ConfigVersion1, missing/unknown version=Stock. AF MIN-only, gameplay source90 FOV and Shadow Stock/Off retain R-GFX3 behavior. VehicleReflections.Mode defaults Stock; recognized ViewDependent2D currently logs BLOCKED_BY_CLASSIFICATION. Invalid mode=Stock with reason. Only canonical EXE SHA bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 supports game-specific policy; unknown builds forward and expose unknown classifications.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -v
python -m compileall modernization/renderer
```

F10 records classification fields additively, preserving legacy logical/effective state. Normal gameplay keeps compact tracking only; no per-draw GPU getters or continuous draw JSON. Builds/logs remain ignored. Analyze tools read external inputs and print derived JSON without changing the game/research inputs. No new reflection state, lighting, resource wrapper, backend, weather, postFX or freecam is implemented.
