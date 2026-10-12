# R-CAM1-A3i implementation

## Scope and admission

Camera bookmarks are available only when the existing Freecam is configured on the exact retail profile, the controller is active, the game window is focused, and the current `live_race_certificate` is valid. That certificate currently means the supported offline `RaceTest/France1` context. The three actions are observed in the existing `FlightWindowInput::sample` path; the original WndProc still receives every message, and no global hook, keyboard consumption, new native patch, CameraFrame owner, or vehicle write was added.

`J` saves, `K` loads, and `L` cycles slots 1 → 2 → 3. Bindings and the default slot are configurable. They are edge-triggered from the existing key-level sample, checked against the Freecam, F10, movement, speed, FOV, roll, and Clean View bindings, and do not alter the native game input stream. The suggested letter bindings should still be checked by the operator during the short in-game pass; if a native command also uses one, rebind it in the INI.

## Controller state

`FlightController::capture_bookmark` and `restore_bookmark` own the state transfer. A bookmark stores the visible 4×4 camera pose separately from the pre-manual-roll orientation, plus horizon heading/progress, manual roll, effective vertical FOV, and the horizon/FOV policy flags. Capture deliberately settles unfinished roll, FOV and initial horizon transitions to their currently visible values; a saved viewpoint does not resume an obsolete tween after loading. The captured horizon is held stable until the operator next changes camera yaw/pitch, after which the existing AutoLevelHorizon behavior resumes. Restore validates both rigid right-handed bases, their shared world translation, the manual-roll relationship between them, finite values and configured roll bounds before changing any controller field.

On success, restore keeps the current movement-speed setting, clears velocity and pending wheel delta, resets the QPC baseline and mouse recenter baseline, and suppresses one subsequent input sample. The loaded pose is installed after the current controller update but before `FrustumFrame::begin`, so the first rendered image uses the saved visible pose and the existing CPU culling/view synchronization. A rejected/empty load does not alter controller pose. If the destination disables Cinematic FOV or Manual Roll required by the saved state, the load fails closed instead of snapping on the next controller update.

Bookmarks do not change native `CameraFrame` ownership. The only camera write remains the already-reviewed `FrustumFrame` scope; no scheduler ABI, 176-byte scope, final VIEW owner, Clean View policy, speed, race certificate, vehicle state, or physics behavior changed.

## Persistence

The per-user path is `%LOCALAPPDATA%\Master Rallye\MRRRenderer\camera-bookmarks.json`. The UTF-8 JSON schema is bounded to 16 KiB and schema version 1. Its root contains the fixed format tag, pristine retail EXE SHA-256 (`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`), logical course ID (`RaceTest/France1`), and exactly three slots. Each occupied slot contains its 1-based slot, printable label, UTC timestamp, visible pose, base orientation, horizon state, manual-roll state, FOV state, and policy flags.

No process ID, native pointer, camera address, owner lifetime, scheduler generation, device handle, or raw CameraFrame is serialized. Float output uses round-trippable precision and the classic numeric locale. Parsing rejects duplicate/unknown/missing fields, non-finite numbers, invalid transforms, extra slots, unsupported schema/build/course, and oversized files. A missing file means three empty slots. Invalid or mismatched files are preserved and cannot be overwritten by Save.

Each save merges one slot with the latest validated file, writes a unique temporary file beside the destination, flushes it, then uses `MoveFileExW` with replace/write-through flags. A write/replace failure leaves the prior file in place. The slots survive race restart and process restart; each use still requires a fresh live France1 certificate. UI selection/current slot is session-local and starts at the configured default.

## Diagnostics

Each bookmark key edge emits one bounded `camera_bookmark_event` with event category, action, slot, course identity (when certified), certificate reason and result reason. The F10 `free_camera` snapshot includes current slot, occupied slots, course identity, storage status, last action/result, bounded action/save/load/reject counters, and the last successful camera world position, both bases, manual roll, and FOV. Persistent JSON contains none of the runtime identity fields.
