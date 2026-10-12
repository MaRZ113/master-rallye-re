# R-CAM1-A3j.4 — Road-only vehicle teleport engineering decision

**Status: `BLOCKED_ON_SPECIFIC_ROAD_TELEPORT_INVARIANT`**

This pass narrowed the question to a France1 RaceLine anchor and the exact-pristine physics route. It did not add a teleport control or write to game state. The primary blocker is **no verified Freecam-to-live-RaceLine selection**: the game exposes a route collection to its recovery routine, but no safe, generation-bound route reference is available to the Freecam request path. Two independent commit gates also remain: a safe one-shot request/flag protocol and sufficient physical-reset guarantees for an arbitrary selected RaceLine sample.

## Build and evidence boundary

- Retail executable: `D:\Game\Master Rallye\MRallye.exe`, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, PE32/I386, ImageBase `0x00400000`.
- Pristine installed `Data.sma`: 274,620,035 bytes, SHA-256 `948121b1a0207c4b4a2127fd7f42fb187327eb5b41123f70803eaed0c05da806`.
- Extracted pristine `DataScene/RaceTest/France1.xml`: SHA-256 `beaa2180912ffd54f313a149962e295f9894239014481d2c7ba2db84fb1e08e1`.
- Ghidra 12.1.4 bridge queries against the existing exact-retail program were read-only. Transient query output is under the ignored `modernization/renderer/recon_scratch/a3j3b/` directory.
- A3j.3a runtime evidence is reused; no new game session or physics write was performed.

## What is established about the road candidate

The pristine France1 scene contains an ordered `RaceLine` marker list with 448 positions, ordinals `0..447`. Exact-retail code consumes marker records with stride `0x48` and reads position at record `+0x38` (`X/Y/Z`). France1 consecutive sample distances in the extracted scene range from 12.31 to 31.46 units, with a median of 20.02. This makes the proposed 60-unit cap plausible as a search limit, but it is not yet a validated safe default; it spans roughly three median sample intervals and measures camera-to-sample distance, not road clearance.

The A3j.3a observed post-recovery chassis position was approximately `(-1629.48999, 51.494225, 153.210007)`. Its nearest point in the pristine France1 source list is ordinal 2 at `(-1629.49, 50.49, 153.21)`, about 1.004 units away in Y and effectively coincident in X/Z. This is a strong source-to-runtime positional match, but the capture did not record the selected RaceLine ordinal; therefore ordinal 2 is a `STATIC_INFERENCE`, not a runtime-observed selection.

`ResetManager_Recovery_004CCC90` (VA `0x004CCC90`, RVA `0x000CCC90`) takes its sample from the current per-car `Progress`/`LastMarker` state. It builds orientation from adjacent RaceLine positions (using a preceding point at the final list entry), applies the stock vertical offset, and publishes the transform through `Controller/CarN`. It does not accept a Freecam position.

`ResetRecovery_AdjustForNearbyCars_004CD200` (VA `0x004CD200`, RVA `0x000CD200`) receives an already selected sample ordinal. It examines other participants and can step that ordinal backward when the candidate is within its car-distance threshold and fails its direction test. It does **not** search the RaceLine for the sample nearest an arbitrary external position, and it does not validate static obstacles, foliage, chassis footprint, or road-surface contact.

The reset's collision-service boolean query returns false in this exact call path, so its hit-position and hit-normal getters do not provide a measured ground surface. RaceLine is confirmed as a race-progress route; the executable evidence does not prove every sample lies within a collision-free paved road footprint. The route is a promising road anchor source, not a general road/clearance oracle.

## Why the native transaction is not ready to trigger

The stock controller path is real: the A3j.3a capture showed the controller transform consumer applying the stock recovery matrix to the physical chassis and synchronizing previous position. Static analysis and the same capture support the translational-velocity reset. The controller consumer is called at VA `0x00443827` / RVA `0x00043827` before the per-car wheel routines, and the captured controller/substep events used one thread in that session.

That is not yet an authorized teleport commit boundary:

- The sampled call order does not prove global reset-manager/physics-job ordering, behavior while paused, or that no other physics job owns relevant contact state.
- `Controller/CarN` apply byte `P+0x33` is level-triggered. The consumer at `0x00444AE0` reads it but does not clear it; ResetManager clear paths include VAs `0x004CD1DE`, `0x004CCC70`, and `0x004CD1A1`. A3j.3a observed a later clear, but did not attribute the writer branch or establish a one-shot protocol for a new request. Setting the byte and hoping for a later clear could apply the transform repeatedly.
- The stock helper resets selected wheel/controller state, but direct wheel poses, full suspension/contact state, warm-start/manifold invalidation, and broadphase refresh remain unproven. The runtime observer sampled only selected wheel words. One successful stock recovery does not prove that every RaceLine point is safe for relocation.
- A3j.3a proved a stable `PlayerType=1` candidate and pointer chain in one exact-retail France1 session. The future request still needs current-session owner/lifetime validation and must reject AI, stale, or ambiguous ownership.

`RaceStartPlacement_0048EB40` (VA `0x0048EB40`, RVA `0x0008EB40`) uses `StartArea` to publish `Race/CarN/Transform` values during race setup. Its optional `Physics/Car0/Transform` path also publishes race transform data; the reviewed function is not a live physical-body relocation service after physics registration.

## Decision

Do not add `VehicleTeleportEnabled`, a T binding, a queued write, or a DLL candidate in A3j.4. Do not alter `Progress`, `LastMarker`, `ResetNo`, `P+0x33`, chassis bytes, or wheel records. Do not call a pose helper from the D3D/render thread. There is no Undo path, so a failed or partially applied move would leave no verified recovery transaction.

This is a specific engineering stop, not a claim that a road-only prototype is impossible. The current evidence supports implementing a pure nearest-point selector once it is fed the **live, validated France1 RaceLine collection**; it does not yet support connecting that selector to a native physical commit.

## Shortest next proof

Extend the existing exact-retail observer in read-only mode for one France1 session. At the native recovery entry and the already instrumented controller boundary, record only bounded values:

1. Active RaceLine list begin/end, count, and a bounded fingerprint of the `+0x38` positions; selected ordinal and resulting matrix translation from a normal stock recovery. Match the live list to the pristine France1 source and confirm or refute the ordinal-2 positional inference.
2. Freecam position and the nearest live sample/distance as a diagnostic only; do not queue or apply it.
3. Whether the controller callback occurs during native pause and the exact clear-writer branch for the normal stock recovery flag. Preserve the current exact-byte and thread-quiescence installation checks.

This establishes the active route identity and the timing/flag facts without moving a vehicle. If it passes, review the exact native commit option and contact guarantees before creating any write-enabled candidate. The first eventual human test remains a clear road stretch, with manual resume, slow steering/braking checks, and one ordinary stock Reset. Do not use foliage as the first target.

## Validation and repository state

The France1 XML parser check found 448 finite, ordered positions with continuous ordinals and no missing `Marker Pos` values. The exact-retail executable hash matched the required SHA-256. No source code, executable, game asset, or existing A3j research document was modified. A3j.4 decision artifacts are limited to this Markdown file and its JSON companion; the handoff archive contains only those two files.

No Python/native suites or build were run because this result adds documentation only and deliberately produces no teleport candidate. `git diff --check` reported no errors; it emitted only line-ending conversion warnings for pre-existing modified files. No commit or push was made.
