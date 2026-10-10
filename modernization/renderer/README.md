# Master Rallye renderer — R-GFX5 stable baseline

**Status: `STABLE_BASELINE_CHECKPOINTED`.** Windowed live resizing and PreserveMargins v2 passed in-game validation. Windowed and Borderless are supported for continued development. Exclusive recovery after minimize or focus loss remains `DEFERRED_KNOWN_BROKEN`; this does not block R-CAM1 planning.

Read the [stable checkpoint](docs/r-gfx5-stable-checkpoint/README.md) for supported modes, runtime evidence, and the authorized next phase. The [scope decision](docs/r-gfx5-stable-checkpoint/decision.md) records why Exclusive is deferred; [R-EXCL1](docs/r-excl1-deferred.md) retains its evidence and unresolved questions. R-GFX5's full experimental matrix is not closed.

Renderer implementation remains here. R-GFX5-8's [implementation](docs/r-gfx5-8/implementation.md), [Exclusive static analysis](docs/r-gfx5-8/exclusive-static-analysis.md), and [validation record](docs/r-gfx5-8/validation.md) are historical and preserve the state and evidence from that phase. The [numeric INI example](MRRRenderer.ini.example) retains Stock defaults; the [stock-plus preset](research/r-gfx5/stock-plus.ini) remains opt-in. Backdrop status remains **BACKDROP_ASSET_EXTENSION_REQUIRED**.

The PC-VISUAL-PILOT1 [diagnostic checkpoint](research/pc-visual-pilot1/final-report.md) remains **BLOCKED_ON_DRAW_IDENTITY**. CPU-upload provenance, Lock/Unlock observation, resource generations, bounded memory mirrors and F10 diagnostics are preserved. `PS2FoliagePilot.Mode=0` and `Diagnostics=0` remain the safe defaults; requested Mode 1 still renders Stock.

## R-UI1 accepted carousel correction

Race Select and Vehicle Select passed the human test with R-UI1-FINAL. Exact-retail card-row alignment is now automatic under PreserveMargins, without a public option. Old `CarouselAlignment` keys are ignored; Stock/Centered4x3 and unrelated HUD/decorative anchors are unchanged. See [closeout](docs/r-ui1/findings.md).

## R-CAM1-A camera owner probe

[R-OBS1b closeout](docs/r-obs1b/closeout.md) makes hook-free display handling standard. The A3d request confirms that the combined baseline passed human Broker/native Dump/F10 testing, alongside accepted Windowed/Borderless/cursor/lifecycle behavior, ordinary Restart and legitimate idle Attract. Those baseline behaviors are accepted; the newly built A3d DLL requires its own regression smoke test. No diagnostic flag or message-hook INI toggle is required.

R-ATTR1's exact-retail process-memory guard remains unchanged; no disk EXE patch or global Attract override is used. The exact internal mechanism of the old hook-enabled Broker stall is UNKNOWN and deferred.

R-CAM1-A adds a read-only exact-retail camera-owner observation during an existing F10 frame capture. It records manager/current-camera identity, camera pose and CPU planes, and the effective D3D projection/VIEW. It installs no new game hook and performs no camera or rendering writes. The observation helps qualify race, preview, replay, and camera-cycle ownership before any independent camera control is considered.

R-CAM1-A3d implements opt-in Freecam with a hierarchical live race certificate and a scope shared with GameFov. Default is OFF. Only pristine retail, offline France1, one human and one camera are admitted. WASD, physical Numpad and Custom controls are available. Restoration follows the scheduler return, after particles and EndFrame. See [implementation](docs/r-cam1-a3d/implementation.md), [validation](docs/r-cam1-a3d/validation.md) and [first flight](docs/r-cam1-a3d/runtime-handoff.md). In-game flight is **PENDING HUMAN VALIDATION**.

A3c and A3b documents and the inspector's default output are historical evidence, not current feature status. The two actual A3c captures prove false poisoning at event 4 and owner/HUD scene-generation differences; they lost subsequent valid success callbacks. A3d does not turn those gaps into runtime proof. Use `inspect_camera_scope.py --a3d` for the current static map. Older [epoch](docs/r-cam1-a3c/race-epoch.md) and [scope](docs/r-cam1-a3b/scope-closure.md) findings are retained.
