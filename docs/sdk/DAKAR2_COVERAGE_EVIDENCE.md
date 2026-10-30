# Dakar 2 Xbox coverage and texture-address evidence

This is the v8.1 bounded follow-up to the existing source-material decoder. It
does not introduce a native compiler, a runtime slot, new geometry or new glass
and lamp ownership. The original scenes and their pixel definitions remain
immutable. Source rendering is still L2 WARN, and these CPU rules alone cannot
approve a complete L3 material translation.

## Exact original build and reproducibility

Original `default.xbe` SHA256:
`715db4e407b38c0a6d14ea0ee9d08ebc524b9ece92ceeaa70b5fb81a5ec32378`.

`tools/probe_dakar2_coverage.py` reads that executable from the owner-local Xbox
disc through the existing XDVDFS reader. It checks the exact hash and original
section mappings before replaying bounded CPU routines with Unicorn. The tool
writes only to a fresh, source-disjoint private output directory. It exports
hashes and state observations; it does not package original executable or shader
bytes. `dakar2_coverage.py` provides source-bound coverage/address rules and
rejects implicit entry-alpha/reference assumptions.

Private verified output:
`.research-output/vehicles/dakar2-material-closure/coverage/verified-final/`.

## Coverage is selected by HIR kind and original LOD flags

`0x46da0` copies the **first DWORD of each original 0xd4-byte HIR record** to
the first field of the corresponding 0x290-byte runtime node. This source kind
is distinct from the sequential node ordinal stored in Universal Vehicle Scene.
The source kind is read from the already retained, hash-pinned `ALL.RBB`; the
existing HIR record hash and exact node/LOD ownership are checked again.

`0x46ae0` draws nodes without LOD flag `0x08000000` in its first loop. It draws
the flagged nodes in its second loop. In the second loop only, it enables
alpha-test if either:

- the original HIR kind is in the inclusive range 1 through 7; or
- original LOD flag `0x10000000` is set.

It then invokes `0x86920(4, [0x18eab4])`: comparison GREATER, reference from the
original global. After each second-pass node, it invokes `0x86920(7,0)` and
`0x88100(0)`: ALWAYS, reference zero, alpha-test disabled. All submeshes of that
node share the state; the reset occurs after the whole node, not after each
submesh.

The original enable path is `0x880e0(0)` → `0x87eb0` →
`0x87470(0x3c,1)`. Disable follows the corresponding `0x88100(0)` path.
`0x86920` writes reference through state `0x3d` and compare through `0x3a`.
This is separate from declaration-specific alpha **blending** in `0x8b360`.

The first loop inherits entry alpha-test state. The first second-pass node can
also inherit that state if it does not satisfy the explicit cutout predicate.
The decoder therefore requires an explicit incoming enable and effective
reference. It never assumes that every transparent texture is cutout glass or a
brake controller. A disabled-entry reconstruction is a named static context,
not a capture of an original running Xbox.

| Source vehicle | First-pass draws | Second-pass draws without explicit cutout | Second-pass explicit cutout |
| --- | ---: | ---: | ---: |
| Pajero | 38 | 10 | 8 |
| Nissan Pickup | 30 | 13 | 8 |
| Hino Ranger | 41 | 6 | 0 |

These totals are draw groups, not nodes. Pajero and Nissan's four road wheels
have source kinds 1,2,3,4 and two draw groups each. Their window/headlight-cover
and internal spare-wheel nodes have kind zero; those labels do not automatically
enable alpha-test. Hino's road-wheel kinds are also 1,2,3,4, but their LOD flags
place them in the **first pass**, so the second-pass wheel predicate does not
apply. Hino is an independent case, not a copy of Pajero policy.

## Effective reference and controlled CPU checks

The original data at `0x18eab4` is 100. Its known direct writers are in the
separate `0x13400` path: save the value, temporarily use 10, draw a different
hierarchy through `0x46ae0`, then restore the original value. Thus 100 is an
original initialized value and ordinary-path static inference, not a universal
runtime constant across all uses of `0x46ae0`.

The probe replays the **original instructions** of `0x46ae0`, `0x86920`,
`0x880e0`, `0x88100`, `0x87eb0` and `0x87470` against five synthetic nodes.
Only the matrix, draw, triangle-count and matrix-stack helpers are stubbed;
the observed state is the original CPU's deferred state, not GPU pixels. The
five cases are first-pass road wheel, second-pass kind-zero surface,
second-pass wheel, following kind-zero surface, and explicit LOD cutout flag.
Each of the 100 and 10 reference runs follows the expected schedule in **687
instructions**, including the post-wheel reset that prevents cutout state from
leaking to the following window-like node. This verifies the source rule and
reference dependence, without claiming emulator rendering parity.

## Original pixel-constant upload

`0xe6210` wraps a non-null pixel-definition pointer and passes it to
`0xe6250`. The latter copies the original embedded constant arrays into the
push buffer. The probe executes `0xe6250` with the two selected original pixel
definitions, an explicit previous non-null shader and a bounded empty push
buffer. No upload/overflow helper is replaced: an unexpected helper call fails
the probe.

Both original CPU replays return in **187 instructions**, writing 240 bytes.
All sixteen uploaded constant DWORDs equal their original definition arrays.
For `0x192058`, stage1 C0 is exactly ARGB `0x59000000`, alpha **89/255** at
this upload. For `0x192148`, its unused stage1 C0 is zero. The stored software
constant mapping is metadata; its presence alone does not prove a game call
updates that constant.

Bounded application/SDK instruction inspection found no direct call through the
game's `0x87470` setter selecting PS field indices below `0x39`; the inspected
game calls select render states at `0x39` and above. This is useful negative
static evidence, **not proof against indirect calls, shader overrides, saved
state restoration or every original runtime path**. The decoder must continue
requiring explicitly qualified effective mapped constants. An embedded initial
upload cannot silently authorize a static bake in the presence of an unresolved
runtime context.

## Texture addressing

`0x8ac20` constructs the native texture header at source XTX `+0x18` and retains
the source flag word at `+0x10`. `0x8dbe0` passes ordinary textures through;
its special marker paths handle other resource forms. `0x8b590` calls
`0x8aed0(stage, texture, 2)` for all four original texture fields. The third
argument equal to two forces the source-address-flag branch even when the
global addressing override is enabled.

For the low two flag bits, the original branch sets U/V as follows:

| `flags & 3` | Original U value | Original V value |
| ---: | ---: | ---: |
| 0 | 3 | 3 |
| 1 | 1 | 3 |
| 2 | 3 | 1 |
| 3 | 1 | 1 |

The original API values are 1 for wrap and 3 for clamp. All 11 Pajero, 13 Nissan
and 13 Hino retained XTX textures have the original flag word **7** and select
U/V **1/1**. The remaining flag value `0x4` stays retained and uninterpreted by this narrow
address decoder. This result qualifies source addressing for these bound
resources, not texture-coordinate generation, filtering, mip LOD or the
secondary-stage shader contribution.

## Remaining boundary

Coverage and initial constant upload are now reproducible source evidence.
They do not establish original dynamic vertex lighting, reflection coordinates,
effective complete draw context, dynamic lamp ownership, glass opacity, damage
state, optional equipment selection, Xbox GPU precision or MR equivalence.
The source snapshots, UVs, normals, geometry, textures, alpha samples and Nissan
transforms are unchanged. Any parent material qualification must keep these
independent dependencies visible.

## Owner-local runtime evidence boundary

A bounded read-only inventory checked the source Xbox directory, Source Garage
tools/research directories, `C:/Games`, top-level `D:/Game` directories,
AppData Roaming/Local names, Downloads names, ShareX screenshot names and the
repository's retained evidence filenames. The Xbox source folder contains the
original ISO only. No xemu/Cxbx installation, original Xbox game capture or
PGRAPH trace was found in these inspected roots: **MISSING INPUT** for runtime
corroboration. This is not a whole-machine absence claim. Xenia Canary is an
Xbox360 emulator, PCSX2 Nightly is PS2, and the local Xbox360 ISO extraction tool
is not an original Xbox runtime. No emulator was installed, configured or
launched. The bounded inventory is recorded privately in
`coverage/runtime-reference-inventory.json`.

## Existing MR environment mechanisms: useful but not equivalent by default

The existing shared bridge accepts an explicitly pinned native environment
helper through `environment_reference`, and requires complete original material
ownership. Existing native/GT4 qualification describes MR COLOROP18 as
`base.rgb + base.alpha * helper.rgb`; `gt4_mr_materials.py` admits only proven
coverage, compatible alpha/DATE behavior and complete oriented geometry pairs.
It explicitly describes MR normal-coordinate environment generation as a
renderer approximation. Workshop material controls keep blended/cutout and
unknown shader families read-only; opaque reflection weights are distinct from
ordinary opacity (`help/en/materials.md`, `material_semantics.py`).

This does not establish a Dakar2 translation for the independent T1 alpha mask,
T0 output alpha and dynamically generated T2 coordinates. A derived opaque-only
weight texture could be investigated where every coverage condition is proven,
but it must not silently repurpose glass/cutout alpha, erase the source mask or
claim identical coordinate generation. The current shared helper has no proven
automatic contract for those independent Xbox inputs. These existing mechanisms
therefore remain an evaluated alternative, not a generic material PASS or
permission to add fragmented reflection geometry.
