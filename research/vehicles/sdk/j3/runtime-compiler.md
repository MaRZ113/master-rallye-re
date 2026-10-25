# J.3-B collection runtime compiler

## Scope

`tools/addon_collection_runtime.py` compiles a complete manifest collection and
one validated author-project build into the external runtime bundle format
consumed by the existing J.1/J.2 launcher. It does not modify or emit
`MRallye.exe`, the retail `Data.sma`, or the J.0 offline-plan semantics.

The first implementation is deliberately capability-bounded to exactly:

- Mercedes physical ID26, T1/local7, from the qualified Mercedes manifest and
  the pinned I.1 external resource package;
- one ID27, T2/local7 vehicle, from either the exact I.1 reference package or
  a project build validated from the supported Navara donor.

A T2-only collection fails closed. The compiler does not insert Mercedes
implicitly. Other IDs, layouts, donor families, unlock/audio policies, resource
overrides, or family-routing arrangements remain unsupported until qualified.

## Compile and verify

Use the stable `mrtool addon` entry point. Paths below assume the canonical
vehicle worktree and the user-owned Glacier Sprint author project:

```powershell
$env:PYTHONPATH='src'
python tools/mrtool.py addon runtime-prepare `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/glacier-sprint-t2.json `
  --project-build glacier-sprint-t2=.research-output/vehicles/sdk/j3/glacier-sprint-build-20261009-3 `
  --output .research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final
python tools/mrtool.py addon runtime-verify `
  .research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/glacier-sprint-t2.json `
  --project-build glacier-sprint-t2=.research-output/vehicles/sdk/j3/glacier-sprint-build-20261009-3
python tools/mrtool.py addon runtime-launcher-build `
  .research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/glacier-sprint-t2.json `
  --project-build glacier-sprint-t2=.research-output/vehicles/sdk/j3/glacier-sprint-build-20261009-3 `
  --launcher-output .research-output/vehicles/sdk/j3b/glacier-sprint-launcher
```

`runtime-prepare` validates the exact retail build, capability file, both
manifests, author build provenance, DataGame family rows, required DX/DXT
closure, frontend scene source, stock SmallCarSheet member, native operation
preimages, sparse ID/class mapping, and non-overlapping J.2 re-entry code. It
stages into a new directory and refuses overwrite. `runtime-verify` reconstructs
the output deterministically and checks every file, resource path, size and
hash. `runtime-launcher-build` first invokes that same verifier and then builds
the existing audited x64 Windows launcher against the collection's trust
profile.

The older `addon build` and `addon verify` remain offline semantic/project
commands. Their `runtime_installable=false` field is unchanged. A runtime
bundle has its own `runtime-artifact.json`; it is statically ready for a human
run, never marked runtime-qualified by compilation.

## Composition and identity

The native compiler resolves the whole addon plan, requires the qualified
ID26+ID27 sparse layout, writes ID27's manifest-configured record (including
race-marker RGBA), and generates fresh native operations from the exact retail
preimages. It composes those operations with the audited J.2 constructor
republisher and keeps the invariant:

```text
local_field_offset = 0x14 + 4 * class_id
```

For ID27/T2, the field is `this+0x18`; the emitted instruction is
`C7 46 18 07`. The J.2 path uses a deterministic, zero-preimage executable
`.text` cave in the previously qualified page. The reference-pair regression
continues to choose `0x0068EB40`; the longer Glacier native identity occupies
that location, so the composer selects the first safe aligned cave at
`0x0068EFA0`. The selected address and operation are recorded in the native
patch manifest, and the stub bytes are decoded and symbolically ABI-checked.

The resource root starts from the hash-pinned I.1 resource package. For a
custom ID27 family it removes only the previous ID27 family and the three
composed resources (`DataGame/vehicles.xml`, `DataGame/Modifications.xml`, and
`DataScene/FrontendScreens/VehicleSelect.xml`), then inserts the verified
project model/texture closure and donor-derived physics family. Mercedes rows
are compared before and after. `Data.sma` remains byte-identical; its
SmallCarSheet frame is checked as an embedded archive member, not extracted as
a made-up loose override. The original executable is neither copied nor
written.

## Current evidence boundary

The reference Mercedes+R5VQualifier collection reproduces J.2's corrected
reconstructed image and operation table. The Glacier collection has a separate
plan, manifest, RVP table, image reconstruction, and 187-file external resource
root. The compiled native launcher statically verifies that bundle. These are
static package/build checks. GlacierSprint has not yet been confirmed by a
human in the game; its identity remains unqualified. See
[`runtime-validation.md`](runtime-validation.md) and
[`runtime-handoff.md`](runtime-handoff.md).
