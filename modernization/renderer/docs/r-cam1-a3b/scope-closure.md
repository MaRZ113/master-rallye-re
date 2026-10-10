# R-CAM1-A3b: complete native camera-consumer extent

**Native reader extent established for the reviewed single-camera scheduler path.
Executable mutation remains unapproved; Freecam is not implemented.**

All VAs belong to pristine retail, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
3,121,214 bytes, ImageBase `0x00400000`. RVA = VA minus ImageBase.
The [extended A3 map](../../research/r-cam1-a3/camera-scope-map.json) retains
the original 17 anchors and adds 51. [Instruction excerpts](../../research/r-cam1-a3b/scope-excerpts.json)
and [export digests](../../research/r-cam1-a3/ghidra-evidence.json) preserve the
new call relationships without publishing game binaries or reverse databases.
Ghidra 12.1.4 queries used the installed ghidra-bridge exporter, a read-only
pristine project and rolled-back transactions. Empty xref lists were not used
as evidence of absence. Decompiled calling conventions were not trusted.

## Begin, late readers and three end candidates

`CONFIRMED_BY_EXE`:

| VA / RVA | Operation and ownership |
|---|---|
| `0x006532DD` / `0x002532DD` | Existing GameFov interception before entity traversal `0x00509680`; selected-camera preparation and viewport installation have occurred |
| `0x006532E2` / `0x002532E2` | Traversal returns; **candidate A rejected** because FinalizeCamera follows |
| `0x006532E6` / `0x002532E6` | Renderer virtual `+0x20` → `0x0056E250`, FinalizeCamera |
| `0x0056E40A` / `0x0016E40A` | FinalizeCamera calls camera builder `0x005614A0` |
| `0x0056410E` / `0x0016410E` | Particle renderer uses selected CameraFrame Current Pose `+0x88`; cache retention cannot replace this read |
| `0x006532E9` / `0x002532E9` | Camera index increment/loop; **candidate B rejected** because EndFrame has additional consumers |
| `0x006532EE` / `0x002532EE` | Camera manager reacquired, camera 0 rebound after the per-camera loop |
| `0x006532FD` / `0x002532FD` | Camera 0 viewport `+0x78..+0x87` deliberately written to full-frame bounds |
| `0x00653329` / `0x00253329` | Renderer virtual `+0x18` → EndFrame `0x0056CD80` |
| `0x0056CE38` / `0x0016CE38` | Conditional debug path calls camera builder again |
| `0x0056CE48` / `0x0016CE48` | Selected camera `renderer state +4` passed to debug renderer `0x00589880` |
| `0x00589952` / `0x00189952` | Debug renderer passes that CameraFrame to world debug rendering `0x00589B70`, before switching to 2D projection/identity VIEW |
| `0x0065332C` / `0x0025332C` | EndFrame returns; **candidate C closes this native reader extent** |

EndFrame draws deferred UI at `0x0056CE0A`, conditionally executes the late
builder/debug calls, unbinds textures, calls native EndScene at `0x0056CE60`
and Present through `0x0055B0D0` at `0x0056CE90`. The calls after Present
(`0x0056CE95` / `0x0016CE95`, `0x0056CE9C` / `0x0016CE9C`) obtain/update a
performance timer, followed by FPS accounting and optional logging. The timer
uses QueryPerformanceCounter; these reviewed bodies do not consume CameraFrame.

The disabled-renderer branch at `0x0056CD91` / `0x0016CD91` goes to the
epilogue at `0x0056CF4D`. The normal and short paths terminate with plain RET
at `0x0056CF4A` / `0x0016CF4A` and `0x0056CF54` / `0x0016CF54` respectively.
Both return through the same scheduler end boundary. No native message pump
was found in the reviewed EndFrame path. Driver/overlay reentry during native
Present is an implementation cancellation obligation, not proven absent.

## Scheduler return and immediate caller

After `0x0065332C`, only POP EDI/ESI/EBP/EBX, ADD ESP,`0x50` and RET 4 remain.
The scheduler is called at `0x005B0166` / `0x001B0166` by main loop
`0x005AFE30` / `0x001AFE30`. ECX comes from main-loop object `+0x18`;
one float interpolation argument is pushed at `0x005B0165`.
Return is `0x005B016B` / `0x001B016B`.

`CONFIRMED_BY_EXE`: the continuation increments a local frame counter, optionally
restores thread priority, and loops to exit checks and the message pump at
`0x005AFF5C` / `0x001AFF5C` → `0x0064F1C0`. Fixed-step scene/camera updates
follow that pump. The reviewed continuation contains no additional native
CameraFrame consumer. Thus a post-scheduler callback before `0x005B016B`
also precedes the next independent camera update/message dispatch.

The five-byte relative CALL at `0x005B0166` is a nonoverlapping completion
interception candidate. It avoids patching the three-byte EndFrame virtual CALL
over adjacent POP instructions. It is **not installed or ABI-tested**.
A future wrapper must call the original scheduler exactly once with its original
ECX/float argument and RET-4 contract, preserve its opaque output machine state,
then finish the single camera scope. No return-address substitution is proposed.

## Fields and intervening writers

`CONFIRMED_BY_EXE`: builder `0x005614A0` reads source angle, viewport and both
pose endpoints; it interpolates and orthogonalizes their basis/position into
cached VIEW state. Its `state+8`/argument/global `0x006E9A74` conditional cache
exit is not a universal cache promise. CPU sphere visibility `0x004F2380`
reads Current Pose position/back axis and CPU side planes. Particles read
Current Pose directly. SetCamera `0x0056BAF0` rebinds the selected pointer.

The proposed owned ranges are CPU planes `+0x08..+0x37`, Previous Pose
`+0x38..+0x77`, and Current Pose `+0x88..+0xC7` (176 bytes total).
Source `+0`, flags `+4`, viewport `+0x78..+0x87`, and snap `+0xC8` are excluded.
No reviewed traversal/finalization body was found writing those owned pose/plane
ranges; this is a bounded static audit, not a guarded write/readback test.

Viewport writes at `0x006532A4..0x006532C2` and
`0x006532FD..0x00653309` must survive restoration. A whole-`0xCC` restore is
rejected. Native camera producer `0x004F2620`, outside the render scope, copies
Current → Previous when byte `+4` is set (`0x004F2A0B`) or snap count is nonzero
(`0x004F2A1F`), then clears the flag/decrements snap. Both temporary endpoints
can be owned without freezing this native history, subject to implementation tests.

## Earlier camera dependencies and limits of closure

Actor update `0x004F61A0` calls per-camera sort `0x005097F0` at `0x004F62CE`,
before the final camera update and render scope. Incremental sorter `0x00509970`
and comparator `0x00509F80` read Current Pose position to order entity lists.
The reviewed operations are ordering, not frustum rejection; they do not prove
missing geometry. Another pre-render function, `0x004F65B0`, caches camera
positions. Its downstream purpose remains `UNKNOWN`; it is not classified as LOD.
Independent-camera ordering/cache behavior still needs implementation/runtime validation.

Candidate C establishes the **end** of the reviewed native consumption, not a
permission to mutate. The supported path must validate exactly one camera,
correct thread/device and a live race epoch. Existing Present/Reset
`GameFov.finish_frame` must be coordinated so it cannot restore effective planes
before late readers finish. Atomic hook rollback, x86 output-state preservation,
owner-change/Reset cancellation and guarded field restoration remain unimplemented.
The outstanding admission blocker is recorded in [race ownership](race-ownership.md).
