# R-CAM1-A3: camera scope and race ownership

**Status: `BLOCKED_ON_POST_TRAVERSAL_RESTORE`. Functional Freecam is not implemented.**

The accepted R-UI1 carousel correction is now automatic in PreserveMargins on
the exact retail profile, in separate commit `7e866d7`. The obsolete public
`CarouselAlignment` setting is ignored. Stock/Centered4x3, row signatures,
sticky anchors and draw-local WORLD restoration retain their previous contracts.
The user's acceptance confirms the tested carousel behavior; it does not validate
any camera mutation.

## Exact target and method

Read-only input: `D:\Game\Master Rallye Pristine\MRallye.exe`, 3,121,214 bytes,
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
ImageBase `0x00400000`. All addresses below belong to this image.

Fresh narrow queries used the installed ghidra-bridge exporter with Ghidra
12.1.4 on D:, Java 25, a read-only pristine project and rolled-back transactions.
Ignored output is under `modernization/renderer/scratch-camera/`. Exact byte and
relative-CALL checks independently reproduce the central findings through
`tools/inspect_camera_scope.py`. No original project, EXE or asset was saved or
modified. Ghidra's inferred function types are not authoritative ABI evidence;
some unanalysed callees produce misleading decompiled stack variables. Instruction
operands and confirmed offsets are the evidence used here.

## Verified traversal ABI

`CONFIRMED_BY_EXE`: scheduler CALL at VA/RVA `0x006532DD` / `0x002532DD`
targets `0x00509680` / `0x00109680`. ECX is the selected-camera entity-list
owner (`list manager +0x20`). Stack arguments are camera index, then first-camera
boolean. The callee loads the index at entry-stack `+4`, and the other argument
at `+8` after accounting for its saved registers. Its loop dispatches entities
through renderer virtual `+0x10`; it skips entity flag bit 2. Both loop and empty
list paths converge on one `RET 8` at `0x005096CE` / `0x001096CE`.

This proves the static thiscall/two-argument cleanup contract. It does not certify
a replacement bridge. Native return EAX/EDX, flags, x87/SSE/MXCSR and stack balance
must still survive a real x86 fixture. No replacement bridge or pose write was
introduced; `GameFov` retains its existing single-owned pre-submit tail-JMP.

## Traversal return is too early for a complete camera scope

`CONFIRMED_BY_EXE`: at `0x006532E2` / `0x002532E2`, immediately after traversal
returns, the scheduler prepares renderer virtual `+0x20` and calls it at
`0x006532E6` / `0x002532E6`. Renderer vtable `0x006922C8` / `0x002922C8`
resolves that slot to `FinalizeCamera_0056E250` / RVA `0x0016E250`.

As already mapped in [renderer reconnaissance](../../../renderer-recon/frame-lifecycle.md),
FinalizeCamera flushes queued geometry, shadows and trails, and conditionally
renders particles. Fresh analysis confirms two concrete late camera dependencies:

| VA / RVA | Late operation | Evidence |
|---|---|---|
| `0x0056E40A` / `0x0016E40A` | Calls camera builder `0x005614A0` with argument 0 | `CONFIRMED_BY_EXE` |
| `0x0056E416` / `0x0016E416` | Calls particle renderer `0x00563CB0` | `CONFIRMED_BY_EXE` |
| `0x00564061..0x0056406B` / `0x00164061..0x0016406B` | Particle renderer follows renderer holder `+0x38`, then selected camera `+4` | `CONFIRMED_BY_EXE` |
| `0x0056410E` / `0x0016410E` | Adds `0x88` to that camera pointer: Current Pose | `CONFIRMED_BY_EXE` |
| `0x00564185..0x0056418A` / `0x00164185..0x0016418A` | Passes Current Pose to billboard builder `0x005641C0` | `CONFIRMED_BY_EXE` |

The final VIEW builder has a conditional cache exit, not an unconditional promise
to retain traversal's VIEW. More decisively, particles read CameraFrame Current
Pose directly, independently of that cache. `STATIC_INFERENCE`: restoring stock
Previous/Current Pose immediately after `0x00509680` would let those late draws
use stock orientation/position while earlier visibility/rendering used Freecam.
Keeping a cached Freecam D3D VIEW would not repair particle pose consistency.

**Exact missing fact:** a single camera mutation scope must restore native state
without depriving FinalizeCamera's late consumers of the same effective pose.
The proposed immediate post-traversal restore does not establish this. Leaving
pose modified until Present or adding a late VIEW-only override would violate the
requested lifetime/coherence contracts.

**Smallest next verification:** audit one scope ending after FinalizeCamera returns
at VA/RVA `0x006532E9` / `0x002532E9`, before scheduler advances to the next camera
or rebinds camera 0 at `0x006532EE` / `0x002532EE`. Prove its exceptional/alternate
returns, remaining EndFrame camera consumers and coordinated restore ownership,
then exercise the actual x86 pre/native/post bridge. This is a candidate boundary,
not permission to keep a temporary pose active until Present.

## Race-state candidates narrowed, not approved

`CONFIRMED_BY_EXE`:

- `Frontend/Running` getter is `0x004ADBD0` / `0x000ADBD0`; setter is
  `0x004ADBA0` / `0x000ADBA0`. Constructor `0x00449100` / `0x00049100`
  initializes false; destructor `0x00449330` / `0x00049330` writes false at
  CALL `0x00449364` / `0x00049364`. False alone is not independent race proof.
- Scene manager global `0x006F9AA0` / `0x002F9AA0`: `+4` receives the requested
  scene ID before loading (`0x005223D0` / `0x001223D0`). `0x00522680` /
  `0x00122680` commits `+4` into `+0` on successful load; its failure branch
  assigns the interned `Default` ID. These are sequential string-pool IDs.
- Scene unload `0x00522480` / `0x00122480` clears cameras/entities and sets
  `+0x0C=3`, but contains no clearing write to committed scene ID `+0`.
  Main update decrements `+0x0C` at `0x005B008E..0x005B00A2` /
  `0x001B008E..0x001B00A2`. Zero is not a validated race-ready flag.
- `gaRaceStarterAI` constructor `0x0048E210` / `0x0008E210` installs vtable
  `0x00690D30` / `0x00290D30`. Its update `0x0048E820` / `0x0008E820`
  increments `+0x0C` and queues actor retirement when it reaches 23 at
  `0x0048E939..0x0048E943` / `0x0008E939..0x0008E943`. It is not a persistent
  active-race identity.
- Race startup creates named actor `RaceLimits`, attaches `gaLimitsAI` at actor
  slot 0 through `0x004F5950`, and initializes it via virtual `+0x14`.
  `gaLimitsAI` constructor `0x004CD870` / `0x000CD870` installs vtable
  `0x0069152C` / `0x0029152C`; initializer `0x004CDF00` / `0x000CDF00`
  owns participant arrays `+0x20/+0x24/+0x30..+0x40` and count `+0x2C`.
  Update is `0x004CD9B0` / `0x000CD9B0`. This is a promising live-owner candidate,
  not an approved offline Quick Race gate.

The missing race fact remains: bounded read-only registration/phase lifetime for
that persistent owner, combined with verified France1/offline/singleplayer and
replay/attract/loading/teardown exclusions. No game Broker getter is called, no
interned ID is guessed, and no pointer or stale scene name authorizes mutation.

## Implementation and runtime boundary

Freecam controls, mouse ownership, temporary pose writes and new configuration
are absent. No first-flight DLL is advertised. FOV, UI, vehicle semantics,
resource lifecycle, foliage probes and display policy remain unchanged by the
camera investigation. Pose fields `+0x38/+0x88`, snap field `+0xC8`, and coherent
CPU plane writes are future scope; their restore policy is not certified here.

The tested baseline DLL is useful for automatic UI closeout. Do not interpret its
successful build or regression tests as functional Freecam validation.
