# Master Rallye renderer — R-GFX5 stable baseline

**Status: `STABLE_BASELINE_CHECKPOINTED`.** Windowed live resizing and PreserveMargins v2 passed in-game validation. Windowed and Borderless are supported for continued development. Exclusive recovery after minimize or focus loss remains `DEFERRED_KNOWN_BROKEN`; this does not block R-CAM1 planning.

Read the [stable checkpoint](docs/r-gfx5-stable-checkpoint/README.md) for supported modes, runtime evidence, and the authorized next phase. The [scope decision](docs/r-gfx5-stable-checkpoint/decision.md) records why Exclusive is deferred; [R-EXCL1](docs/r-excl1-deferred.md) retains its evidence and unresolved questions. R-GFX5's full experimental matrix is not closed.

Renderer implementation remains here. R-GFX5-8's [implementation](docs/r-gfx5-8/implementation.md), [Exclusive static analysis](docs/r-gfx5-8/exclusive-static-analysis.md), and [validation record](docs/r-gfx5-8/validation.md) are historical and preserve the state and evidence from that phase. The [numeric INI example](MRRRenderer.ini.example) retains Stock defaults; the [stock-plus preset](research/r-gfx5/stock-plus.ini) remains opt-in. Backdrop status remains **BACKDROP_ASSET_EXTENSION_REQUIRED**.

The PC-VISUAL-PILOT1 [diagnostic checkpoint](research/pc-visual-pilot1/final-report.md) remains **BLOCKED_ON_DRAW_IDENTITY**. CPU-upload provenance, Lock/Unlock observation, resource generations, bounded memory mirrors and F10 diagnostics are preserved. `PS2FoliagePilot.Mode=0` and `Diagnostics=0` remain the safe defaults; requested Mode 1 still renders Stock.

## R-UI1 accepted carousel correction

Race Select and Vehicle Select passed the human test with R-UI1-FINAL. Exact-retail card-row alignment is now automatic under PreserveMargins, without a public option. Old `CarouselAlignment` keys are ignored; Stock/Centered4x3 and unrelated HUD/decorative anchors are unchanged. See [closeout](docs/r-ui1/findings.md).

## R-CAM1-A camera owner probe

Broker/display interoperability is tracked separately in [R-OBS1](docs/r-obs1/findings.md): menu-less exact-retail HWND validation and bounded opener outcomes are corrected, while the reported Windowed stall awaits the controlled hook-isolation runtime comparison. This is not a Broker/Dump runtime acceptance or camera unlock.

R-CAM1-A adds a read-only exact-retail camera-owner observation during an existing F10 frame capture. It records manager/current-camera identity, camera pose and CPU planes, and the effective D3D projection/VIEW. It installs no new game hook and performs no camera or rendering writes. The observation helps qualify race, preview, replay, and camera-cycle ownership before any independent camera control is considered.

Freecam remains **unavailable: `BLOCKED_ON_RACE_EPOCH_CORRELATION`**. R-CAM1-A3c implements an exact-retail read-only lifecycle observer with request/job/owner generations and bounded F10 history. It distinguishes commit results, callback return and errors, and records RaceLimits construction and live admission. The relationship between later owner creation and the completed load, including a same-France1 restart, still needs the [single restart capture](docs/r-cam1-a3c/runtime-test-plan.md). No Freecam configuration, hotkey or pose writes are exposed. See [epoch policy](docs/r-cam1-a3c/race-epoch.md), [native observation hooks](docs/r-cam1-a3c/native-hooks.md), [implementation](docs/r-cam1-a3c/implementation.md), and [validation](docs/r-cam1-a3c/validation.md). A3b's [complete camera scope](docs/r-cam1-a3b/scope-closure.md) and [race ownership](docs/r-cam1-a3b/race-ownership.md) retain the earlier evidence; its proposed scheduler completion bridge is still uninstalled.
