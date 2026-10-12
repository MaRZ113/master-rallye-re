# R-CAM1-A3j.4a — validation and runtime handoff

> ABI crash hotfix continuation: see [route-getter-abi-hotfix-a3j4a1.md](route-getter-abi-hotfix-a3j4a1.md) for the corrected getter bridge and the current A3j.4a.1 runtime handoff. The DLL identity below is superseded by the A3j.4a.1 closeout.

**Status:** `ROAD_TARGET_PREVIEW_READY_FOR_RUNTIME`. The production selector, bounded live snapshot path, F10 output and exact-build Reset clear observers are implemented. Static and automated checks do not count as game runtime confirmation.

## Build identity and local artifact

The target is pristine retail `MRallye.exe`, 3,121,214 bytes, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, PE32/I386, ImageBase `0x00400000`. Direct `.text` extraction verified the three Physics Observer contexts/calls, RaceLine getter context/call target, and all three clear-store contexts. The optional Python PE test repeats this check against `MR_PRISTINE_EXE` or the conventional pristine path.

Build output is local and ignored at `modernization/renderer/.build-msvc/Release/d3d8.dll`; do not include it in source archives or commits. The A3j.4a.1 hotfix DLL is 2,121,728 bytes, SHA-256 `53a1de53047134791e9e811dc7a727d90ab92f247088ab4c012f661c2a89891d`, PE32/I386 with the three expected exports and no recursive `d3d8.dll` import. Build/package checks establish PE structure only. Runtime acceptance has not been collected for this A3j.4a.1 build.

## One-session test

Use the pristine executable with the freshly built renderer. In `MRRenderer.ini` set:

```ini
[Trace]
Enabled=1

[PhysicsObserver]
Enabled=1
RoadTargetPreviewEnabled=1
RoadTargetPreviewRadius=60.0
```

Start one offline France1 race, drive on clear road, invoke one normal in-game vehicle Reset, and drive briefly after recovery. Pause normally for a short interval, activate Freecam, fly to a recognizable road section near the target foliage and press F10 once. Exit normally so the bounded session summary is written. Do not restart the race, invoke Reset programmatically, teleport, or alter progress/pause/physics data. Submit one new `session-*.jsonl` and one `frame-*.jsonl` from `MRRRenderer/logs`.

First require setup to report `requested=true`, `exact_retail_build=true`, `installed=true`, `reason="exact_callsites_installed_read_only"`, and `read_only_game_data=true`. On normal shutdown, require `patch_restored=true`. The session should include a `physics_probe_clear_writer_event` with `apply_flag_before=1` for the observed participant, plus bounded consumer/substep records. If there is no clear event with a set flag, retain the exact event sequence and do not infer a responsible branch. The frame should show `route_source="native_live_raceline"`, count 448, stride 72, offset 56, matching current race/owner generation, a finite selected marker, and `physical_placement_verified=false`.

Pause interpretation requires a fresh pause sample age at most 500 ms. A controller/substep/clear record labeled `paused` proves that instrumented path ran while paused in this session. A zero counter without a fresh pause-state sample is inconclusive. `substep_phase_records_while_paused` is a count of bounded phase callbacks, not a count of unique physical integration steps.

## Safety and limits

The observer reads physics and Broker data only. It patches only verified executable code bytes while peer threads are suspended and quiescent; exact byte ownership is required for restore. The bridges replay all original instructions. A failed or foreign patch remains disabled and pinned; setup emits a per-context failure reason. No chassis setter is called by injected code, no transform/apply flag or other game data is written, and no teleport control exists. Freecam, camera-frame ownership, bookmarks, FOV, roll and Clean View behavior are unchanged.

No live RaceLine snapshot, new clear-writer attribution, pause result, physical placement guarantee, or safe one-shot write boundary is claimed until the human capture is reviewed. The next step after that capture is to classify the exact observed stock lifecycle; physical teleport remains a separately gated phase.
