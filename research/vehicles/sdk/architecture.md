# R5V-J — Generic Addon Vehicle SDK architecture

J.0 introduces a versioned addon definition and deterministic offline compiler
foundation. J.1 now adds a separate, exact-build Windows launcher candidate and
an external resource bundle. The launcher can install an audited operation set
into a suspended retail process, but no human startup or addon runtime test has
been recorded; J.1 is not runtime-qualified and J.0 output semantics remain
offline-only.

The components are separated deliberately:

1. **Vehicle definition** — strict JSON manifest v1.
2. **Validator** — validates identity, class, physical-ID policy, family paths,
   presentation, unlock/audio/AI/Results policies, and the selected target
   capability profile.
3. **Compiler** — resolves IDs and class ordinals, computes the audited
   registry layout, and emits deterministic semantic integration plans.
4. **Runtime integration** — a research-only J.1 launcher candidate verifies
   and starts the byte-exact retail EXE without replacing it. Its separate
   `addon runtime-*` artifacts verify an external resource root and translate
   the audited H.2/I.1 byte layers into file-offset/RVA operations for install
   before the suspended process first resumes. This does not set the J.0
   offline plan's `runtime_installable` flag and does not establish a public
   loader release.

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
