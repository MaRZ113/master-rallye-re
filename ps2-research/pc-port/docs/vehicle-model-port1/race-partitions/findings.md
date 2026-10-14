# CAR material partitions: source proof and native boundary

Read-only subagent audit on `master`, starting
`a6daf3b17d32043c948e3ed9a843b1a5b3258f16`. No renderer, integration patch,
Course SDK, original PSM/DX or live process was modified. The main agent owns
integration and serial builds.

`partition-evidence.json` retains original resource hashes, PSM node/material
offsets, PC record offsets, exact current-compatible geometry keys, category
multiplicities, source-order runs and attribute residuals. It contains no vertex
arrays, index arrays, textures or original assets.

## Strict source result

All joins below use the original **0.001 model-local source-unit** limit. No
0.005 association or newly increased runtime tolerance is used. Counts are
original PC compiled triangle records, not live draws or independently visible
vehicle parts.

| PC family / source record | Verified root material categories | Unknown faces | Original-index runs |
|---|---|---:|---:|
| Xtrail CAR 1 |195 `carshiny`,14 `carflat`|0|2|
| ChevyBlazer CAR 7 |60 `carshiny`,10 `carglass`|0|3|
| Forester CAR 8 / PS2 WOOLDAND |43 `carshiny`,11 untagged authored-map faces|0|5|
| Forester CAR 9 / PS2 WOOLDAND |43 `carshiny`,28 untagged authored-map faces|0|2|
| Forester CAR 2 / PS2 WOOLDAND |4 `carshiny`|0|1|
| LandCruiser CAR 8 |215 `carshiny`|25|33|
| LandCruiser CAR 9 |373 `carshiny`|104|7|
| Bruno CAR 4 |229 `carshiny` across root.4/root.5|3|5|
| SeatBuggy CAR 7 |165 `carshiny`|4|9|

The source-frame transform is identity, independently supported by the earlier
WATER1/GEOM1/REFL1 and family geometry joins; it was not fitted to these faces.
Each whole-record unsigned float32 position digest is unique to its PC vehicle
family in the bounded **78 original retail DX** files. COMPLETE/CAR repeats
inside the same family occur and require independent race admission.

No newly discovered whole-record `carshiny` classification is warranted for
these mixed sources. Untagged WOOLDAND materials keep authored maps; their
generic mode3 is not the `carshiny` handler's render-target substitution.
PS2 FORESTER remains a distinct asset and is not used as the PC Forester alias.

## First material partition

Xtrail CAR record1 is the simplest source-supported candidate:

```
PC geometry multiset SHA-256
16c3cf75f8d9aa9f4a9d96c36fb0c4f70e1046ea324123b51237158a7c12a19f
244 source vertices / 209 source triangles
    -> root.1 carshiny: source faces 0..194
    -> root.2 carflat: source faces 195..208
```

Only the 195 `carshiny` faces may receive the working Mode4 body contribution.
The 14 `carflat` faces must not receive that contribution. Keeping them Stock is
a bounded reflection-only pilot; faithfully implementing mode1 additionally
needs a tested stage1-disable transaction. Do not call the Stock remainder a
completed PS2 `carflat` port.

ChevyBlazer7 is another verified source candidate. Its source order is18 shiny,
10 glass,42 shiny. Leaving the glass run at Stock preserves its PC behavior;
it does not implement the PS2 `carglass` renderer. A dedicated glass port is
separate from widening this body contribution.

## Source attributes and winding

The PC geometry and all current native attributes should remain unchanged for
the partition pilot. Original PSM source vertices are52 bytes: normal+0,
control+12,color+16,UV+20,XYZW+36. The reader already applies the newest-vertex
ADC/control suppression rule and excludes diagnostic degenerate PS2 triples.

Positions correspond much more closely than some normals/UVs. Xtrail's shiny
subset reaches approximately0.0800 normal-component difference despite matching
positions and UV0. ChevyBlazer's glass UV0 residual reaches1.0212. These facts
are preserved as differences, never repaired by substituting another slot or
copying PS2 normals into the current PC buffer.

`pc_ordered_attribute_sha256` fingerprints **original DX source** indexed XYZ,
normal,raw four color bytes and UV0. It is not claimed to be the live game's
interleaved upload hash: native color conversion/tinting still needs an actual
upload observation before that stronger claim. Material partitioning can keep
all native bytes and only select original IB ranges.

Unsigned face keys allow vertex permutations. They do not change the actual PC
index order, winding,culling,normal orUV. The PSM reader's exact strip winding
and conditional cull choices remain UNKNOWN. Every source duplicate is counted;
contradictory material categories for the same geometry key fail closed.

## Existing native evidence

`runtime-evidence.json` records a bounded read of9 F10 frames from session10348
and3 most recent nonempty20261014 session logs. **No exact digest event for
these nine mixed target records exists in that bounded capture set.**

There is a layout-only ChevyBlazer candidate in frame41028:
`DrawIndexedPrimitive(4,8991,102,20772,70)`,FVF0x152,stride36,original environment
stage1 COLOROP18,TCI65536,COUNT2. LandCruiser240/477-face layout candidates use
the same normal-bearing material pipeline. Those are not source ownership
proofs; numerical VB/IB IDs,count,drawing sequence and shared emitter cannot
activate the feature by themselves.

The source-compatible Xtrail244/209 combination was not found in those frames.
Many4-face matches for the Forester grille shape filter are scenery or other
models,including FVF0x142/0x242. They are explicit false-positive controls.
Those layouts cannot be claimed to be Forester or passed through the existing
FVF0x152/stride36 reflection contract without current geometry evidence.

## Validation and reproduction

Executed:

```
python ps2-research/pc-port/docs/vehicle-model-port1/race-partitions/audit.py
python ps2-research/pc-port/docs/vehicle-model-port1/race-partitions/audit_runtime.py
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/race-partitions -v
python -m compileall -q ps2-research/pc-port/docs/vehicle-model-port1/race-partitions
```

Five focused tests PASS. Fixture/synthetic tests need only this directory and
Python standard library. Audit regeneration needs the existing PS2 PackFS
corpus,protected retail PC vehicles,prior readers and read-only Course SDK.
Runtime regeneration needs the referenced user log files. No runtime mutation,
menu rotation test,post-fix rendering test or new DLL was performed by this
subagent. Native partition implementation remains the main agent's work.

Source result: **CONFIRMED_BY_BYTES**. Algorithmic matching: deterministic
bounded diagnostic. Exact mixed-group current native identity:
**NOT_YET_CONFIRMED_BY_RUNTIME**.
