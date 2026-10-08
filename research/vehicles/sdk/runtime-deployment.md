# J.1 external runtime deployment

## Current result

J.1 has a statically verified Windows x64 launcher candidate for the exact
32-bit retail image. It starts the original `MRallye.exe` suspended, checks
the mapped image and base, validates every native-operation preimage before
the first write, installs the full operation set before the primary thread is
resumed, and terminates the suspended child if installation is incomplete.
The launcher never writes a replacement executable. No game process was
launched by this build, so bootstrap, the no-op canary, resource lookup, and
addon behavior remain **READY FOR HUMAN RUNTIME**, not runtime-confirmed.

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

## Runtime levels and remaining gates

* **Static plan:** H.2/I.1 source layers and all RVP1 bytes reproduce the
  pinned reference image; exact resource inventory verified.
* **Native build:** MSVC x64 launcher builds and `--verify` validates all
  246 operations plus all 243 staged resources.
* **Bootstrap:** not human-confirmed.
* **No-op process-memory canary:** implemented but not human-confirmed; it
  exercises suspended-process targeting and temporary page protection with
  identical bytes.
* **Resource-root lookup:** unresolved until the integrated human run reports
  the Broker root and successfully materializes an addon.
* **Original-EXE unchanged after runtime:** not yet runtime-confirmed; no game
  startup has been performed by this task.
* **Addon runtime:** not tested.

See [loader decision](loader-decision.md), [J.1 validation](j1-runtime-validation.md),
and [human handoff](j1-runtime-handoff.md).
