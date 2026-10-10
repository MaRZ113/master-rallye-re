# R-CAM1-A2 implementation boundary

**Result: diagnostic-only. No functional Freecam is exposed.** The camera writer and final VIEW share CameraFrame data, and the existing `GameFov` submission hook is the narrowest candidate integration point. Two conditions remain unproven for a safe opt-in feature: an independently validated active single-player race predicate, and the immediate restoration point for temporary pose fields.

## Read-only diagnostic added

The existing `GameFov::before_submit(index)` callback now keeps a bounded snapshot of the selected `CameraFrame` after exact manager/current-camera identity checks and before `FrustumFrame::begin` writes effective FOV planes. The existing F10 `camera_owner_observation` record includes:

- `pre_submission_camera.available` and a bounded status reason;
- camera pointer and index;
- source angle and viewport;
- the four side planes;
- previous and current poses.

At the gameplay VIEW return, the snapshot is marked unavailable if the selected camera pointer no longer matches. It is cleared at the existing Present/Reset/disable boundaries. Capture is one record per existing camera observation; there is no per-frame dump stream or keyboard logging.

This diagnostic is active only when the existing exact-retail GameplayFOV hook is installed. It uses that already-owned callsite, adds no second interception, changes no renderer or game camera state, and leaves the distributed INI defaults unchanged. `Camera.GameplayFOV=0` remains stock and reports no pre-submission snapshot.

## Not implemented

- No Freecam config section or toggle key.
- No WASD, Numpad or Custom binding resolver.
- No keyboard or mouse capture.
- No CameraFrame pose writes or D3D VIEW override.
- No new gameplay-state read or heuristic.
- No changes to frontend preview, window lifecycle, FOV policy, vehicle semantics, reflections, foliage diagnostics or Exclusive Fullscreen.

The existing `0x006532DD` CALL provides a plausible place to coordinate the camera frame with CPU culling, but the current bridge's established behavior is a pre-submit callback followed by a tail jump to the original traversal. Changing that lifetime to write/restore pose would be a separate behavior change. It must not happen until the pre-submit-to-final-View trace and the post-traversal return are understood and restoration can be bounded to the exact camera generation.

## Gameplay eligibility evidence needed

The next capture should correlate the F10 camera owner with a stock native active-race Broker Dump. Existing race audits use a family of fields including `Race/Type`, `Race/NumPlayers`, `Race/NumNetworkPlayers`, `Race/NetworkSyncActive`, `Race/AttractMode`, `Race/GhostPlayback`, `Race/FinishingType`, `Race/PlaybackReplay` where present, and the selected track/participant state. These fields are candidates for static/runtime correlation, not a renderer-ready predicate. A future implementation must read them without calling a getter that can create entries, and must fail closed when the fields or scope are unavailable.
