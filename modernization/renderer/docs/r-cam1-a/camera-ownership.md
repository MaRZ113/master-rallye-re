# R-CAM1-A camera ownership reconnaissance

**Status: `READY_FOR_CAMERA_DIAGNOSTIC_VALIDATION`.** Static analysis identifies the camera data path and the existing CPU-frustum synchronization seam. It does not yet establish a safe runtime discriminator for single-player race gameplay versus every unsupported source-90 consumer, so no Freecam camera writes or input controls are enabled.

## Exact build and evidence

The target was verified as `D:\Game\Master Rallye\MRallye.exe`, 3,121,214 bytes, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. It is PE32/I386, timestamp `0x3C02695D`, ImageBase `0x00400000`, entry VA `0x005C4602` (RVA `0x001C4602`), with `.text` RVA `0x1000` size `0x28D294`, `.rdata` RVA `0x28F000` size `0x1E432`, `.data` RVA `0x2AE000` size `0x5E608`, and `.rsrc` RVA `0x30D000` size `0x3AB8`.

Evidence labels used here:

- **`CONFIRMED_BY_EXE`**: exact-build instruction/decompiler evidence queried from the pristine retail program using Ghidra 12.1.4. The project was opened read-only, no program was saved, and the analysis transaction was rolled back. Query outputs are ignored scratch data under `.analysis/r-cam1-a-queries/`.
- **`CONFIRMED_BY_EXISTING_RESEARCH`**: a finding preserved in the earlier camera/FOV research cited below.
- **`STATIC_INFERENCE`**: a control-flow interpretation supported by the exact executable but not yet checked in a live game session.
- **`HYPOTHESIS`**: a remaining explanation or behavior requiring runtime evidence.

## Camera objects and ownership

**`CONFIRMED_BY_EXE`** — Camera manager global VA `0x006F94DC` / RVA `0x002F94DC` points to a `0x14`-byte manager. `FUN_004E3DD0` (VA `0x004E3DD0` / RVA `0x000E3DD0`) allocates four `0xCC`-byte camera objects and initializes the active count at manager `+0x10`. The four pointer slots occupy offsets `+0x00` through `+0x0C`; active count is a separate field at `+0x10`.

**`CONFIRMED_BY_EXISTING_RESEARCH`** — The renderer current-camera chain is rooted at global VA `0x006F9CF0` / RVA `0x002F9CF0: [global] -> renderer singleton -> +0x38 state/holder -> +0x04 current camera`. The current FOV path compares this pointer against the selected manager camera before changing CPU side planes.

Camera layout, byte offsets from the object base:

| Offset | Meaning | Evidence |
|---|---|---|
| `+0x00` | Authored/source angle | `CONFIRMED_BY_EXE` constructor/builder; see also R-GFX3 camera findings |
| `+0x08..+0x37` | Four CPU side-plane normals | `CONFIRMED_BY_EXE`, `FUN_004F2620` |
| `+0x38..+0x77` | Previous/interpolation pose | `CONFIRMED_BY_EXE`, read by final camera construction |
| `+0x78..+0x87` | Viewport X/Y/width/height | `CONFIRMED_BY_EXE`, assigned by frame scheduler |
| `+0x88..+0xC7` | Current pose: right/up/back basis and world position | `CONFIRMED_BY_EXE` layout; forward is negative back |
| `+0xC8` | Snap/interpolation frame field | `CONFIRMED_BY_EXE` layout |

## Update, visibility, and rendering order

| Order | Function VA / RVA | Finding |
|---:|---|---|
| 1 | `0x005AFE30` / `0x001AFE30` | Main loop performs fixed-step update work including `0x00522AD0`, computes interpolation alpha, then calls frame scheduler `0x00653080(alpha)`. `CONFIRMED_BY_EXE`. |
| 2 | `0x00522AD0` / `0x00122AD0` | Calls `0x00522740`, camera update scheduler `0x00522600`, `0x0054A660`, and `0x005FCD30`. `CONFIRMED_BY_EXE`. |
| 3 | `0x00522600` / `0x00122600` | Runs camera-related producer/update helpers `0x004E6070`, `0x004E5FD0`, `0x004F68F0`, `0x004F65B0`, ensures the camera manager, rebuilds active-camera planes via `0x004E3DA0`, then runs `0x004EE5D0`. Exact per-camera Follow/Fixed pose writer is not isolated from these calls and their indirect dispatch. `CONFIRMED_BY_EXE` for call order; writer identity remains unknown. |
| 4 | `0x004E3DA0` / `0x000E3DA0` -> `0x004F2620` / `0x000F2620` | Rebuilds each active camera's four CPU side planes using the camera source angle, viewport dimensions, and current basis. `CONFIRMED_BY_EXE`. |
| 5 | `0x00653080` / `0x00253080` | Selects the active camera(s), assigns each camera's viewport at `+0x78..+0x84`, binds the selected camera through the renderer interface, calls `0x004F6310`, then calls entity-list traversal `0x00509680(index, index==0)`. The inspected scheduler supports multiple camera slots; a count of one is not proven to mean race gameplay by itself. `CONFIRMED_BY_EXE`. |
| 6 | `0x00509680` / `0x00109680` | Selects manager camera by index and walks that camera's entity list, skipping entities with flag bit `2`; visible entities enter renderer virtual call `+0x10`. `CONFIRMED_BY_EXE`. |
| 7 | `0x0054C9D0` / `0x0014C9D0`, `0x004F2380` / `0x000F2380` | Model-bound traversal calls sphere visibility and then applies forward-distance checks before compiled geometry submission. Camera-relative rejection therefore continues inside traversal after the existing `0x006532DD` hook. `CONFIRMED_BY_EXE` and `CONFIRMED_BY_EXISTING_RESEARCH`. |
| 8 | `0x005614A0` / `0x001614A0` | Builds the final D3D projection and VIEW. VIEW basis/position are interpolated between the previous pose at `+0x38..+0x74` and current pose at `+0x88..+0xC0` with the renderer interpolation factor; the basis is normalized/orthogonalized before submission. It calls transform wrapper `0x0053F9E0` for `D3DTS_PROJECTION` (`3`) and `D3DTS_VIEW` (`2`). `CONFIRMED_BY_EXE`. |

The selected camera object is supplied to renderer state and also resides in the camera manager used by traversal. The existing `GameFov` path verifies that those two pointers agree at its pre-submission hook. This is strong static evidence of a shared owner, but it does not establish that all camera-family and mode transitions use that same stable object. `STATIC_INFERENCE` pending runtime captures.

## Existing synchronization seam and its limits

The existing hook is the relative CALL at VA `0x006532DD` / RVA `0x002532DD`, expected bytes `E8 9E 63 EB FF`, original target VA `0x00509680` / RVA `0x00109680`. The call occurs after viewport assignment and `0x004F6310`, immediately before entity-list traversal. `GameFov` already owns this site and temporarily replaces CPU side planes, restoring them before Present/Reset. This is a proven FOV integration point; it is **not** a proven Freecam write window.

At the site, later model-bound/sphere visibility uses the camera and planes during entity traversal. Earlier camera update and per-camera list preparation have already run, however, and the exact role of `0x004F6310` for every camera family has not been established. The final D3D VIEW is built from both old and current poses. A Freecam therefore needs one coordinated, correctly timed effective pose for CPU culling and final VIEW, plus a safe restore that does not overwrite a newer camera update. A late VIEW-only override is insufficient.

The final transform setter wrapper is called at VA `0x0053FA75` / RVA `0x0013FA75`; the same return site can receive several transform types. At that point source-45 preview, source-90 family, other perspective families, and non-perspective transforms can be separated from the projection matrix, but the source-90 family is not an activity-mode identity.

## Unsupported and unresolved owners

**`CONFIRMED_BY_EXISTING_RESEARCH`** — Source-45 frontend preview is kept separate by the existing projection policy. The five authored camera variants include three Follow and two Fixed cameras, but the exact selector-to-producer mapping is not established for every route.

**`UNKNOWN`** — Whether Replay, Replay Theatre/Attract, cinematics, pause, or split-screen uses the same manager, same current-camera chain, one active camera, source-90 projection, or shared final transform callsite. Prior research explicitly warns that source-90 is shared and does not prove normal race ownership. R-CAM1-A does not expand the feature gate on this evidence.

**`UNKNOWN`** — Exact producer routine(s) writing previous/current pose fields, whether every producer overwrites them each simulation tick, camera object invalidation on scene transition, and whether any pre-traversal activation/LOD decisions use vehicle position rather than camera position.

## Source references

- [R-GFX3 camera findings](../../research/r-gfx3/camera-findings.md)
- [R-GFX4 FOV/culling evidence](../../research/r-gfx4/fov-culling.md)
- [R-GFX4 exact hook map](../../research/r-gfx4/fov-culling-map.json)
- Read-only exact-build decompiler exports: ignored `.analysis/r-cam1-a-queries/`; provenance records the retail SHA and rolled-back transaction.
