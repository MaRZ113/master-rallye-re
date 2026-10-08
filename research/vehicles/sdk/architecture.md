# R5V-J.0 — Generic Addon Vehicle SDK architecture

J.0 introduces a versioned addon definition and deterministic offline compiler
foundation. It does not patch or launch `MRallye.exe`, distribute game assets,
or claim a public runtime release.

The components are separated deliberately:

1. **Vehicle definition** — strict JSON manifest v1.
2. **Validator** — validates identity, class, physical-ID policy, family paths,
   presentation, unlock/audio/AI/Results policies, and the selected target
   capability profile.
3. **Compiler** — resolves IDs and class ordinals, computes the audited
   registry layout, and emits deterministic semantic integration plans.
4. **Runtime integration** — not implemented. It must later preserve the
   retail executable on disk, verify the exact supported build, install a
   removable external runtime component, and fail closed on unknown builds,
   missing resources, or conflicts.

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

Build output is a deterministic **offline plan**, not an installable mod. See
[manifest schema](manifest-schema.md), [compilation](compilation.md), and
[remaining gates](remaining-gates.md).
