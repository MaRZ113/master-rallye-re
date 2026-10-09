# R-CAM1-A camera owner runtime validation

**Purpose:** collect a small set of read-only owner observations needed to decide whether an exact-build, single-player Freecam gate and transient CPU/D3D camera integration can be proven. This procedure does not test a Freecam because no movement feature is enabled in this candidate.

## Setup

Use the exact pristine retail executable (SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`) with the R-CAM1-A `d3d8.dll` candidate. Prefer Windowed (`Display.Mode=1`) or Borderless (`Display.Mode=2`); do not use known-broken Exclusive recovery. Keep all other renderer options unchanged during the first comparison.

Enable the existing trace if needed:

```ini
[Trace]
Enabled=1
FrameSummaries=1

[Camera]
GameplayFOV=0
```

No Freecam INI option or hotkey exists. F10 is the existing one-frame capture key and remains reserved. Each capture should produce the ordinary `frame-...jsonl` plus a `camera_owner_observation` line in its matching session JSONL, joined by `device` and `frame`. Do not send or commit continuous raw logs; retain only the small set of captures listed below.

## Capture sequence

1. **Frontend preview:** in the main menu or Quick Race vehicle preview, press F10 once while the car preview is visible. Record the screen/context and expected source-45 family.
2. **France1 race:** start a single-player Quick Race with default camera. Once the scene is stable, press F10 once.
3. **Stock camera variants:** cycle through each available stock camera mode and press F10 once per settled mode. Include pause/unpause only if the game retains its camera owner while paused.
4. **Replay or Attract:** if readily accessible, collect one capture during replay playback and one during Replay Theatre/Attract. Do not spend time bypassing normal menus to reach these states.
5. **Transition lifetime:** return to the frontend, re-enter France1, and take one new default-camera capture. This checks whether manager/current-camera pointers change or are reused across the normal transition.
6. **Optional FOV comparison:** only after the first set is complete, repeat the default-race capture with the existing GameplayFOV enabled. This is a projection/culling regression observation, not a Freecam test.

## What to inspect

For each `camera_owner_observation`, compare:

- executable identity, device and frame;
- caller VA/RVA (`0x0053FA75` / `0x0013FA75`);
- `projection_family` and the F10 frame's logical/effective projection setters;
- manager count and its validity, all readable camera pointers, renderer singleton/holder/current-camera read status, `camera_index`, and `owner_match`;
- camera viewport against the game client/active viewport;
- camera source angle, side planes, previous/current poses, and finite values;
- D3D VIEW against the camera pose pair and expected movement as the stock selector changes;
- whether pointer/count/index/projection family distinguishes the supported race path from every sampled unsupported context;
- whether the selected camera remains stable through pause, camera cycling, Reset/resize, and re-entry.

The event records both requested logical projection (the camera-family signal) and effective native D3D projection, plus input VIEW. It does not include raw input, alter the game, or record every draw. The frame file contains the wrapper's corresponding transform events; use the session event's `device` + `frame` to correlate it.

## PASS / FAIL decision

**Diagnostic pass** requires all of the following:

- all expected read flags and the selected manager/current-camera identity are internally consistent during the normal single-player race;
- camera pose, planes, viewport and D3D transform data are finite and stable enough to reconstruct a single effective owner;
- stock camera cycling either preserves that owner safely or produces a predictable owner transition;
- the supported race contexts have a reliable exact-runtime discriminator that rejects every sampled preview, replay, attract, cinematic, and multi-camera context. A source-90 projection, manager count of one, or camera index zero alone is not sufficient;
- no observed pointer reuse or transition invalidates the documented identity/lifetime checks.

If any unsupported context has the same candidate discriminator as a race, or a required owner/pose read is unavailable, the gate **fails closed** and the Freecam stays disabled. Static evidence and F10 traces do not prove in-game movement or visual correctness.

## Evidence to retain

For a diagnostic pass or failure, keep:

- one session JSONL and matching F10 frame files for the frontend preview, each distinct race owner, and each accessible unsupported camera context;
- the exact executable SHA and candidate DLL SHA from the session header;
- a short note for each capture identifying screen/state, active stock camera selection, focus/pause/reset condition, and whether all pointer-read flags were true.

Raw captures remain local diagnostic data and are not added to the source handoff archive.
