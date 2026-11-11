# Bootstrap decision and renderer compatibility

## Decision for the first integrated candidate

The supported test mechanism is an external x64 suspended-process launcher
plus one x86 runtime-core DLL. The launcher verifies the exact retail image,
creates that original image suspended, verifies the mapped image, validates
all operation preimages and allocation ranges, installs the generated plan,
and resumes only after complete read-back. Any pre-resume failure terminates
the child. The package never contains or writes a replacement game EXE.

This is a statically verified candidate, not a Windows game-runtime pass. It
uses an audited pristine-derived operation template and fixed remote code/data
addresses. It refuses to relocate those addresses if either region is not
free. The OEP stub calls the imported `LoadLibraryA("kernel32.dll")`, resolves
`LoadLibraryW` through the already-resolved `GetProcAddress` IAT, loads the
adjacent runtime-core DLL by absolute UTF-16 path, resolves its fixed C ABI,
configures it, and replays the exact five displaced retail entry bytes.
`DllMain` performs no setup under loader lock. This ordering is statically
derived from the PE loader contract and audited imports; actual process startup
is still a human gate.

R-MOD2 BOOT-A now builds an x86 `dinput8.dll` forwarding-only test artifact.
It checks all six host `dinput8.dll` names and ordinals and compares forwarded
DirectInput results with the system DLL. It installs no gameplay patches and
has not yet passed a human game-start/input test. See
[`rmod2-boot-a.md`](rmod2-boot-a.md). The planned R-MOD integration trigger is
immediately before the first forwarded `DirectInput8Create`; exact Ghidra
startup flow places that call during initialization before the frontend loop,
but actual runtime timing and the complete DLL-plus-renderer matrix remain
unverified. No work is performed under loader lock.

## Exact executable gate

Only this on-disk image is accepted:

- `MRallye.exe`
- SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
- size `3,121,214`
- I386 / PE32, image base `0x00400000`, image size `0x00311000`
- entry point RVA `0x001C4602`

The launcher also checks the suspended child's normalized full image path,
x86 architecture, main-module base/size/header and executable section bytes.
The audited image has relocations stripped and is loaded at its fixed preferred
base. Patch targets are resolved from the verified actual module base plus
RVA. Unknown hashes, other sizes, wrong architecture, unexpected mappings,
unreadable pages, foreign preimages, overlaps and unavailable fixed remote
regions fail closed.

## Renderer compatibility

The launcher leaves the existing graphical `d3d8.dll` and its configuration
untouched, and sets the original game directory as the child's working
directory so the same renderer search path is used. That demonstrates
non-interference by implementation; it does not demonstrate runtime
compatibility. The graphical proxy may still conflict with process startup,
input or the patched in-memory hooks.

| Configuration | Current evidence | Release qualification |
|---|---|---|
| pristine retail, no mod | exact disk image statically verified; fresh human control pending | human startup, frontend, race and shutdown |
| graphical `d3d8.dll` proxy only | launcher does not own or replace it | human baseline with exact proxy hash |
| BOOT-A `dinput8.dll` only | HUMAN BOOT-A PASS; game launches and input/controls work | basic startup/input/renderer pass, broader shutdown/relaunch check |
| graphical proxy + BOOT-A `dinput8.dll` | HUMAN BOOT-A PASS; both proxies load simultaneously, graphics/input/controls work | BOOT-B activation-specific regression still required |
| BOOT-B `dinput8.dll` + F3 runtime | first human launch failed closed at overly broad mapped `.text` comparison; corrected virtual-extent candidate is ready | T1 Quick Race, live policy reload, race/Results/shutdown |
| graphical proxy + BOOT-B | renderer untouched by source; initial BOOT-B failure did not identify whether renderer was relevant | repeat corrected test with the existing renderer in a separate disposable copy |
| launcher + Randomizer, no graphical proxy | prior candidate built and self-verifier passes | human frontend/race/Results/shutdown |
| graphical proxy + launcher | no composed runtime evidence | human compatibility pass |

The launcher is suitable for a bounded test of these configurations, but the
release is not renderer-qualified until the full matrix passes. No `d3d8.dll`
is included, replaced, patched or required by the candidate. No Vehicle SDK
component, addon manifest or addon resource is loaded.

## Removal and conflicts

The mod is external to the retail installation. Disable it by launching the
game EXE directly; remove the launcher/runtime/config package to uninstall.
All in-memory changes disappear when the process exits. The launcher does not
attempt hot-unload. It rejects any non-stock target bytes at a planned patch
site, which is the conflict gate for another mod owning those locations.
Unknown renderer proxy identities have not been validated and must remain a
human-test boundary; the launcher never chains, renames or replaces them.
