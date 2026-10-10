# R-CAM1-A2 camera diagnostic handoff

This is a short read-only capture to close camera timing and gameplay-state evidence. It does not test or enable Freecam.

## Setup

Use the hash-verified pristine retail executable with the current renderer candidate. Keep the accepted Windowed or Borderless display settings and other quality settings unchanged. For the new pre-submit snapshot, enable the existing hook:

```ini
[Renderer]
ConfigVersion=1

[Camera]
GameplayFOV=1
VerticalFOVDegrees=75.0

[Trace]
Enabled=1
```

The FOV value is the existing supported setting; the diagnostic itself does not select or change it. Start F10 capture before each observation.

## Captures

1. In the frontend vehicle preview, capture one F10 frame. Record the screen state and confirm the observation is Source45 or is rejected by its existing exact callsite gate.
2. Enter a normal France1 Quick Race, before Results. Capture one F10 frame on the active gameplay view. While still in the live race, use the existing stock native Debug→Dump only if that established read-only workflow is available; do not request a dump after Results. Preserve the Broker rows needed to check the active-race candidate fields listed in `implementation.md`.
3. Exit normally to the frontend and capture one F10 frame. Record whether any race Broker values persist in a separately available safe state capture; do not treat stale values as proof of active gameplay.

Keep only the F10 session and matching frame files needed for analysis. The proxy emits the pre-submit record inside the existing bounded camera-owner event. Do not capture continuous frame logs.

## PASS / FAIL

**Camera-order PASS** requires the France1 observation to show `pre_submission_camera.available=true`, index zero, and the same camera pointer as the final CameraFrame. The viewport and both pose endpoints should remain unchanged through traversal; the plane difference is expected when GameplayFOV is enabled. Reconstruct the D3D View from the previous/current pose and interpolation contract, checking orientation basis as well as position. A pointer/status mismatch, incomplete read, unexpected pose rewrite, or View inconsistency is FAIL and keeps all pose writes disabled.

**Gameplay-state evidence PASS** requires a fresh active-race Broker snapshot matching the normal one-player offline Quick Race context, with replay/attract/network flags absent or false and a track/participant record consistent with France1. Frontend and post-race observations must not independently satisfy the proposed gate. If the same candidate values remain after teardown, or replay/cinematic ownership is unknown, the runtime predicate remains unproven and Freecam stays unavailable.

These captures do not authorize activation in Replay, split-screen, loading, cinematics, attract mode, pause, teardown or unknown scenes. Those contexts remain fail-closed until the game-state discriminator is established.
