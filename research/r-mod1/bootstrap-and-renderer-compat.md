# Bootstrap decision and renderer compatibility

## Decision

Use the external suspended-process launcher as the only supported activation
path for the first test candidate. Keep a drop-in x86 `dinput8.dll` proxy as an
optional later adapter, **unsupported until it passes actual Windows runtime
tests**. Neither adapter has been implemented in this phase; the shared core is
portable C++ in `src/native/rmod1/core.hpp`.

The launcher is the better-supported choice because it can verify the exact
file, create the original process suspended, validate the entire patch bundle,
write and read back every operation before resuming the main thread, and
terminate the still-suspended child on any failure. Its general pattern matches
the proven J.1 safety ordering. J.1 source is not imported from or linked to the
Vehicle SDK worktree.

## Retail build gate

Only this on-disk image is in scope:

- filename: `MRallye.exe`
- SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
- file size: `3,121,214`
- PE machine: I386 / PE32 (`0x014C`)
- image base in the audited headers: `0x00400000`
- entry point RVA: `0x001C4602`

The adapter must also prove the mapped main module path and architecture
correspond to the verified disk file. Operation addresses are resolved as
`actual_module_base + RVA`; fixed preferred VAs are not trusted without a live
mapping check. The original executable is never written. Unknown hashes, a
wrong size/architecture, unreadable target bytes or any preimage mismatch abort
before the process is resumed.

## Suspended launcher sequence

1. Parse config and verify the exact retail file and PE32 identity.
2. Resolve the requested Quick Race feature plan and validate runtime
   capabilities/course limits.
3. Validate every patch owner, RVA, byte count, dependency, allocation and
   overlap. Open the original path read-only.
4. Create the exact original image with `CREATE_SUSPENDED`; verify the child
   image path, main-module mapping and architecture.
5. Allocate all required remote regions RW (never RWX), verify every original
   instruction/preimage and all branch reachability/fixups, then populate code
   and data. Finalize code pages RX and data pages with least privilege.
6. Read back the entire plan. If any step fails, terminate the suspended child
   and release allocations; never resume a partial installation.
7. Resume only after all operations and read-backs succeed. On game exit, close
   launcher handles. No hot-unload is attempted; the process teardown removes
   all in-memory changes.

Process-image equality needs a real PE-aware verifier: compare module identity
and executable section bytes with relocation/IAT handling, not a blind whole
mapped-image hash. That verifier and the Win32 launcher are not implemented.

## `dinput8.dll` feasibility and block

Exact retail import evidence shows a static `DINPUT8.dll` import of
`DirectInput8Create` at IAT VA `0x0068F020` / RVA `0x0028F020`. The retail
initialization owner is identified as `FUN_00570E00` (DirectInput creation and
device setup), called within application-manager startup `FUN_005AFB20`.
Static PE evidence confirms this import exists; it does not prove that an
export-triggered installer runs before every affected constructor.

The local 32-bit system `dinput8.dll` export audit lists six exports, ordinal 1
through 6: `DirectInput8Create`, `DllCanUnloadNow`, `DllGetClassObject`,
`DllRegisterServer`, `DllUnregisterServer`, and `GetdfDIJoystick`. A proxy must
forward all six required name/ordinal entry points using the absolute 32-bit
system DLL path, preserving the stdcall ABI. The stock game itself imports only
`DirectInput8Create`. This list must be re-audited on each supported OS/runtime;
it is not a promise that unrelated overlays use no additional exports.

`DllMain` may only capture its instance and disable unnecessary thread
notifications. It must not read config, hash executables, load another DLL,
create UI, or install hooks under loader lock. A worker created from DllMain
cannot be assumed to beat the game entry thread. Synchronously initializing
inside `DirectInput8Create` would run outside loader lock, but current static
evidence does not prove that all participant/race constructors are still ahead
of that call. Until startup order is proven and actual Windows runtime tests
pass, the proxy is **NOT IMPLEMENTED / NOT SUPPORTED**.

## Renderer requirements

The graphical proxy is a different filename (`d3d8.dll`) from the optional
bootstrap (`dinput8.dll`). The retail import descriptors list `d3d8.dll` before
`DINPUT8.dll`; this is static load-order context, not proof of actual runtime
module initialization order. R-MOD must never replace, overwrite, require or
modify the graphical `d3d8.dll`. The external launcher is independent of DLL
search order; when paired with a graphical proxy it launches the same game
directory and verifies the proxy files remain byte-identical.

The existing renderer research documents static D3D8 forwarding feasibility,
but no R-MOD renderer coexistence runtime result is established. Required human
matrix for the release candidate:

| Configuration | Required proof | Current status |
|---|---|---|
| pristine retail, no mod | vanilla startup, frontend, race, shutdown | R-MOD baseline not freshly tested |
| graphical `d3d8.dll` proxy only | existing graphics behavior and clean shutdown | STATIC feasibility only; runtime pending |
| Randomizer launcher only | INI modes/count guards, frontend, race, results, shutdown | launcher/candidate not built |
| graphical proxy + Randomizer launcher | combined rendering, input/AI/race, results and shutdown | not tested |

The four-way matrix is mandatory before renderer-compatible release
qualification. A fifth later test is required before advertising the `dinput8`
proxy: vanilla, graphical proxy only, DInput proxy only and both proxies,
including input forwarding, module load paths, early initialization and clean
shutdown. No such pass is claimed here.

## Compatibility and conflicts

Conflicts fail closed on any overlapping byte owner, foreign preimage, unknown
loaded proxy identity or unsupported graphics wrapper. The Randomizer never
chains or replaces `d3d8.dll`; it does not install Vehicle SDK components. The
launcher path and INI can be removed between launches; no original game file is
owned or changed.
