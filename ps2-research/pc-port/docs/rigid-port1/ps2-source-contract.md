# Original Turkey3 tumbleweed: source and bounded native conversion contract

The original tumbleweed hull is wire-compatible with the already studied PC
tag101 counted format. Fresh extraction and the existing Course SDK's strict
reader/canonical serializer reproduce it **byte-identically**. This is a format
result, not successful private-resource registration, entity creation or vehicle
contact. No physics object was spawned in this source investigation.

The compact facts, original byte offsets, topology hashes and short R5900
instruction windows are in `ps2-source-contract.json`. Full mesh and texture
arrays are excluded. Original hull bytes remain ignored under
`ps2-research/data/rigid-port1/Turkey3Tumbleweed.tag101`.

## Selected authored identity

| Field | Fresh original-byte result |
|---|---|
| Scene | `\TNG\DATASCENE\RACETEST\TURKEY3.XML` |
| XML SHA-256 | `7c1c274cd8403bc7fcc2b5e2e8a13e57dccc44dade53a1be57d631ea073e51ce` |
| Selected record | `list:11:egg:13:ai:0`; `IContManager`, `tumbleweed`, `gaAiRigidBody` |
| Count | Six authored rigid tumbleweed records; live admitted population remains UNKNOWN |
| Model spelling | `misc\objects\tumbleweed\tumblweed` |
| Initial translation | Float32 `(3213.659912109375, 43.099998474121094, -155.13999938964844)` |
| Basis | Authored identity 3×3, row-major en3d matrix; homogeneous last value 1 |
| Matrix SHA-256 | `dbb65381027ae9e1c0d3f76271b1a7bd5eca952dfc03e2094ac290686e99f7dc` |
| Mass | `5.00000`, direct source mass, not density |
| Local inertia | MOI diagonal `(2,2,2)`, not inverse inertia |
| Trigger Distance | `5.00000`; selected owner update does not read it |
| Casts Shadow | `True`; deeper shadow consumer remains UNKNOWN |

All six records use these mass/inertia/trigger/shadow values and identity
orientation. The selected original translation is an authored starting pose;
native initial collision placement may change its height. It must not be
advertised as the measured settled world position. The five other source IDs
are retained without publishing all their placement matrices.

## Visual source

The canonical model resource is
`\TNG\DATAPSM\MISC\OBJECTS\TUMBLEWEED\TUMBLWEED.PSM`, 9,819 bytes,
SHA-256 `eb959250d0bdb6fa051fb69f4a852c4789be200613eb8e90678d36a48ab54bf4`.
Existing WATER1/RIGID1 parsing freshly reproduces 96 source vertex records,
one material-owning mesh at byte 5032, four strips and 48 nonsuppressed,
nondegenerate visual-source triangles. Source bounds are approximately
`(-1.03446,-0.877456,-1.05100)..(1.03645,0.874627,1.05026)` in **MODEL_LOCAL**
coordinates. These are neither a live polygon count nor collision bounds.

Material bytes at 5100 read `bigshrub $shader(treeblend)`. Slot0 at 5054 is
`Misc\Objects\Tumbleweed\shrubtrig2-tga`, with literal source map flags
`[true,true,false]`. Mesh flags and the strip flag/scale values are preserved in
the JSON; their unproved semantics are not converted into PC culling flags.
The last strip vertex's control bit0 suppression remains the original source
triangle rule. Winding/live back-face behavior is a separate rendering gate.

The 52-byte original source vertex contains normal XYZ at +0, control at +12,
color u32 at +16, four UV float words at +20 and position XYZW at +36.
Normals and positions are model-local. The measured normal-length range is
`0.999999985875..1.000000121102`; this is a host numerical check. Original
color words are `0x949494ff` (56 source records) and `0xe0e0e0ff` (40).
Original normal/UV/control hashes are retained. A future PC draw must explicitly
map the existing source-color contract to D3D diffuse rather than memcpy an
unverified channel interpretation.

The exact texture exists at
`\TNG\DATAPSM\MISC\OBJECTS\TUMBLEWEED\SHRUBTRIG2-TGA.GXI`:

- SHA-256 `e34ca0193956eca2d03217fb18929b6ec0a78cfe2d9d6e6a081b8b10c934fc4f`;
- supported simple GXI `0x13039`, 64×64, 16,392 bytes;
- existing GXI interpretation RGBA; stored alpha 0..255, 255 distinct values,
  2,430 nonzero-alpha texels.

The resource and material reference are **CONFIRMED_BY_BYTES**. A selected live
tumbleweed texture binding has not been captured. TREEBLEND1's independently
revalidated mode2 contract supplies alpha-test OFF, blending ON, masked depth
write, `(Cs-Cd)*As/128+Cd` and bucket1 within the traced drain. Inherited GS
state and live order remain separate. Ordinary D3D8 SRCALPHA/INVSRCALPHA is an
approximation; no PS2 visual parity is claimed for this future object.

## Exact native convex wire

The original PSM visual tree stops at **5203**. The tag101 block is exactly
`PSM[5203:9815]`; the four-byte `ffffffff` trailer is outside the block. The
existing PC collision parser consumes it strictly without scanning/resync or
guessed sizes. The canonical serializer preserves every byte, collection order,
index, centroid/reference point, edge, face descriptor, adjacency, face loop and
area scalar.

| Input boundary | Bytes | SHA-256 |
|---|---:|---|
| Complete tag101, including dispatch u32 | 4,612 | `27cb1089bf997a0b20d6a4f98fee9827a9089972ff6e891fce5cf34e41e01d48` |
| Reader payload after dispatch | 4,608 | `83d6bd02133d7e8b262243c9b716c73e4ada3a0a717d612dbb2c25b5cab43e41` |

The original PC contract at `0x0057CE60` reads base geometry through
`0x0057D640`, then a float32 base scalar and two representations through
`0x0057D140`. At that entry, the enclosing dispatch has consumed tag101;
feed `wire[4:]` exactly once. Feeding the whole PSM, a DX header or the dispatch
tag again is not this reader contract. A native bounded-stream adapter is still
required and has not been validated by this serializer exercise.

Relative offsets below are measured from the tag word:

| Section | Start | End exclusive | Source facts |
|---|---:|---:|---|
| Outer tag/base/scalar | 0 | 28 | Base1 vertex/0 triangles; scalar `1.0692750215530396` |
| Representation A | 28 | 892 | Geometry A8 vertices/12 triangles; point geometry B1/0; 8 refs,12 edges,6 faces |
| Representation B | 892 | 4612 | Geometry A26 vertices/48 triangles; point geometry B1/0; 26 refs,56 edges,32 faces |

The JSON includes contiguous field-by-field wire accounting. Counts, indices
and finite values are strict-reader validated; serialize/reparse equality is
tested. This does **not** certify which representation the live narrowphase
selects, a new hull's behavioral correctness or resource ownership.

`representation_a`/`representation_b` are the existing SDK's **serialization
order** names: the8/12 block precedes the26/48 block in this source. They must
not be silently mapped to a native prototype's first/second pointer slot.
Reader store offsets, instance clone slot order and backend's choice of detail
level require their own original-PC instruction evidence. This source JSON
deliberately contains no guessed prototype/instance field mapping.

Conversion policy is deliberately minimal: preserve this original hull in
**MODEL_LOCAL** float32 coordinates; apply the selected Egg/native body pose
once. Do not bake course translation into hull vertices, swap Y/Z for Blender,
infer a COM from mesh bounds, substitute a sphere, or replace representation B
with the original PC haybale's different16/28 hull. No new topology is cooked.

## Direct R5900 corroboration

The exact ELF remains 3,739,852 bytes, SHA-256
`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`.
Its file-backed PT_LOAD maps offset0x1000 to VA0x100000. Ghidra12.1.4 EER opened
the existing project **read-only**, `r5900:LE:32:default`, with no reanalysis,
instruction replacement or generic-MIPS surrogate. Rabbitizer1.16.2 explicitly
used `InstrCategory.R5900`. All141 original words in five bounded windows matched
their original ELF bytes and decoded as valid R5900 instructions.

| Original VA window | Confirmed operation |
|---|---|
| `0x0019fe98..0x0019ff14` | Typed shadow/mass/trigger/MOI readers |
| `0x001a0058..0x001a00e0` | Owner mass to body+20 and inverse+24; direct MOI diagonal to local inertia+28; `0x00203358` matrix inverse |
| `0x0027d060..0x0027d0a0` | Gravity callback `F=(0,-g*m,0)`; no wind term in this callback |
| `0x00244230..0x00244250` | Body binding into instance+10, both representations+2c, base+08 |
| `0x003946e0..0x003947b0` | Source convex loader calls `0x003b4c20`, assigns model+34 for nonwheel path |

The compact JSON retains the critical original mass/inertia/gravity/body-binding
instruction windows. RIGID1 supplies the wider static owner/manager/contact
chain: two halfsteps per manager invocation, RK4 mode1, momentum/quaternion
state, contact wake, rest/pause behavior and same-entity Broker world-matrix
publication. No live cadence, wind, solver coefficient or impact amplitude is
invented from those instructions. Fresh windows reinforce the parameter/shape
contract; they do not convert old generic-MIPS pseudocode into source authority.

## Reproduction and dependencies

The tool uses existing PackFS/PSM code and read-only SDK APIs. The reference SDK
was clean at `4244fa0c4d878523c9947f54816bf377cdfb2589`; parser/serializer file
hashes are recorded. It was not modified or compiled.

Executed from the primary repository:

```powershell
python ps2-research/pc-port/tools/prepare_tumbleweed_contract.py `
  --ps2-root 'D:\Game\Master Rallye PS2' `
  --sdk-root 'D:\Game\Master Rallye\master-rallye-re-course' `
  --output ps2-research/pc-port/docs/rigid-port1/ps2-source-contract.json `
  --native-wire ps2-research/data/rigid-port1/Turkey3Tumbleweed.tag101
python -m unittest discover -s ps2-research/pc-port/tests -p test_tumbleweed_contract.py -v
```

The raw output uses exclusive creation and refuses paths outside ignored
`.assets/rigid` or `data/rigid-port1`; existing candidates are preserved.
For repeat metadata generation, omit `--native-wire`. The independent R5900
check additionally ran the same tool with the isolated Rabbitizer venv and
`--elf` / `--r5900-probe`. Its ELF mapping delegates to REVALIDATION2's existing
verifier. That mode requires the original ELF and an exact read-only EER export,
kept locally under ignored research data. The normal source-contract mode does
not require Ghidra/Rabbitizer or a running game.

Focused checks: **9/9 PASS**, zero failures/skips on this machine, including
independent synthetic counted-wire round-trip, wrong hash/tag, unknown trailer,
duplicate hull, negative counts, nonfinite values, invalid indices, output
confinement, original-source known answers and deterministic compact output.
The two original-source integration checks require the private canonical corpus;
wire tests require the external read-only Course SDK. Their missing dependencies
produce explicit skips in a corpus-free handoff; no failing source parse is
silently skipped.

## Remaining native gates

`RIGID_COLLISION_RESOURCE = PARTIAL`: original bytes and native wire format are
positively established. The following remain separate requirements before a
private one-object pilot may run:

1. Owned bounded-stream/native reader ABI and correct private prototype lifetime.
2. Native model/resource registration and installed-backend attachment.
3. Safe load/physics-thread admission; D3D8 EndScene is not an admission proof.
4. Reliable body/entity cache invalidation, restart and retirement/destruction.
5. Native body mass/inertia/initial pose and original PC vehicle contact.
6. Rendering from the admitted body's live pose; no updates after destruction.

Yellow checkpoint barrels remain a different owner/collision mechanism. The
tumbleweed's mass/inertia or hull cannot be applied to them merely because both
look movable. The next native capture is defined separately by the lifecycle
agent; no renderer, frozen baseline, native physics source or playable asset was
edited by this source-contract investigation.
