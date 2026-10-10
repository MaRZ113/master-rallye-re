# Master Rallye renderer — R-GFX5 stable baseline

**Status: `STABLE_BASELINE_CHECKPOINTED`.** Windowed live resizing and PreserveMargins v2 passed in-game validation. Windowed and Borderless are supported for continued development. Exclusive recovery after minimize or focus loss remains `DEFERRED_KNOWN_BROKEN`; this does not block R-CAM1 planning.

Read the [stable checkpoint](docs/r-gfx5-stable-checkpoint/README.md) for supported modes, runtime evidence, and the authorized next phase. The [scope decision](docs/r-gfx5-stable-checkpoint/decision.md) records why Exclusive is deferred; [R-EXCL1](docs/r-excl1-deferred.md) retains its evidence and unresolved questions. R-GFX5's full experimental matrix is not closed.

Renderer implementation remains here. R-GFX5-8's [implementation](docs/r-gfx5-8/implementation.md), [Exclusive static analysis](docs/r-gfx5-8/exclusive-static-analysis.md), and [validation record](docs/r-gfx5-8/validation.md) are historical and preserve the state and evidence from that phase. The [numeric INI example](MRRRenderer.ini.example) retains Stock defaults; the [stock-plus preset](research/r-gfx5/stock-plus.ini) remains opt-in. Backdrop status remains **BACKDROP_ASSET_EXTENSION_REQUIRED**.

The PC-VISUAL-PILOT1 [diagnostic checkpoint](research/pc-visual-pilot1/final-report.md) remains **BLOCKED_ON_DRAW_IDENTITY**. CPU-upload provenance, Lock/Unlock observation, resource generations, bounded memory mirrors and F10 diagnostics are preserved. `PS2FoliagePilot.Mode=0` and `Diagnostics=0` remain the safe defaults; requested Mode 1 still renders Stock.

## R-UI1 accepted carousel correction

Race Select and Vehicle Select passed the human test with R-UI1-FINAL. Exact-retail card-row alignment is now automatic under PreserveMargins, without a public option. Old `CarouselAlignment` keys are ignored; Stock/Centered4x3 and unrelated HUD/decorative anchors are unchanged. See [closeout](docs/r-ui1/findings.md).

## R-CAM1-A camera owner probe

R-CAM1-A adds a read-only exact-retail camera-owner observation during an existing F10 frame capture. It records manager/current-camera identity, camera pose and CPU planes, and the effective D3D projection/VIEW. It installs no new game hook and performs no camera or rendering writes. The observation helps qualify race, preview, replay, and camera-cycle ownership before any independent camera control is considered.

Freecam remains **unavailable: `BLOCKED_ON_LIVE_RACE_OWNERSHIP`**. R-CAM1-A3b maps native camera consumption through EndFrame and the scheduler's immediate caller. Post-traversal and post-FinalizeCamera restoration are both too early. The remaining admission proof must associate the live RaceLimits owner with the current successful scene epoch, including restart/error paths; Source90, a vtable or zero countdown cannot authorize camera writes. No Freecam hook, hotkey or configuration option is exposed. See [complete camera scope](docs/r-cam1-a3b/scope-closure.md), [race ownership](docs/r-cam1-a3b/race-ownership.md), [validation](docs/r-cam1-a3b/validation.md), and the [narrow ownership handoff](docs/r-cam1-a3b/runtime-test-plan.md). The [A3 findings](docs/r-cam1-a3/findings.md) retain the earlier investigation state.
