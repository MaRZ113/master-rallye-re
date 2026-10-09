# J.1 external runtime deployment

## Current result

**R5V-J.1 is CLOSED / CONFIRMED_BY_RUNTIME.** Its Windows x64 launcher starts
the original `MRallye.exe` suspended, validates the mapped image and all
native-operation preimages before writing, installs the complete operation set
before resuming the primary thread, and terminates the child if installation
is incomplete. The original EXE remains byte-unchanged on disk. Human runtime
evidence in the 2026-10-09 Observatory archive confirms the exact pristine
retail identity and the approved in-memory hardened Dump walker while the
same runtime integration materializes Mercedes ID26 and R5VQualifier ID27.
That archive is independently indexed and sidecar-verified in `j2/`.

The current J.2 status is **PARTIAL_RUNTIME_CONFIRMED**. One verified
two-addon runtime bundle and both addon identities are exercised, but
SplitScreen, post-race Vehicle Select re-entry, Cup next-stage reuse, and
Master Rallye fresh-process resume remain human gates. See the J.2 handoff.

J.0 remains an offline semantic planner and continues to report
`runtime_installable: false`. J.1 uses a distinct runtime bundle and native
launcher build; it does not reinterpret the J.0 plan as an installable mod.

## Exact build and native operations

Supported source image:

* SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
* Size: 3,121,214 bytes.
* PE: I386 / PE32, preferred image base `0x00400000`, relocations stripped.
* The launcher is x64 so it can query the WOW64 PEB32 and process memory.

The supported fixed base is checked in the mapped process before any RVA is
used. The process image path is compared by Windows file identity with the
read-only pinned retail handle. The launcher also compares mapped headers and
a mapped `.text` sample with the exact source file.

`tools/addon_runtime.py` composes the retail-to-reference operation set from
the audited H.2 retail patcher and I.1 incremental patcher. It checks each
layer's original bytes and proves each layer's operations reproduce its
audited output before deriving the retail-relative delta. The generated RVP1
table contains 246 records: 244 byte-changing memory ranges, one no-op `.rdata`
write canary, and one PE-header-only `.text` `VirtualSize` record. The
header-only record participates in reconstruction and provenance checks but
is deliberately not written to an already-mapped process. The canary writes
the exact same four bytes (`File`) at RVA `0x2AC7AE`, verifies them, and
restores protection; it has no semantic image effect.

For each memory range, the launcher checks file offset to section/RVA mapping,
non-overlap, exact retail preimage, target `MEM_IMAGE` ownership, committed
page, expected executable/data protection class, exact mapped preimage, and
the expected process base. It verifies all ranges before changing protections
or writing. It prepares protections for every range before the first write,
writes while the primary thread is suspended, reads back every replacement,
flushes instruction cache, and restores page protection. A write/readback or
restoration failure terminates the child without resuming it; the design does
not claim that in-memory rollback is safe.

The reported reference-image SHA is the hash of deterministic source-file
reconstruction, including the file-only PE-header operation. It is not a hash
of the full mapped process address space.

## Resource and frontend staging

The external bundle contains the verified 243-file I.1 resource inventory,
including the separately named Mercedes and R5VQualifier model families, DXT
dependencies, DataGame family definitions, the effective VehicleSelect XML,
and the qualified Data.sma copy. The retail installation's EXE and Data.sma
are read-only inputs and are not copied over or modified. The generated bundle
does not contain a replacement EXE. The effective VehicleSelect scene is
staged from the verified I.1 package at
`resource-root/DataScene/FrontendScreens/VehicleSelect.xml`; J.1 does not
substitute the J.0 semantic plan for native XML.

For `--integrated`, the launcher sets the child process current directory to
the external `resource-root` and leaves the executable path in the original
retail location. Existing I.1 runtime evidence had the EXE and resources
co-located, so it does not prove that this separated CWD arrangement is
honored for every resource path. The Observatory `Resource Root` field and
successful Mercedes materialization are mandatory human checks. No resource
lookup hook is assumed.

The I.1 source package now has two unlisted, game-generated
`DataGame/PlayerState.xml` files. J.1 never copies them into the resource root.
Runtime-created `PlayerState.xml`, `PlayerState.xml#`, and `options.xml#` are
treated as profile state, not resources, and are preserved in the external
test root. Other extra files, missing resources, links, hash changes, or
inventory changes fail verification.

## Launch, conflicts, and removal

The launcher is a standalone command-line program. It is not installed as a
proxy DLL, adds no DLL beside the retail EXE, and does not alter DLL search
order. Integrated launch checks for common adjacent D3D/input/sound proxy DLL
names; any such local wrapper currently causes a fail-closed refusal because
coexistence is not qualified. This scan is intentionally conservative and is
not a complete module-conflict detector.

Normal startup bypasses the launcher. Remove J.1 between runs by disabling or
deleting the generated launcher and external bundle under ignored
`.research-output/vehicles/sdk/j1/`; no hot-unload operation exists. The
original executable is opened read-only with write/delete sharing denied,
hashed before startup, and hashed again after the game exits. The launcher
does not mutate or replace the original retail path.

## Runtime evidence boundary

The human J.1 runtime closeout supersedes the original static-only statements
in `j1-runtime-validation.md`; that file preserves the evidence status at the
time it was written. J.2 ingested 11 JSON/raw pairs from one PID. Every raw
sidecar SHA256 and length matches its JSON metadata. The records show a retail
EXE on disk, a verified live hardened walker with both approved trampolines,
and live ID26/ID27 identities in Quick Race plus ID27 in an initial Rallye
Cup stage and Results. The capture set does not prove SplitScreen, next-stage
Cup persistence, fresh-process Master Rallye persistence, or post-race menu
re-entry. See [J.2 runtime evidence](j2/runtime-evidence.md) and the
[remaining gates](remaining-gates.md).
