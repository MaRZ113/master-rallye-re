# R-CAM1-A1 camera owner diagnostic validation

**Status: `READY_FOR_CAMERA_DIAGNOSTIC_VALIDATION`.** This short procedure validates the corrected read-only camera-owner probe. It does not test Freecam movement; no Freecam option, hotkey, or camera write exists.

## Candidate and configuration

Use the exact pristine retail executable (SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`) and the newly built Win32 candidate `modernization/renderer/.build-r-cam1-a/Release/d3d8.dll`. Confirm the installed candidate SHA256 against the validation record before launch. Keep the stable Windowed configuration and all other visual settings unchanged. Do not use Experimental Exclusive Fullscreen.

For the three captures, use these existing INI keys:

```ini
[Display]
Mode=1

[Camera]
GameplayFOV=0

[Trace]
Enabled=1
FrameSummaries=1

[PS2FoliagePilot]
Mode=0
Diagnostics=0
```

Press F10 once per screen state and wait for each one-frame capture to complete before moving to the next state.

## Three captures

1. **Frontend vehicle preview.** Open the frontend vehicle preview and capture once. If this screen submits the observed source45 VIEW path, the session event should identify `projection_family="source45"`; otherwise, the matching `frame_summary.camera_probe` must report a bounded skip reason. No frontend camera state may change.
2. **France1 default camera.** Enter a France1 Quick Race, wait for a stable view, and capture once. Expected caller RVA is `0x00161A26`, projection family is source90, and the session JSONL contains one `camera_owner_observation`. Owner mismatch or incomplete reads remain useful diagnostic evidence and must not suppress the payload.
3. **France1 alternate stock camera.** Select another stock camera, wait for the view to settle, and capture once. Expected caller RVA remains `0x00161A26`; the observation must have a new device/frame association and comparable owner/pose fields.

Do not add camera cycling, replay, attract, long driving, FOV changes, or other captures to this corrective check.

## Files and correlation

Retain the unique session JSONL and the three corresponding `frame-...jsonl` files. Label the three captures in a short note with screen state and camera selection. The full `camera_owner_observation` payload is written only to the session JSONL. Each F10 frame file contains its regular transform events and the compact `frame_summary.camera_probe` status. Join records using the session filename as capture identity, then `device` and `frame`; confirm the session header and each frame's `frame_begin` executable/proxy hashes match the tested binaries.

The status reports one of the bounded outcomes, including `no_verified_gameplay_view_site_observed`, `gameplay_view_observed_capture_inactive`, `executable_profile_unsupported`, `projection_state_unavailable`, `projection_ineligible`, `camera_owner_read_incomplete`, `observation_emitted`, `duplicate_observation_suppressed`, `serialization_failure`, or `session_write_failed`. `owner_reads_complete=false` means the partial payload was emitted with the existing per-field read flags; it does not represent a valid Freecam owner.

## Diagnostic decision

The callsite correction is validated when the race captures emit from `0x00161A26`, the source45/source90 family remains visible in JSON, no UI VIEW is admitted, and camera reads remain observational and guarded. A coherent owner still requires human review of the manager/current-camera identity, camera index, viewport, side planes, previous/current poses, and D3D VIEW. This phase does not authorize Freecam movement or change the status from `READY_FOR_CAMERA_DIAGNOSTIC_VALIDATION`.
