# Master Rallye renderer — R-GFX5 stable baseline

**Status: `STABLE_BASELINE_CHECKPOINTED`.** Windowed live resizing and PreserveMargins v2 passed in-game validation. Windowed and Borderless are supported for continued development. Exclusive recovery after minimize or focus loss remains `DEFERRED_KNOWN_BROKEN`; this does not block R-CAM1 planning.

Read the [stable checkpoint](docs/r-gfx5-stable-checkpoint/README.md) for supported modes, runtime evidence, and the authorized next phase. The [scope decision](docs/r-gfx5-stable-checkpoint/decision.md) records why Exclusive is deferred; [R-EXCL1](docs/r-excl1-deferred.md) retains its evidence and unresolved questions. R-GFX5's full experimental matrix is not closed.

Renderer implementation remains here. R-GFX5-8's [implementation](docs/r-gfx5-8/implementation.md), [Exclusive static analysis](docs/r-gfx5-8/exclusive-static-analysis.md), and [validation record](docs/r-gfx5-8/validation.md) are historical and preserve the state and evidence from that phase. The [numeric INI example](MRRRenderer.ini.example) retains Stock defaults; the [stock-plus preset](research/r-gfx5/stock-plus.ini) remains opt-in. Backdrop status remains **BACKDROP_ASSET_EXTENSION_REQUIRED**.

The PC-VISUAL-PILOT1 [diagnostic checkpoint](research/pc-visual-pilot1/final-report.md) remains **BLOCKED_ON_DRAW_IDENTITY**. CPU-upload provenance, Lock/Unlock observation, resource generations, bounded memory mirrors and F10 diagnostics are preserved. `PS2FoliagePilot.Mode=0` and `Diagnostics=0` remain the safe defaults; requested Mode 1 still renders Stock.

## R-UI1 accepted carousel correction

Race Select and Vehicle Select passed the human test with R-UI1-FINAL. Exact-retail card-row alignment is now automatic under PreserveMargins, without a public option. Old `CarouselAlignment` keys are ignored; Stock/Centered4x3 and unrelated HUD/decorative anchors are unchanged. See [closeout](docs/r-ui1/findings.md).

## R-CAM1-A camera owner probe

R-CAM1-A adds a read-only exact-retail camera-owner observation during an existing F10 frame capture. It records manager/current-camera identity, camera pose and CPU planes, and the effective D3D projection/VIEW. It installs no new game hook and performs no camera or rendering writes. The observation helps qualify race, preview, replay, and camera-cycle ownership before any independent camera control is considered.

Freecam remains **experimental and unavailable pending in-game owner/lifecycle validation**. A source-90 projection does not by itself prove single-player race ownership; no Freecam hotkey or configuration option is exposed in this build. See the [R-CAM1-A camera ownership report](docs/r-cam1-a/camera-ownership.md), [implementation boundary](docs/r-cam1-a/implementation.md), and [runtime test plan](docs/r-cam1-a/runtime-test-plan.md).
