# R-GFX4-3: projection and CPU side-plane synchronization

**READY_FOR_HUMAN_RUNTIME.** The widened-edge X-Trail wheel omission is a **STRONG_HYPOTHESIS** attributable to the independently confirmed projection/culling mismatch. The candidate removes that angular mismatch at the shared submission boundary. The specific visual artifact is not called repaired in runtime until the human edge retest passes. R-GFX3 remains administratively CLOSED; its original D3D-only FOV implementation and runtime acceptance are retained as historical evidence.

All addresses below are pristine-retail VA / RVA (ImageBase0x00400000), SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Corpus and current `D:/Game/Master Rallye Pristine/MRallye.exe` both rehashed to this identity in this continuation. Latest Ghidra found on D: is12.1.4. Queries used the installed ghidra-bridge exporter, a read-only pristine project/program and always rolled back temporary transactions. The first configured project exposed no program, so queries used the existing pristine audit project instead. No project/database was saved. [Byte and assembly-digest map](fov-culling-map.json) is reproducible with renderer-local `tools/inspect_fov_culling.py`; raw exports are ignored.

| Owner/site | VA / RVA | Confirmed role |
|---|---|---|
| Camera constructor | 0x004F21B0 /0x000F21B0 | 0xCC-byte object, default source45, old/new pose, rectangle |
| Camera manager update | 0x004E3DA0 /0x000E3DA0 | Loops active camera pointers and calls plane builder at004E3DB2 |
| Camera update scheduler | 0x00522600 /0x00122600 | Updates camera producers then manager/frustum |
| Source-angle helper | 0x004F2350 /0x000F2350 | source if W<=H, otherwise source*H/W |
| Stock side-plane builder | 0x004F2620 /0x000F2620 | Four outward normals atcamera+08,+14,+20,+2C; uses source and dimensions, then transforms by current camera pose |
| Axis-angle / vector math | 0x00431FB0 /0x00031FB0; 0x004C4E90 /0x000C4E90 | Quaternion sin/cos half-angle, row-vector transform |
| Sphere visibility | 0x004F2380 /0x000F2380 | Radius<=0 rejection, optional distance and behind-camera rejection, four normal·delta<radius tests |
| Shared model bound traversal | 0x0054C9D0 /0x0014C9D0 | Calls sphere test at0054CA9B, then forward-distance scalar, then compiled draw virtual+30 |
| Entity submission | 0x0056BBC0 /0x0016BBC0 | Interpolated instance transform, model bound hierarchy and queue submission |
| Camera entity-list traversal | 0x00509680 /0x00109680 | Selects manager camera; submits each entity except flagbit2 |
| Per-camera list maintenance | 0x00509810 /0x00109810; 0x00509970 /0x00109970 | Sorts/relinks lists by category and camera-position distance; the inspected paths do not discard by FOV |
| Frame scheduler | 0x00653080 /0x00253080 | Assigns actual client camera rectangle before the submission CALL |
| Final D3D camera | 0x005614A0 /0x001614A0 | Source-angle call00561537, perspective construction, interpolated VIEW |

Camera source degrees live at+00; viewport X/Y/W/H at+78/+7C/+80/+84. Current right/up/back basis starts+88/+98/+A8 and position+ B8/+BC/+C0. The game's forward direction is negative back-basis. Old interpolation pose is+38..+74. Camera-manager pointer is VA006F94DC /RVA002F94DC, with camera pointers at+4*index and active count+10. Renderer singleton VA006F9CF0 /RVA002F9CF0 → holder+38 → camera+4 supplies the current camera for both hierarchy and final D3D work.

Near0.2 and far twice the ViewDist300/400/500 scalar (or100000 branch) come from renderer parameters, not these side planes. Sphere visibility additionally uses distance/behind-camera tests, and hierarchy imposes its caller distance scalar. Those limits, positions, basis, old/new interpolation, flags, near/far and FOV source degrees remain stock.

## Recovered angular mismatch and solution choice

**CONFIRMED_BY_EXE:** the CPU builder takes source/2, linearly scales the smaller viewport axis, then uses x87 FSIN/FCOS/quaternion rotation. Constants are0.5 at0068F958, degrees-to-radians at00690F54, and signed half-degree factors around006917CC..D4. No source-angle clamp is present in the inspected builder. CPU landscape HFOV is source; VFOV is source*H/W. D3D perspective HFOV is instead `2*atan(tan(VFOV/2)*W/H)`.

| Viewport / target | Stock VFOV | Linear source if changed | Actual target HFOV |
|---|---:|---:|---:|
|640x480, VFOV80|67.5|106.666667|96.418343|
|1920x1027, VFOV80|48.140625|149.561831|114.967910|
|1920x1027, VFOV110|48.140625|205.647517 (invalid for outward convex sides)|138.934321|

A single shared source value cannot reproduce both exact perspective angles at nonsquare aspect; sufficiently wide accepted configurations also exceed180 degrees under the linear conversion. Hooking the builder's separate half-angle inputs is possible, but it runs during camera update, before the frame scheduler installs current viewport dimensions; resizing would require another synchronization boundary. The selected narrow seam is **one pre-submission CALL after viewport assignment**, constructing the four side normals from the effective modern VFOV/HFOV and the proven stock basis. No large radius, global visibility bypass, wheel exception or extra draw submission is used.

With vertical half-angle v and horizontal half-angle h, local outward normals are `(0,±cos(v),sin(v))` and `(±cos(h),0,sin(h))`; transform them by current right/up/back basis. This reproduces the recovered sign/order convention while supplying perspective-consistent angles. Normals remain finite/unit for a rigid basis. source90 and all other camera fields stay unchanged, so logical projection, getter virtualization and the temporal source90 classifier need no compensating changes or double override. The stock distinction between current CPU pose and interpolated final VIEW remains; this is an angular correction, not a camera-interpolation rewrite.

## Exact hook and fail-closed behavior

Hook CALL VA`0x006532DD` /RVA`0x002532DD`, expected bytes **`E8 9E 63 EB FF`**, original target VA`0x00509680` /RVA`0x00109680`, return VA`0x006532E2` /RVA`0x002532E2`. Also verify the17-byte context atVA006532D1: `8B 40 20 3B FB 0F 94 C1 51 57 8B C8 E8 9E 63 EB FF`. It proves scene-list lookup, camera arguments and CALL after rectangle writes/viewport application.

Installation occurs from the successful device-wrapper constructor, before CreateDevice returns to the render loop, only for exact file SHA, valid enabled GameplayFOV, base00400000, SSE2 and matching live bytes. Only this relative CALL is replaced; no instruction relocation/trampoline decoder is needed. The bridge preserves GPRs, original ECX/arguments/return PC, EFLAGS and x87/SSE via aligned FXSAVE/FXRSTOR; it initializes a private helper FP environment and tail-jumps to the unchanged original submitter. A module pin keeps the stock-forwarding stub valid even if teardown cannot remove the CALL. This implementation does not hot-toggle config or suspend threads.

The runtime path accepts only active count1, index0, matching manager/current-renderer camera, finite source90±0.01°, valid dimensions and a finite rigid affine basis. It does not add replay, cinematic or split-screen camera families. Source45 preview and ortho remain stock. Mode-specific equivalence beyond the existing source90 scheduler family is unproven and requires a separate study; this candidate is not a replay support claim.

Only camera+08..+37 (48 bytes) changes during submission. The original48 bytes are saved and restored before native Present, before Reset, when disabling and at device release. An intervening engine plane rebuild is preserved; stale pose/dimension proof is rejected. Final D3D FOV override requires this same camera, unchanged basis/dimensions/source and exact effective plane bytes plus matching original perspective aspect. Failed/missing hook or proof means **Stock projection**, with no D3D-only experimental widening fallback. Unknown builds install no hook and keep generic forwarding/trace only. Native projection rejection disables FOV and restores planes; an already submitted failed-native frame can still differ visually and is a human FAIL, not a promised visual rollback.

Memory protection, write verification, instruction-cache flush and restoration are checked. Failed patch operations attempt rollback. Teardown restores only our expected replacement; it never overwrites a foreign hook. Unexpected thread/device scheduling disables semantic FOV; multiple devices are rejected for the session. All writes are in process memory. EXE on disk and assets are untouched.

`frame_summary.fov_culling` exposes installed/synchronized/restored, width/height, source/VFOV/HFOV, synchronized frame count, failures and reason. F10 projection overrides add `culling_synchronized`. No continuous per-object culling log or GPU getter was added.

## Body/wheels and evidence limits

**CONFIRMED_BY_EXE + EXISTING_RESEARCH:** BuildVehicleEntities004B6A00 binds `/car` at004B7027 and creates/binds four separate wheel entities at004B71E1. Each has its own model/transform packet and follows common entity submission → model bounds → camera sphere test. Different centres/radii can therefore reject one wheel while a chassis remains submitted. This supports the X-Trail symptom without establishing its exact missing-wheel cause from a screenshot description alone. There is no wheel-specific workaround.

**CONFIRMED_BY_SYNTHETIC_TEST:** plane/projection agreement at640x480 and1920x1027, portrait handling, bounds just inside/outside each side,110° wide safety without a205° source, preview/invalid/changed-camera rejection, five generic orientations plus lookback, exact frame restoration, failed patch install/remove rollback and x86 CALL ABI/FP preservation. Five game presets were not executed by these synthetic orientations. Human B/C/D must validate real camera producers, edge geometry and Reset before reflection E.
