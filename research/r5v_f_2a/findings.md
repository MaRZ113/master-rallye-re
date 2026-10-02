# R5V-F.2a — retail-native Mercedes cooker bridge

**Result: BLOCKED before cooking.** Retail statically contains the expected
GXM→DX and GXI→DXT cache paths, and the model writer emits the retail DX
revision marker. The exact Mercedes source and retail executable are now
hash-locked. No source-specific cook was run, no DX/DXT was generated, and no
registry, executable, archive, or canonical vehicle resource was modified.

The selected unique source remains demo-8.4.1 `DataGx/Vehicles/Copy of
Mercedes`. All 59 root files match the prior inventory. Its three source GXM
files contain 25 distinct GXI dependencies, but their serialized references
are absolute paths rooted at
`D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes/`. Retail's cache writer uses
ordinary file creation for DXT output; the extracted caller does not establish
a safe writable mapping from those embedded paths into a cloned retail
workspace. A source-path staging/rebase method and runtime cache-miss trace are
therefore still needed before we can claim a reproducible pipeline.

## What is proven

- The exact retail `MRallye.exe` SHA-256 is
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- In retail, `FUN_0053be70` calls `FUN_0053c3f0`. The latter builds `.gxm` and
  `.dx` paths, accepts a valid cache on a source/cache metric comparison, and
  otherwise calls the GXM reader/builder before the DX writer.
- `FUN_00551260` is reached from the model cook path. Raw assembly pushes
  `0xD00D` and then `0x87`; the latter is revision 135. This is static writer
  evidence, not a runtime output check.
- The texture manager has separate cache-hit and source-cook paths: `.gxi` is
  read and transformed, then a `.dxt` cache writer is called. This path is
  separate from the model DX cache.
- The selected folder has all 25 GXI/DXT filename pairs. Existing DXT files
  parse, and the previous offline GXI→DXT encoder reproduces their bytes. That
  does not establish that retail's own DXT writer produces the same bytes or
  that the retail loader resolves the embedded absolute names in this corpus.

## What is not proven

- No retail run logged `Reading GXM`, `Making dx model`, or `Saved cached model`
  for any Mercedes role.
- No retail run logged `Reading GXI` / `Saved cached texture` for the 25 source
  textures.
- `complete`, `car`, and `wheel` were not forced through retail's cache-miss
  path. There are no Cook A/B output hashes.
- No revision-135 outputs exist to parse, round-trip, compare semantically, or
  inspect for collision retention.
- No Mercedes package is ready for F.2 P0/P1. Retail Mercedes physics,
  localization, and prior collision research remain separate, already-documented
  findings; this phase changes none of those conclusions.

## Exact remaining edge

The missing edge is:

```text
hash-locked Copy of Mercedes GXM/GXI
    -> isolated, writable paths matching the serialized texture references
    -> retail runtime cache miss for all three roles
    -> repeatable revision-135 DX + usable DXT outputs
    -> SDK, geometry, collision, material and texture validation
```

The smallest next research action is to establish a reversible isolated
source-path mapping for the length-prefixed GXM GXI references, then capture a
retail cook in an isolated runtime copy with the original registry unchanged.
Do not patch ID26 to Mercedes until all output gates pass.

See the detailed [model cooker](retail-model-cooker.md), [texture cooker](retail-texture-cooker.md),
[source manifest](mercedes-source-manifest.md), [workflow](cook-workflow.md),
[determinism](determinism.md), [model validation](model-validation.md),
[collision validation](collision-validation.md), [texture validation](texture-validation.md),
and [gate summary](validation.md).
