# R5V-J — Generic Addon Vehicle SDK architecture

J.0 provides versioned addon definitions and a deterministic offline compiler
foundation. J.1 adds a separate exact-build Windows launcher and external
resource bundle. J.1 is **CLOSED / CONFIRMED_BY_RUNTIME**. J.2 is also
**FULL PASS / CLOSED**: the capture batch confirms two-addon SplitScreen, Cup
stage reuse, Master Rallye fresh-process persistence and the hardened Dump
walker; the owner separately confirmed the exact corrected ID27 Vehicle Select
re-entry candidate. That report is not represented as a new Observatory
capture. See `j2/closeout-2026-10-09.md` for provenance and identities.

The components are separated deliberately:

1. **Vehicle definition** — strict JSON manifest v1.
2. **Validator** — validates identity, class, physical-ID policy, family paths,
   presentation, unlock/audio/AI/Results policies, and the selected target
   capability profile.
3. **Compiler** — resolves IDs and class ordinals, computes the audited
   registry layout, and emits deterministic semantic integration plans.
4. **Runtime integration** — the research J.1 launcher verifies
   and starts the byte-exact retail EXE without replacing it. Its separate
   `addon runtime-*` artifacts verify an external resource root and translate
   the audited H.2/I.1 byte layers into file-offset/RVA operations for install
   before the suspended process first resumes. Runtime qualification does not
   set the J.0 offline plan's `runtime_installable` flag and does not establish
   a public loader release.

This generic addon SDK is separate from the frozen
[vehicle authoring SDK v1](../../../docs/vehicle-sdk.md). R4G edits/validates existing donor-based DX,
DXT and collision resources. J0 describes an addon identity and plans how its
already-qualified payload is routed into the game. Authoring, addon
integration, and runtime deployment remain distinct layers.

The supplied Mercedes and R5VQualifier examples are metadata-only. They do
not contain proprietary model, wheel, texture, physics, sound, or game files.
R5VQualifier is authored qualification content, not historical game content.

Run from the repository root:

```powershell
py -3 tools/mrtool.py addon validate `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json

py -3 tools/mrtool.py addon build `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json `
  --output .research-output/vehicles/sdk/reference-build

py -3 tools/mrtool.py addon verify .research-output/vehicles/sdk/reference-build
```

Build output is a deterministic **offline plan**, not an installable mod. The
separate J.1 launcher and runtime bundle are documented in
[runtime deployment](runtime-deployment.md) and
[the loader decision](loader-decision.md). See
[manifest schema](manifest-schema.md), [compilation](compilation.md), and
[remaining gates](remaining-gates.md).

## R5V-J.3 donor-authoring productization

J.3-A adds a project initializer and bridge to the existing VehicleProject
validators/build outputs. A project owns an addon manifest plus a VehicleProject
recipe; no DX/DXT or collision parser was duplicated. The project compiler can
stage validated model and DXT dependencies under the declared independent
family and, when the exact pinned retail Data.sma and matching unpacked root
are supplied, clone the donor's DataGame physics/config values into a separate
family namespace. These DataGame rows inherit donor values unchanged.

The independent Glacier Sprint T2 manifest demonstrates a new family and
frontend name without SDK-source changes. It resolves synthetically to the
qualified physical slot ID27/T2/local7. That does not runtime-qualify Glacier
Sprint: only the exact Mercedes ID26 and R5VQualifier ID27 profiles have game
runtime qualification.

The offline author build remains `runtime_installable=false`. J.3-B adds a
separate statically verified collection runtime artifact for the bounded
ID26/T1 plus ID27/T2 layout and uses the unchanged-executable J.1/J.2 launcher
format. GlacierSprint is ready for human runtime testing, not runtime-qualified;
T2-only input fails closed. See [`j3/release-boundary.md`](j3/release-boundary.md)
and [`j3/runtime-compiler.md`](j3/runtime-compiler.md).
