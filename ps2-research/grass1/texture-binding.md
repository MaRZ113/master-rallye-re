# Grass and shrub resource binding

The resource proof now goes beyond existence and loader xrefs.

| Category | Owner pool | Category name field | Canonical resource | Status |
|---|---:|---|---|---|
| grass | 1 | record +40: `particles/grass1` | `\TNG\DATAPSM\PARTICLES\GRASS1.GXI` | CONFIRMED_BY_BOTH for selection/binding path |
| shrubs | 0 | record +40: `particles/bush1` | `\TNG\DATAPSM\PARTICLES\BUSH1.GXI` | CONFIRMED_BY_BOTH for selection/binding path |
| stones | none | Directive ID only | No image selected by this generator | CONFIRMED_BY_EXE, bounded exclusion |
| none / singular shrub | none | No generating category record | No detail image selected | CONFIRMED_BY_EXE |

`34e698` initializes the resource-name interner IDs from anchors
`486180/486190`. `3581e8` traverses the two pools, obtains record `+0x40`,
looks up its owner cache (100 hash slots, key from name ID +1), and on a miss
calls **2fd7d0**. That routine resolves the runtime resource root, appends the
interned relative image name and **`.gxi`** at `4846a0`, and calls manager
filename cache/create `2f84f0`, then residence `2f9c80` as required.

The returned handle is cached in the owner entry value at `+0x0c`. The same
handle pointer is supplied to renderer virtual slot `+0xc0` at vtable
`4853f0`, independently resolving to **311c50** (callsite fields include the
four-byte adjustment slot immediately before each function pointer).
`311c50` indexes 48-byte texture-state entries at global `42e430`, ensures
residence through `2fa058`, and writes TEX0/TEX1/MIPTBP state templates.
`31c8f8` snapshots those templates before `3597e0` appends that pool's points.
Thus selection is **per category/batch**, with cached resource handles, not a
per-instance random image choice.

RESOURCE_EXISTS: independently extracted/hash-checked GXI files are 32×32;
stored alpha ranges 0–255 with 223 grass / 213 bush distinct values.
RESOURCE_LOADED_BY_DETAIL_SYSTEM: original relative names, root/extension
construction and manager calls are tied to the pool loop.
RESOURCE_BOUND_TO_DETAIL_BATCH: returned handle, renderer virtual bind and
state snapshot precede that pool's record append. These three proof levels
describe the static load-request/binding contract; the runtime root value and
actual RAM handle were not captured. **RESOURCE_BOUND_TO_A_VISIBLE_RUNTIME_INSTANCE**
remains UNKNOWN.

GXI decoded hashes: grass
`519908ac79ca57591a8a38d3629286e25ffc51539705342864a5056785427eb6`;
bush `2e4178614fbcbb3dbc3eaf5931001d2a566e76d59ef6adf7e66cd372556d40e9`.
Existing PackFS and GXI infrastructure is reused; no second image parser was
created. Ordinary course `GRASS-TGA` ground textures are not these resources.

The general filename-cache export truncates in packed-instruction code.
Complete missing-image fallback, texture decoding/upload semantics, actual
live TEX0 address and all unrelated image consumers are not certified.
No additional stone resource/primitive is inferred from its directive.
