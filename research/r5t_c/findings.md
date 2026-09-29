# R5T-C course spatial and tag100 findings

Status: **MORE WORK NEEDED**. The France1 whole-x3 experiment is closed with
two baseline and two modified cold cooks plus a human runtime comparison. The
rigid source edit deterministically changes tag100 but does not move the player
or AI starting arrangement. The actual grid source remains unlocalized. No
course writer, executable patch, or custom layout was added.

## Baseline

- Branch: `research/r5t-course-archaeology`.
- R5T-B.1 closeout baseline: `f110e11` (`research: record R5T-B.1 controlled tag100 proof`).
- Vehicle SDK v1 remains frozen. Course work is read-only except for controlled
  source copies staged under ignored `.research-output` for the original Demo
  9.10 runtime cooker. No course writer or executable patch is present.
- Full synthetic suite at this checkpoint: 137 tests pass. Blender 5.2.2
  headless checks pass for retail Italy1/France1 and the translated source
  helper points.

## R5T-B.1 closeout reproduced

The saved France1 experiment contains three baseline and three one-point
modified cooks. The only source difference is one float32 in `France1.gxm`,
point 0 X from `-987.0555419921875` to `-986.0555419921875` (+1.0). All six DX
files are revision 135 and pass render/index validation. The render prefix
varies naturally across repeated identical inputs, while each cohort's
10,118,248-byte tag100 suffix is byte-identical internally. Baseline SHA-256 is
`9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7`; modified
SHA-256 is `c89654dbf502de96df366d05ecdd87051b0051e8308851550c0e0b6d37c23086`.
The controlled source-to-compiled response is
`CONFIRMED_BY_SOURCE_COMPILED_PAIR`. The owner observed no obvious gameplay
change from the one-corner tracer; this does not establish whole-volume spawn
or trigger semantics.

## Tag100 differential

`src/master_rallye/tag100_diff.py` extracts tag100 only at the exact trailing
boundary returned by the validated course render parser. It refuses a missing
tag, a different payload size, or an unvalidated render prefix. It does not
scan for an integer 100 and does not infer the internal payload boundary.

Across the current retail corpus, all 36/36 revision-135 course DX files pass
render parsing and expose a structurally reached tag100 suffix. Payload sizes
range from 5,634,127 to 10,975,471 bytes. Retail France1 is 10,145,749 bytes;
retail Italy1 is 7,517,509 bytes. The complete repeatable retail scan reported
no parser errors. The small paired Demo 8.4.1 `boinds/track01.dx` is revision
125 and is outside the current course parser's supported revision; it is not
counted as a tag100 parse success.

For the saved France1 one-point source edit:

| Measure | Result |
|---|---:|
| Raw tag100 size in each cohort | 10,118,248 bytes |
| Changed bytes | 452 (0.004467%) |
| Contiguous changed ranges | 253 |
| Unchanged bytes | 10,117,796 |
| Finite aligned float32 candidates touched | 273 |
| Non-finite aligned float32 candidates touched | 3 |
| Unit-normal-like float4 windows | 11 |

The ranges fall into three 64 KiB navigation neighborhoods; those groups do
not imply record boundaries:

| Relative interval | Ranges | Changed bytes |
|---|---:|---:|
| `0x5CA315–0x5CA599` | 16 | 31 |
| `0x5F0045–0x5F64E5` | 178 | 328 |
| `0x86B05C–0x87675E` | 59 | 93 |

The 11 float4 windows have first-three-component lengths within 0.01 of 1.0;
their measured lengths are effectively one at float32 precision. Seven begin at
relative alignment 0 mod 16 and four at 8 mod 16. These are
`HIGH_CONFIDENCE_INFERENCE` plane-like coefficient candidates only. The
alignment sweep also shows overlapping interpretations, so it does not prove a
16-byte record grammar. Exact candidates, deltas, adjacent windows, byte ranges,
and unchanged spans are in
[`tag100-diff-france1-one-point.md`](tag100-diff-france1-one-point.md) and its
JSON companion.

### Candidate plane test against the startpoint box

The eight first source points form the previously measured 10-unit axis-aligned
box. Under the corpus-level source-to-DX hypothesis `(x, z, -y)`, every one of
the 11 candidate float4 windows was tested against all eight box corners for
both `n·x + d = 0` and `n·x = d`.

- For `n·x + d = 0`, each candidate's closest corner residual is between
  15.631578 and 46.130277 source units.
- For `n·x = d`, the closest residual for each candidate is between 50.202269
  and 709.053580 units.
- No corner satisfies either equation within 1e-3.

This does **not** reject plane semantics elsewhere in tag100. It rejects only a
direct equation match between these candidate windows and the eight
startpoint-box corners under the tested transform/conventions. Per-node point
membership is not decoded. The one-corner tracer is not a rigid translation,
so no plane translation law is claimed from that experiment. The exact
per-candidate residual table and source hashes are in
[`startpoint-plane-test.md`](startpoint-plane-test.md) and
[`startpoint-plane-test.json`](startpoint-plane-test.json).

## Whole-volume startpoint candidate

The source patch translated the same X coordinate of all eight first-pool
points by +3.0 source units. Exact source bytes, per-point edits, hashes,
old/new AABBs and centers remain in the ignored
`.research-output/r5t_b1/experiments/france1-startpoint-whole-x3/source-patch.json`.

| Measure | Before | After |
|---|---|---|
| X bounds | `[-987.055542, -977.055542]` | `[-984.055542, -974.055542]` |
| Y bounds | `[-473.666718, -463.666718]` | unchanged |
| Z bounds | `[48.539051, 58.539051]` | unchanged |
| Center in source coordinates | `(-982.055542, -468.666718, 53.539051)` | `(-979.055542, -468.666718, 53.539051)` |
| Maximum pairwise-distance change | — | `0.0` |

Exactly eight float32 fields are targeted; 12 actual byte positions differ due
to their encoded values. Both saved source manifests contain 106 source files
and 160 staged files. Independent manifest comparison finds only
`france1.gxm` changed between cohorts; the paired TXT, all other source files,
the runtime executable and RaceTest XML match. The source node binding remains
`HIGH_CONFIDENCE_INFERENCE`, not proven index membership.

The mapped old center is 1.558779 units from Demo 9.10 `Cameras/Marker 0`; the
candidate +3 X shift leaves that marker inside the translated 10-unit box.
Both runtime clones use the same RaceTest XML SHA-256
`6048ed26c78118f3f82d9ddbcaf4f75c6655b24d805189d3cf3bd772202dc0df`.

All four snapshots exist and pass the course render parser. Each baseline
repeat has a different render-prefix hash, as do the two modified repeats. The
10,118,248-byte tag100 suffix is byte-identical within each cohort and differs
between cohorts:

| Cohort | Run tag100 SHA-256 |
|---|---|
| Baseline 01/02 | `9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7` |
| Modified 01/02 | `e4129f5019491e26973064c72c13776b9aa5bd2379d8190270c3a70215291e06` |

The rigid +3 translation changes 263 bytes in 142 ranges (0.002599%). It
confirms `GXM source edit -> deterministic tag100 change` as
`CONFIRMED_BY_SOURCE_COMPILED_PAIR`. The comparison report and hashes are in
[`whole-x3-closeout.md`](whole-x3-closeout.md) and its JSON companion.

The owner reports that the modified course loaded and ran normally in Demo
9.10, with no observed change from baseline to modified in player position or
orientation, AI positions/order, countdown, or race start. No obvious delayed
trigger or spatial boundary appeared while driving roughly half the lap.
Therefore direct grid-anchor behavior is **NOT SUPPORTED** by this runtime
test. A containment/helper role remains **POSSIBLE** because the +3 boxes still
overlap by 7 units and `Cameras/Marker 0` remains inside the modified box.
This is negative evidence for the tested movement, not proof that the node has
no runtime role. The unchanged formation within Demo 9.10 does not show that
the observed participant order is authored by the old course source.

### Whole-x3 differential and plane test

The one-point and whole-x3 experiments have byte-identical baseline tag100
payloads. All 263 whole-x3 changed byte offsets are a subset of the one-point
experiment's 452 changed offsets, and the final modified byte values match at
all 263 positions. The one-point deformation adds 189 changed byte positions
outside that set. This common pattern is structural correlation only; it does
not identify tag100 records or their consumers.

The whole-x3 diff has six unit-normal-like float4 candidate windows. Under the
source-to-DX transform `(x, z, -y)`, the rigid source +3 X translation is DX
`(+3, 0, 0)`. The candidate normals move by at most `2.5e-5`, but the observed
fourth-component deltas fit neither `d' = d - n·t` nor `d' = d + n·t` within
0.01. No candidate passes either plane-translation test. They remain
plane-like windows only; no face-plane or physical-collision interpretation is
supported.

### Start-region geometry versus participant order

New owner-reported cross-runtime controls change the prior interpretation of
the old France1 order. With three opponents, the player was consistently at
the front in the 8.4.1 runtime, second in the 9.3.1 runtime, and in the normal
retail order in Retail. In a critical control, both completed R5T-C course
output sets derived from old 8.4.1 source were copied into the Retail game;
both showed the ordinary Retail France1 order. This means old 8.4.1
participant order does not follow merely from the source course origin. The
observations strongly suggest runtime/version-specific participant-to-slot
assignment accounts for at least part of the visible order. This does not
establish that physical slot positions or start-region geometry are
runtime-only.

Keep two questions separate:

- **Physical slots/start region:** source and exact representation remain
  **UNKNOWN**. RaceTest `MarkerLists/StartArea` is a source-backed candidate
  for start-region geometry, but no runtime binding to car positions is known.
- **Participant order:** **HIGH_CONFIDENCE_INFERENCE** that runtime/version
  affects which participant occupies a visible slot, based on the cross-runtime
  observations and Retail portability control. Exact assignment logic is not
  decoded.

The earlier statement that old 8.4 France1 preserved a source-authored unusual
grid through a 9.10 cook is therefore withdrawn as a source-semantic claim.
The Demo 9.10 whole-x3 comparison only established that its own baseline and
modified runs looked the same.

### Start-grid source candidates

The local full-build corpus contains RaceTest XML for all four builds. Its
`MarkerLists/StartArea` has four marker positions; those coordinates are
identical in Demo 8.4.1, 9.3.1 and 9.10.0, while retail has small coordinate
changes. The 9.10 experiment XML hash matches the Demo 9.10 corpus. In the
later XML, `Cameras` contains Marker 0 at `(-982.10, 52.20, 467.87)`, 1.559
units from the old GXM `startpoint` candidate center and hundreds of units from
the four `StartArea` markers. This makes `StartArea` a candidate for physical
start-region geometry, but its runtime meaning is **UNKNOWN** and it has not
been bound to car slot locations.

The `startpoint` mesh record is present in old France1 TXT (ordinal 1,
`Index 0 / Size 12`) and Demo 9.3.1 TXT, but absent from Demo 9.10.0 and retail
TXT. Its first eight pool points are still only a high-confidence geometric
candidate; exact node-to-pool membership is unproven. Current evidence does
not localize physical slot geometry to this box, the XML markers, or a specific
compiled tag100 record.

The available evidence does not identify which course structure defines the
physical slots or start region. Runtime-version-dependent participant order
can explain why old ordering does not travel with the old-source cook into
Retail, but does not explain or locate the slot geometry.

### Stronger non-overlap test candidate

A further rigid `source X += 12.0` translation would move the candidate AABB
from `[-987.055542, -977.055542]` to `[-975.055542, -965.055542]`, leaving a
2-unit gap from its original X interval. Demo 9.10 `Cameras/Marker 0` would be
outside the new AABB by 7.044458 units. No other point in the bounded GXM
float3 pool lies inside that translated AABB; the nearest is 1.300377 units
away and 33 points are within 3 units. The opposite -12 direction places one
other pool point inside, so +12 is the cleaner geometric separation. This
probe is justified for testing containment of the candidate helper, but it is
lower priority for finding the actual car grid than a direct `StartArea` XML
probe. It has not been staged or cooked.

## Source `$bsp` oracle

No safe isolated `$bsp` edit is prepared. The only complete small developer
GXM/TXT/DX source pair, Demo 8.4.1 `boinds/track01`, contains `Surface $landdb`
and `$boinds` but no `$bsp`; its cooked DX is revision 125 and cannot be parsed
by the current revision-135 course reader. `gordonTrack`, `RussiaTurkey1`, and
`collisiontests/crack*` have source GXM files but no matching TXT/DX pair in the
local developer corpus. France1 has a large `$bsp` subtree, but its source
point-pool membership by node is still unknown. Therefore `$bsp` to tag100 is
still `UNKNOWN`, not rejected.

## Render-sort BSP versus tag100

The cooker log's `moSortPlane`, draw-plane and render-sort messages remain
evidence for render processing only. The controlled repeats show naturally
variable render prefixes while tag100 is stable for identical source and
deterministically different for both the one-point and rigid whole-x3 source
edits. This supports treating the validated render prefix and trailing tag100
region as separate data regions. It does not establish that tag100 is physical
collision, a trigger structure, or a tree, nor explain why its bytes changed.

## Blender

Blender 5.2.2 passed the existing retail Italy1/France1 course smoke: both
render meshes, draw/source identity attributes, course collection placement,
and all 172/172 DXT material images loaded. The translated old-source
startpoint overlay also passed with eight point-only empties under Course
Helpers; no edges/faces or behavior were inferred. Demo 9.10 France1 RaceTest
XML also imports as a read-only 583-marker overlay with no marker issues. No
tag100 diagnostic geometry was added because the float4 candidates do not pass
a source-plane equation or translation test.

## Closeout artifacts and checks

- [`whole-x3-closeout.md`](whole-x3-closeout.md) / [`whole-x3-closeout.json`](whole-x3-closeout.json)
- `python -m unittest discover -s tests\synthetic -v`: **137 tests pass**.
- Blender 5.2.2 R5T-A Italy1/France1 import, R5T-B France1 XML overlay and
  R5T-B.1 GXM point overlay smoke checks all pass.

## Next controlled source probe

Use an XML-only test in a fresh Retail runtime clone. Start from one of the
old-source cook outputs already observed to load in Retail, edit only the
active Retail `DataScene/RaceTest/France1.xml`, and add +3.0 to the X component
of all four `MarkerLists/StartArea/Marker Pos` values. Keep the runtime, course
output, opponents, and all other XML fields fixed. No cook is needed. Record
car positions and participant order separately from green marker visuals.

| Marker No | Retail Marker Pos | Candidate Marker Pos |
|---:|---|---|
| 0 | `-1649.71 52.42 174.33` | `-1646.71 52.42 174.33` |
| 1 | `-1658.30 53.26 160.72` | `-1655.30 53.26 160.72` |
| 2 | `-1678.49 55.13 171.13` | `-1675.49 55.13 171.13` |
| 3 | `-1671.25 54.64 184.87` | `-1668.25 54.64 184.87` |

If car slot positions move by +3 in X, the list influences physical placement.
If only green marker visuals move, this list is not a direct vehicle-slot
anchor. If nothing observable moves, the relationship remains unproven; then
consider the GXM +12 containment probe. Within-runtime comparison avoids
confusing source geometry effects with the already observed version-dependent
participant ordering.

A clean small source/cooked `$bsp` pair remains unavailable. Physical meaning
of tag100 remains unknown. No course writer, tag100 decoder, custom layout, or
executable patch was added.
