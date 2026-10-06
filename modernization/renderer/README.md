# Master Rallye renderer — R-GFX4-5

**READY_FOR_HUMAN_RUNTIME.** Continuation #4 separates vehicle discovery from stable render semantics to address whole-AI-body reflection blinking. Existing dynamic/stationary four-wheel proof teaches exact geometry/material signatures; eligible submitted body draws can then retain ViewDependent2D despite lost live constellation proof. Appearance and native draw-local TCI override/restore are unchanged.

Canonical repository master-rallye-re-general, branch research/general-re, starting HEAD a6fc83d245902458019262b6574175c7eda3391a. All graphics changes stay inside modernization/renderer. No new branch/worktree/push or deployment; user renderer.zip is preserved. Exact retail SHA bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 gates semantics; unknown builds forward/trace with Stock effects. R-GFX3 stays CLOSED.

[Classification/lifetime](research/r-gfx4/vehicle-classification.md), [reflection](research/r-gfx4/reflection-prototype.md), [input evidence](research/r-gfx4/continuation4-runtime-evidence.json), [handoff](research/r-gfx4/runtime-handoff.md), [validation](research/r-gfx4/validation.md), [machine summary](research/r-gfx4/runtime-summary.json).

Learned proof is full-key and generation-aware, independent of WORLD/object IDs. Every draw still requires race context, opaque FVF0x152 and stock env material. Wheels/brakes/alpha/glass/unproven static geometry remain Stock. Reset/scene clears semantics and tracks; MANAGED resource metadata survives and can relearn. F10 records live versus learned provenance, first learning proof and compact counters. ConfigVersion1 is read once; restart after configuration edits.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -m compileall modernization/renderer
python modernization/renderer/tools/analyze_vehicle_draws.py <F10 files>
```

Human retest: four cars20–30 seconds → B-ai-multicar F10 → C-ai-edge F10 → quick Tata brake regression → actual successful Reset. Return visual notes and exact-candidate logs; no later graphics phase is started.
