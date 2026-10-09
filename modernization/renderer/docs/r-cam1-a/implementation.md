# R-CAM1-A implementation boundary

**Current implementation: read-only camera-owner observation only.** No Freecam mode, hotkey, input capture, camera mutation, game-code hook, or EXE patch is present. The candidate remains `READY_FOR_CAMERA_DIAGNOSTIC_VALIDATION` until runtime observations identify a fail-closed single-player gameplay owner.

## Diagnostic behavior

The D3D8 device wrapper observes a successful `SetTransform(D3DTS_VIEW, ...)` only when all of these hold:

- the caller is the main executable and the return RVA is the verified gameplay VIEW site `0x00161A26` (VA `0x00561A26`);
- the process executable matches the existing exact retail compatibility profile and camera/FOV capability;
- `Trace.Enabled=1` and an existing F10 capture is active;
- requested and effective native projection states are both known and perspective;
- the native `SetTransform` call succeeded;
- no observation for the current device frame has already been emitted.

The gameplay projection return VA/RVA `0x0053FA75` / `0x0013FA75` remains reserved for the existing GameFov projection policy and cannot satisfy the camera VIEW gate. The UI projection and VIEW sites (`0x00161ED3`, `0x00161FDC`) are excluded by the exact callsite gate. The gate is a production helper exercised directly by the native regression tests.

It uses guarded `safe_copy` reads for the camera manager, renderer current-camera chain, selected camera, and pose/frustum fields. It records both the game's requested logical projection (used to classify source45/source90) and the effective native projection from the D3D shadow after forwarding, plus the input VIEW matrix. The full `camera_owner_observation` remains in the uniquely named session JSONL; it records pointer-read validity separately from null pointers and emits non-finite floats as JSON `null`. The same device/frame's compact `frame_summary.camera_probe` status is present in both the session JSONL and matching F10 frame JSONL. Correlate with the session filename, device, frame, and `frame_begin` executable/proxy hashes. Status distinguishes an absent verified site, inactive capture, unsupported profile, missing/ineligible projection, incomplete VIEW or owner reads, emission, duplicate suppression, serialization failure, and session-write failure.

The per-device-frame allowance is checked only after the exact callsite, native HRESULT, trace/capture state, supported build profile, and both perspective matrices are validated. It is claimed only after a guarded copy of the VIEW succeeds. An incomplete owner chain still produces one honest partial observation with read flags; the frame summary marks `owner_reads_complete=false`. A failed serialization or session write consumes the already-bounded attempt and is reported without retrying.

The probe does not write game memory, alter D3D state, install another game hook, consume input, or change current Freecam/FOV policies. Unknown executables and unsupported profiles receive stock forwarding and no game-specific observation.

## Why the first Freecam is not enabled yet

The pre-submission CALL is already owned by `GameFov`; installing an additional hook would conflict with the existing instruction and ownership/lifetime path. The current implementation safely changes only four CPU planes and restores them at existing frame/reset boundaries. Freecam would also need a coherent pose that covers CPU visibility and the final interpolated VIEW. That requires a coordinated extension of this owner, not an independent D3D VIEW setter.

Static analysis shows a promising order: selected-camera viewport is assigned before the pre-submission call, then entity traversal and model-bound visibility run. But camera producers, per-camera list preparation, `0x004F6310`, and final render calls span several owner paths. We have not proven a single transient pose write/restoration window that preserves every intervening engine update. We also cannot safely treat source-90 projection plus one active camera as a gameplay-only gate: replay, attract/cinematic, and split-screen behavior has not been ruled out. These are explicit stop conditions under the R-CAM1-A safety rules.

## Candidate coordinator contract for a later implementation

If runtime evidence establishes the supported context, the next implementation should extend one camera-frame authority that owns the existing FOV side-plane scope and Freecam policy together. It must coordinate:

1. exact-build/callsite and render-thread validation;
2. manager/current-camera identity, count/index, camera allocation generation, and finite `0xCC` camera layout;
3. a single effective pose used by visibility tests and final VIEW, with a documented interpolation treatment;
4. FOV-on and FOV-off behavior, deriving horizontal FOV from the effective viewport and preserving existing camera-family rejection;
5. snapshot/restore that restores only fields still equal to the proxy's own temporary write and never writes to a replaced camera object;
6. deterministic disable/suspend behavior for camera changes, focus loss, Reset, scene transitions, release, and shutdown;
7. input that is focused to the game window and proven not to operate the vehicle; F10 remains reserved.

No control mapping is selected in this diagnostic-only stage. Input/camera-cycle hotkey audit is consequently pending; no WASD, mouse capture, or synthetic key-up behavior is introduced.

## Lifecycle boundaries

| Event | Current diagnostic behavior | Freecam status |
|---|---|---|
| Windowed resize / Borderless resize | Existing renderer Reset and viewport forwarding remain unchanged. | No active state to retain. |
| Alt+Tab / focus loss | Existing renderer focus/display handling remains unchanged. | No mouse capture or camera movement. |
| Pause/unpause | No new pause polling or game-state access. | Unsupported until mode/owner evidence is collected. |
| Camera selector change | Probe reports the next captured owner/matrix; it writes nothing. | No stale camera pointer can be retained. |
| Device Reset/release | Existing FOV scope restores through its current owner; probe status and its once-per-frame claim are cleared at Reset/frame completion. | No new restoration path is needed because no camera data is changed. |
| Frontend/race/replay transition | Observation is only emitted at the exact SetTransform callsite during F10 capture. | No mode is activated or overridden. |

The diagnostic is deliberately a narrow observation, not a partially implemented Freecam. The focused runtime procedure is in [runtime-test-plan.md](runtime-test-plan.md).
