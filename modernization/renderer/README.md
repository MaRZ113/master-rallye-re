# Master Rallye renderer - R-GFX5-2

**READY_FOR_HUMAN_RUNTIME.** R-GFX4 is accepted; prior MSAA4 and pristine MenuFreezeFix are human-confirmed. This continuation fixes display plan/commit ordering, Windowed size ownership and the actual UI projection caller. PreserveMargins implementation and MSAA selection are retained; new visual/display results are pending.

Repository master-rallye-re-general, branch research/general-re. All graphics changes under modernization; no branch/worktree/push or game disk changes. Display/MSAA/AF are generic; freeze and Centered UI use feature-local owner validation on known or compatible unknown EXEs. Camera/culling, packet margins, shadow and vehicle semantics remain exact-profile gated. See [compatibility](research/r-gfx5/compatibility-fingerprints.md).

[Findings](research/r-gfx5/findings.md), [display/Reset](research/r-gfx5/display-pipeline.md), [reference analysis](research/r-gfx5/third-party-widescreen-analysis.md), [UI](research/r-gfx5/widescreen-integration.md), [MSAA](research/r-gfx5/msaa.md), [freeze](research/r-gfx5/compatibility-freeze.md), [handoff](research/r-gfx5/runtime-handoff.md), [validation](research/r-gfx5/validation.md), [machine summary](research/r-gfx5/runtime-summary.json).

Missing config and example INI keep new features Stock/off. Restart after edits. [stock-plus.ini](research/r-gfx5/stock-plus.ini) is a comparison candidate. Previous AF MIN-only, gameplay VFOV/CPU culling, frontend exclusion, shadows and learned vehicle/native TCI contracts remain passing.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -q
python -m compileall -q modernization
```

Run Python capture tests after native suites finish; they verify current executable hashes. Build outputs, synthetic logs and analysis projects are ignored. Human narrow display/UI/combined/task-switching retest A-G is still required. Stop before R-CAM1/F-PHOTO1.
