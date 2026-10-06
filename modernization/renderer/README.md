# Master Rallye renderer — R-GFX4-4

**READY_FOR_HUMAN_RUNTIME.** Continuation #3 fixes D3D-side vehicle semantics: stable object identity across body material mutations and conservative stationary four-wheel admission. R-GFX4-3 FOV/culling and native reflection execution have now passed human observation; this candidate's stationary/brake acceptance is pending.

Canonical master-rallye-re-general, branch research/general-re, starting HEAD69822af. All work stays inside modernization/renderer; no branch/worktree/push/deployment. Retail SHA bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 gates semantics, FOV and effects; unknown builds forward/trace with Stock effects. R-GFX3 stays CLOSED.

[Findings](research/r-gfx4/findings.md), [classification](research/r-gfx4/vehicle-classification.md), [reflection](research/r-gfx4/reflection-prototype.md), [runtime evidence](research/r-gfx4/continuation3-runtime-evidence.json), [handoff](research/r-gfx4/runtime-handoff.md), [validation](research/r-gfx4/validation.md), [machine summary](research/r-gfx4/runtime-summary.json).

Admission can use the existing dynamic path or four repeated full stationary structures. Proven chassis/wheel identity tolerates material-set changes and bounded one-wheel occlusion. Current materials are independently classified;0x102/alpha/wheels stay Stock. ViewDependent2D remains opt-in, opaque0x152 body-only with exact native TCI restoration. Appearance, AF MIN-only, shadow Stock/Off, source45 exclusion, FOV/CPU culling and pool-aware Reset are preserved. ConfigVersion1 is read once; restart after configuration changes.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -m compileall modernization/renderer
python modernization/renderer/tools/analyze_vehicle_identity.py <F10 files>
```

F10 schema1 adds identity source/reason/grace, immutable resource family and independent material/reflection fields. Raw logs/build products stay ignored. Human order: stationary start without movement → brake off cam2 → brake on cam2 with stable IDs and positive modifications → optional cam0/Reset. Stop and return evidence; no reflection tuning or later graphics phase.
