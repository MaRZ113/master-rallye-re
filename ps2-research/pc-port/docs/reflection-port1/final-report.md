# PS2-REFLECTION-PORT1

| Item | Result |
|---|---|
| Repository / branch | master-rallye-re-general / master |
| Starting / ending HEAD | 3f837f4ddcb27ee1034a4b0753634c92009360ec; unchanged |
| Preflight | Earlier pc-port and revalidation1 changes preserved; frozen renderer clean |
| Frozen renderer tree | 7f9f5a7d9464b7b86ff09a9bf6c34b7ce341682d |
| Target | Tata/car.dx compiled record 19; bonnet paint; 55 source triangles |
| PS2 counterpart | TATA/CAR.PSM root.3; node 170755; $shader(carshiny), mode 3 |
| Source correspondence | 55/55 PC faces match 55/57 PS2 faces at 0.001 model-local units |
| Reflection source | Original ENVSOURCE64X64 RGB, multiplied by 80/128 |
| Full PS2 target | Mixed static + framebuffer source; framebuffer 48/128 term deferred |
| Native coordinate generation | Original PC camera-space normals and native texture matrix retained |
| Temporary changes | Stage 1 texture and COLOROP=ADD; one original indexed draw |
| Stock defaults | FoliageMode=0, PixelProbe=0, ReflectionMode=0 |
| Baseline CTest | 24/24 PASS |
| PS2-enabled CTest | 26/26 PASS |
| Focused Python | 25/25 PASS |
| Exports / generator / compileall | PASS for both proxy exports and generator contracts; compileall PASS |
| Enabled Reset integration | PASS using verified local GXI; original asset excluded from handoff |
| Original sources / renderer / Course SDK | Unchanged |
| Live reflection admission / appearance | NOT_PERFORMED; user A/B pending |
| Foliage PILOT1.4 | Preserved; pixel readback still pending |
| Commit / push / deployment | None; existing unrelated changes retained |
| Overall status | IMPLEMENTED_STATIC_COMPONENT_PENDING_USER_RUNTIME |

## What is ready

The independent PS2-enabled proxy contains a narrowly gated reflection experiment
for one original Tata bonnet material. It uses an original PS2 image contribution
and additive color combination grounded in REFL1. It does not reproduce the full
mixed PS2 environment target or claim visual parity.

The original PS2 path is carshiny handler 0x3ade58 -> mode 3 -> shared
rendertarget64x64. REFL1's producer 0x330780 -> 0x31a518 combines ENVSOURCE at
80/128 with a vertically flipped current framebuffer at 48/128. The secondary
body pass uses ALPHA 0x0000008000000029, yielding Cd + Cs. This pilot implements
the static RGB term explicitly; the framebuffer term, body grayscale preparation,
two-pass GS rasterization and exact VU coordinates remain deferred.

See [the original material witness](material-source-contract.json) and
[implementation](design-and-implementation.md). The canonical PS2 corpus was
freshly hash-checked with existing PackFS infrastructure. The original PC x86
constructor was independently inspected through REA and its 113-byte probe
checked against the original executable. No new broad R5900 or emulator pass
was necessary.

## Why this material is selected

The protected retail Tata/car.dx SHA is
45b7bfba6938e259c0ac6d79a42a878a8c66b1e53547a53a6d23343092fb34cb.
Record 19 contains 48 vertices, 165 indices and 55 triangles, with ordered
slots tatabon-tga / whitepaint-tga / Null. Its position/face multiset signature is
f80ae53d8c8691ebb8387680b0555343e10100459949c56e3338c484b680e669.
The signature is unique in all 78 examined retail vehicle DX files. This is source
evidence, not an assertion that a native draw ordinal or a live instance has been
captured.

Live admission additionally requires current mirrored geometry/resource
generations and revisions, the supported executable, verified race ownership,
the existing unambiguous vehicle-body oracle and exact original native material
stage states. A changed mesh, unknown owner, stale buffer, unsupported texture
or conflicting ViewDependent2D mode fails closed. No texture-only predicate is used.

## Native state and lifetime

The integration snapshots immutable draw inputs. It saves the exact native stage
1 COLOROP and texture binding, applies ADD and the private image, submits one
original DrawIndexedPrimitive and restores both values. Native render states,
alpha/depth policy, stage arguments, UV matrix, render target and draw order are
preserved. Logical game state is untouched; effective tracking follows native
writes and restoration. Submitted native HRESULTs are preserved.

Partial application rolls back. A failed restoration retains the original COM
reference for repair before subsequent draws/state blocks. If repair remains
impossible, an unsafe later draw is rejected. Reset releases private resources;
a failed actual reset suspends the effect while preserving mirroring, and a
successful actual reset recreates the image. Window-mode reset echoes bypass
that lifecycle. Final private resources release before native device Release.

## Build gate and preserved baseline

The overlay now locks the complete renderer Git tree rather than the repository
HEAD. Unrelated research commits may proceed with an identical renderer tree;
committed drift, tracked edits and untracked renderer sources are rejected.
Staging still reads immutable objects at the pinned commit. Exact patch/path,
source hash and repeated generator-output checks remain enforced.

Both Win32 Release variants were built separately with --parallel 1.
[build-report.json](build-report.json) contains artifact/source hashes,
[validation.md](validation.md) records focused results, and
[command-log.md](command-log.md) separates actual commands from recipes.
Earlier PILOT1.4 archive, DLL, geometry classifier and pixel diagnostic remain
preserved. No permanent modernization/renderer file changed.

## User check and next step

Use [the A/B recipe](runtime-ab.md): Tata, France1, identical Free Camera bookmark,
paint and lighting; original game Reflections enabled; renderer VehicleReflections
Mode=0. Restart between ReflectionMode=0 and 1 with foliage/pixel modes at zero.
Only the verified bonnet material should change. A successful bounded application
log and unchanged neighboring materials are needed before claiming PC runtime
success. Driver behavior, visible improvement and PS2 equivalence remain pending.

The single next recommendation is **PS2-COURSE-OBJECT-PORT1**, preparing one
France1 dinghy transform and exact baked-PC counterpart before any import.
It has not been started. See [next.md](next.md).
