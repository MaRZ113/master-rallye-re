# Master Rallye renderer — R-GFX4-3

**READY_FOR_HUMAN_RUNTIME.** This continuation separates draw context from temporal frame lifetime and synchronizes gameplay FOV with CPU side planes before common entity submission. R-GFX3 stays CLOSED. Reflection remains the same opt-in, body-only ViewDependent2D prototype; its new game runtime execution and appearance are pending.

Canonical repository master-rallye-re-general, branch research/general-re; starting HEAD25cb58d. Work stays inside modernization/renderer. Frozen reconnaissance/proxy, other research and retired trees are read-only. The user's untracked modernization/renderer.zip is preserved separately.

[Findings](research/r-gfx4/findings.md), [frame lifetime](research/r-gfx4/classifier-frame-lifetime.md), [FOV/culling](research/r-gfx4/fov-culling.md), [classifier](research/r-gfx4/vehicle-classification.md), [Reset](research/r-gfx4/reset-resource-lifetime.md), [reflection](research/r-gfx4/reflection-prototype.md), [human handoff](research/r-gfx4/runtime-handoff.md), [validation](research/r-gfx4/validation.md).

MRRRenderer.ini beside DLL is read once. ConfigVersion1; missing/invalid/unknown version is Stock. AF is stage0 MIN-only, preview source45 remains excluded, Shadow Stock/Off stays intact. VehicleReflections.Mode defaults Stock. Exact EXE SHA bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 gates camera/culling, semantics and reflections; unknown builds only forward/generically trace.

GameplayFOV=true now requires a verified runtime-only CALL seam and matching camera side-plane proof. Disabled FOV installs no hook; missing/failed proof keeps stock projection. The approved in-memory hook changes one5-byte CALL and temporarily four side normals, restoring normals before Present/Reset. It never patches an EXE file or changes source FOV, pose, near/far, visibility radii or individual wheel decisions. No new effects or backend were added.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -m compileall modernization/renderer
python modernization/renderer/tools/inspect_fov_culling.py "..\corpora\retail\MRallye.exe"
```

F10 schema1 is additive: completed-frame and draw-time identity, material/constellation, TCI/native restore, classifier epoch/race-seen, and FOV/culling synchronization. No per-object cull spam or GPU getter was added. Build/raw logs/Ghidra output remain ignored. No game deployment or archive replacement was done.

Human order: A Stock classifier → B VFOV80 edges → C default/cam1..4 and lookback → D successful Reset/relearn → E ViewDependent2D. **Do not start E until A–D pass, and do not judge appearance until candidate/modified/native-write counters are positive.**
