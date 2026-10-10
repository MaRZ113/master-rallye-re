# R-CAM1-A2 camera ownership and mutation boundary

**Status: `READY_FOR_CAMERA_DIAGNOSTIC_VALIDATION`.** The exact-build render order now supports a plausible shared CPU-culling/D3D-view seam, but the renderer still lacks an independently validated active-race gate and a proven immediate pose-restoration boundary. No Freecam camera writes or controls are enabled.

## Target and evidence

The pristine retail executable at `D:\Game\Master Rallye\MRallye.exe` is 3,121,214 bytes and hashes to `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. This is the exact image for the addresses below. The repository copy does not contain the proprietary executable.

Evidence grades:

- **`CONFIRMED_BY_EXE`**: exact-build disassembly or the retained exact-build Ghidra exports under ignored `.analysis/r-cam1-a-queries/`.
- **`CONFIRMED_BY_RUNTIME`**: six R-CAM1-A1 in-game observations reported for this handoff: one frontend Source45 selection and five France1 Source90 selections. The report says the count/index, selected/current pointer match, full guarded CameraFrame, CPU planes and final View were available. Raw JSONL captures are not present in this checkout.
- **`STATIC_INFERENCE`**: expected behavior derived from the confirmed call order, awaiting a targeted capture.

The Ghidra bridge was not exposed as an available session tool. The already-retained Ghidra exports were reused; `0x004F6310` was additionally disassembled read-only from the hash-verified executable with Capstone. No Ghidra project or game image was modified.

## Frame order and candidate seam

| Order | VA / RVA | Evidence |
|---:|---|---|
| Fixed-step update | `0x005AFE30` / `0x001AFE30` calls `0x00522AD0` before `0x00653080(alpha)` | `CONFIRMED_BY_EXE` |
| Camera update | `0x00522AD0` / `0x00122AD0` calls `0x00522600` / `0x00122600`; that routine runs camera producers, rebuilds manager planes through `0x004E3DA0`, then updates camera-related objects | `CONFIRMED_BY_EXE` |
| Render camera selection | `0x00653080` / `0x00253080` assigns viewport, binds the selected manager camera, and calls `0x004F6310` before the owned submit CALL | `CONFIRMED_BY_EXE` |
| Helper formerly uncertain | `0x004F6310` / `0x000F6310` lazily allocates and initializes a global `0x7C`-byte list/manager at `0x006F96FC`. Its decoded paths do not read or write CameraFrame fields. It is not a per-camera pose producer. | `CONFIRMED_BY_EXE` |
| Existing CPU-culling hook | CALL at `0x006532DD` / `0x002532DD`, expected bytes `E8 9E 63 EB FF`, targets `0x00509680` / `0x00109680`. The current `GameFov` callback runs before entity traversal and changes only side planes. | `CONFIRMED_BY_EXE` |
| Entity traversal and draw | `0x00509680` traverses selected-camera entities; model visibility at `0x0054C9D0` calls the sphere test at `0x004F2380` and uses the renderer's current camera. Draws call the final camera builder during traversal. | `CONFIRMED_BY_EXE` |
| Final D3D View | `0x005614A0` / `0x001614A0` interpolates previous pose at CameraFrame `+0x38..+0x74` and current pose at `+0x88..+0xC4`, then normalizes/orthogonalizes the basis and submits VIEW. The gameplay SetTransform return is VA/RVA `0x00561A26` / `0x00161A26`. | `CONFIRMED_BY_EXE` |

The candidate coordinated camera seam is the already-owned `0x006532DD` CALL: a renderer-owned pose would have to be applied before `0x00509680`, used for the CameraFrame-based visibility tests and final View construction, then restored without touching a replacement camera or later stock update. The viewport and current camera are established before the CALL. This is promising ordering, not permission to write pose fields.

The previous R-CAM1-A note marked `0x004F6310`'s role as unresolved. Exact-build disassembly narrows that uncertainty: it is a lazy list-manager initializer, not an observed camera pose update. This new interpretation is recorded here; the earlier note remains unchanged.

## Remaining ownership gate

CameraFrame pointer identity cannot distinguish the frontend from gameplay: the reported A1 observations reused the same address. `manager.count == 1`, index zero, pointer equality and Source90 therefore cannot authorize Freecam.

Existing active-race capture checks provide useful Broker evidence (`Race/Type=2`, one player, no network synchronization, no attract/replay/ghost state, and the selected Quick Race track), but the renderer has no reviewed, side-effect-free way to read and validate those live values. Retail Broker key IDs are sequential interned IDs, not hashes; calling typed getters may grow or reallocate the entry vector. Caching a Broker entry pointer or guessing a key ID would not be safe. No active-race predicate is enabled until its exact-build read path and behavior through loading, frontend, replay/cinematic, teardown and unsupported scenes are demonstrated.

## Restoration boundary

Current `GameFov` snapshots the full CameraFrame but writes only the four side-plane vectors. It guards restoration against intervening camera/plane changes and restores at the existing frame/Present boundary. That policy is acceptable for its narrowly scoped FOV change; it is not evidence that pose fields can remain modified until Present. The renderer must establish whether the complete entity traversal is the end of the pose-write interval and account for the frame scheduler's camera reset after traversal. No temporary pose is written in this phase.

The new `pre_submission_camera` diagnostic stores one read-only CameraFrame snapshot at the existing hook, before the FOV side-plane write, and correlates it with the existing final VIEW observation by device/frame and camera pointer. It does not install another game hook. It is populated only when the existing GameplayFOV hook is active; use the existing FOV option for that diagnostic capture.
