# France1 whole-x3 source and runtime closeout

Status: **2+2 cook PASS; source isolation PASS; grid-source question OPEN.** The
source edit and output comparisons are read-only research. No course writer or
EXE patch was added. The full machine-readable record is
[`whole-x3-closeout.json`](whole-x3-closeout.json).

> Later R5T-D.0 evidence supersedes this report's open grid-source question:
> Retail XML edits confirm `MarkerLists/StartArea` drives the physical grid
> frame and headings. This does not change the controlled R5T-C result that
> moving the GXM candidate changed tag100 without moving the grid. Exact
> per-car interpolation remains unknown. See `research/r5t_d0/findings.md`.

## Source isolation and repeated cooks

The source was Demo 8.4.1 `France1.gxm`, 11,489,135 bytes. Its SHA-256 changed
from
`56ebbf03fe681d730e796a40d455562b5f9976d794c710e73d5c9be32e4e86b2` to
`333ed57f9f9f4cbb56c30780face7ba38888fcca0002420197169948da6da56f`. The only
edit was `source X += 3.0` at the first eight float3 pool points. Their float32
field starts are `0xA56183`, `0xA5618F`, `0xA5619B`, `0xA561A7`, `0xA561B3`,
`0xA561BF`, `0xA561CB`, and `0xA561D7`. Twelve bytes changed at
`0xA56184`, `0xA56190-0xA56191`, `0xA5619C`, `0xA561A8-0xA561A9`,
`0xA561B4`, `0xA561C0-0xA561C1`, `0xA561CC`, and `0xA561D8-0xA561D9`.
The 158,889-byte TXT remained
identical at SHA-256
`71ea372203bcc6e84bfee87e7d2f410e22c1fdcdc5f653c87274100df38c0d43`. Both
source and staged manifests independently identify only `france1.gxm` as a
cross-cohort difference. The two runtime copies use the same executable and
the same 334,577-byte RaceTest XML at SHA-256
`6048ed26c78118f3f82d9ddbcaf4f75c6655b24d805189d3cf3bd772202dc0df`.

All four snapshots exist and parse through the course render parser. The
render prefixes differ between repeat cooks in both cohorts; only the exact
tag100 suffix is stable within a cohort.

| Run | DX bytes | DX SHA-256 | tag100 offset | tag100 SHA-256 |
|---|---:|---|---:|---|
| baseline-01 | 14,828,157 | `37def5987b6eb6d52d0a9747ae2085caefc05bf3013cf4e342fcb991b74c2a84` | 4,709,909 | `9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7` |
| baseline-02 | 14,802,266 | `f1e48b6e8ac5ade0217d903deb9def24e60bed7fbae892173325868d36d0ab2e` | 4,684,018 | same |
| modified-01 | 14,797,526 | `56bf08adcdd7b30d60e79117089fe90319799980117ac625408b009cb518ebc6` | 4,679,278 | `e4129f5019491e26973064c72c13776b9aa5bd2379d8190270c3a70215291e06` |
| modified-02 | 14,771,934 | `44bf1ba8fe2629755dc765fcf11d0a7e210d33e00db33fab15da9d01835e71d7` | 4,653,686 | same |

The baseline and modified tag100 payloads are each 10,118,248 bytes. Baseline
repeats are byte-identical; modified repeats are byte-identical; the cohorts
differ. The saved pre-cook staging validator says `PASS_STAGED`. Its validator
cannot be rerun against the completed runtime folders because it requires the
generated DX/DXT cache to be absent; the completed snapshots were preserved.
The variance-aware comparison was rerun successfully with:

```powershell
python tools\r5t_b1_course_cook.py compare --experiment france1-startpoint-whole-x3 --minimum-runs 2
```

It reports 3,532 unchanged fields, 5 stable modified fields, 22 variable
modified fields, and two stable compiled effects. The stable compiled effects
are the trailing-section and tag100 hashes; render-prefix variation remains
nondeterministic cooker output.

## Stable tag100 differential

The rigid +3 translation changes **263 bytes in 142 ranges**, or **0.002599%**
of tag100. This confirms the causal source-to-compiled relation as
`CONFIRMED_BY_SOURCE_COMPILED_PAIR`. Relative offsets below are from the
validated tag100 start; range ends are exclusive.

| Relative interval | Ranges | Changed bytes |
|---|---:|---:|
| `0x5CA315–0x5CA599` | 16 | 31 |
| `0x5F0045–0x5F64E5` | 96 | 182 |
| `0x86B05C–0x8702BE` | 30 | 50 |

The baseline tag100 bytes also match the earlier one-point `+1 X` experiment
exactly. All 263 whole-x3 changed byte offsets are among the one-point
experiment's 452 changed offsets, and all 263 modified byte values are exactly
the same at those offsets. The one-point deformation adds 189 changed byte
positions. This is a repeatable structural comparison, not a decoded record
or semantic relationship.

The whole-x3 parser found 152 finite aligned float32 candidates, three
non-finite candidates, and six changed float4 windows whose first three
components remain unit length. A scan of all byte alignments touching changed
bytes found no float32 delta of `+3` or `-3`. Changed-byte alignment is spread
across byte positions; no fixed record stride, coordinate array, AABB, sphere,
matrix, index table, or parent/ancestor bounds have been established.

### Plane-like candidate translation test

The known source-to-DX map sends source `(+3,0,0)` to DX `(+3,0,0)`. For each of
the six affected unit-normal-like windows, the candidate normal changes by at
most `2.5e-5`. The fourth-component deltas fit neither `d' = d - n·t` nor
`d' = d + n·t` within 0.01.

| tag100 offset | actual Δd | error for `n·x+d=0` | error for `n·x=d` |
|---:|---:|---:|---:|
| `0x86B070` | -0.006317 | 0.103824 | -0.116458 |
| `0x86B1C0` | -0.022568 | -0.602410 | 0.557274 |
| `0x8702B0` | 0.013092 | 0.200681 | -0.174497 |
| `0x86B1F8` | -0.013046 | -0.629600 | 0.603507 |
| `0x86DDB8` | 0.008087 | -0.348844 | 0.365018 |
| `0x870278` | -0.001747 | -0.202567 | 0.199073 |

No candidate passes the translation law. These remain plane-like candidate
windows only. The test rejects the proposed translation behavior for these six
windows; it does not reject every possible plane representation in tag100.

## Runtime controls and physical start-region question

The owner reports a normal course load and race start. In the Demo 9.10
baseline/modified comparison, player position and orientation, AI positions
and ordering, countdown, and race start showed no observed change. No obvious
delayed trigger or physical boundary appeared while driving roughly half the
course. Thus:

- GXM startpoint candidate → tag100 change: **CONFIRMED_BY_SOURCE_COMPILED_PAIR**.
- GXM startpoint candidate → direct grid anchor: **NOT SUPPORTED** by this test.
- GXM startpoint candidate → containment/spatial helper: **POSSIBLE**; the +3
  boxes still overlap by 7 units and the marker remains inside.
- tag100 → physical collision, and `$bsp` → tag100: **UNKNOWN**.

### Cross-runtime participant-order control

The owner subsequently compared France1 with three opponents across runtimes.
The player was consistently placed at the front in 8.4.1, second in 9.3.1,
and in the normal retail order in Retail. In a critical control, both completed
R5T-C course output sets derived from the old 8.4.1 source were copied into the
Retail game; both showed the ordinary Retail France1 order. Therefore the old
8.4.1 player order does not follow merely from the source course origin.

This is **CONFIRMED_BY_RUNTIME** for the reported observations and a
**HIGH_CONFIDENCE_INFERENCE** that runtime/version-specific participant-to-slot
assignment explains at least part of the visible order. The exact file list
copied into Retail was not supplied, so this does not identify whether a
specific DX, XML, or other resource controls assignment. The result does not
prove that physical slot locations are runtime-only and does not prove that no
course start-region data exists. The prior statement that old 8.4 participant
ordering survived a 9.10 cook as source-authored semantics is withdrawn. The
Demo 9.10 +3 comparison remains a valid within-runtime negative result: that
edit did not observably change its baseline car positions/order.

### Physical start-region candidates

The full local corpus contains France1 RaceTest XML for all four builds.
`MarkerLists/StartArea` contains four markers, identical in Demo 8.4.1, 9.3.1
and 9.10.0; Retail has small coordinate changes. The Demo 9.10 experiment XML
hash matches its local corpus. In later XML, `Cameras` has Marker 0 at
`(-982.10, 52.20, 467.87)`, 1.559 units from the old GXM `startpoint`
candidate center. `StartArea` markers are hundreds of units away. Thus the
GXM box is camera-marker-adjacent, while `StartArea` is a candidate for
physical start-region geometry. Neither is bound to vehicle slot positions.
Physical slot geometry remains **UNKNOWN / NOT LOCALIZED**.

The old France1 `startpoint` TXT node is ordinal 1 (`Index 0 / Size 12`) and is
also present in Demo 9.3.1 TXT, but absent from Demo 9.10.0 and retail TXT. Its
first eight GXM pool points form the candidate box only as a high-confidence
geometric inference; exact node-to-pool membership is unproven. Current
observations do not link this box, the XML markers, or a tag100 record to
physical car slots.

## Next controlled source probe

Use an XML-only test in a fresh Retail runtime clone. Start from one of the
old-source cook outputs already observed to load in Retail. Edit only the
active Retail `DataScene/RaceTest/France1.xml`: add +3.0 to X for the four
`MarkerLists/StartArea/Marker Pos` values. Hold runtime, course output,
opponents, and all other XML fields fixed; no cook is needed. Record vehicle
slot positions and participant order separately from the green marker visuals.

| Marker No | Retail Marker Pos | Candidate Marker Pos |
|---:|---|---|
| 0 | `-1649.71 52.42 174.33` | `-1646.71 52.42 174.33` |
| 1 | `-1658.30 53.26 160.72` | `-1655.30 53.26 160.72` |
| 2 | `-1678.49 55.13 171.13` | `-1675.49 55.13 171.13` |
| 3 | `-1671.25 54.64 184.87` | `-1668.25 54.64 184.87` |

If physical car slots move by +3 in X, the list influences placement. If only
green marker visuals move, this list is not a direct vehicle-slot anchor. If
nothing observable moves, its relationship remains unproven; then consider
the geometrically separated GXM +12 containment probe. Keeping the runtime
fixed avoids conflating physical geometry with version-dependent participant
ordering.

The GXM +12 test remains justified for containment but lower priority for
finding physical slot geometry. It would move the candidate AABB to
`[-975.055542, -965.055542]`, leave a 2-unit gap from its original X interval,
and place Demo 9.10 Cameras Marker 0 outside by 7.044458 units. No other
bounded GXM point lies inside the new AABB; the nearest is 1.300377 units away
and 33 points are within 3 units. This edit has not been staged or cooked.

No clean small `$bsp` source/cooked pair was found: old France1 and Italy1 are
large `$bsp` examples; small Boinds has no `$bsp`. Therefore `$bsp -> tag100`
remains **UNKNOWN**.

## Validation run for this closeout

The full synthetic suite passed: `python -m unittest discover -s tests\synthetic -v`
reported **137 tests, OK**. The variance-aware cook comparison passed with:

```powershell
python tools\r5t_b1_course_cook.py compare --experiment france1-startpoint-whole-x3 --minimum-runs 2
```

Blender 5.2.2 headless checks passed for Retail Italy1/France1 course import,
Demo 9.10 France1 RaceTest XML overlay (583 markers, zero issues), and Demo
8.4.1 France1's eight point-only GXM candidates. Successful commands used
`--factory-startup` to avoid loading the user's installed addon before the
repository addon:

```powershell
& 'D:\Game\Master Rallye\_reverse-tools\blender-5.2.2-windows-x64\blender.exe' -b --factory-startup --python tests\blender\r5t_a_course_smoke.py -- inputs\retail_Italy1\track01.dx inputs\retail_France1\france1.dx .research-output\r5t_c\r5t_a_course_smoke.json
& 'D:\Game\Master Rallye\_reverse-tools\blender-5.2.2-windows-x64\blender.exe' -b --factory-startup --python tests\blender\r5t_b_xml_smoke.py -- inputs\9.10.0_France1\france1.dx 'D:\Game\Master Rallye\corpora\demo-9.10.0\DataScene\RaceTest\France1.xml' .research-output\r5t_c\r5t_b_xml_smoke.json
& 'D:\Game\Master Rallye\_reverse-tools\blender-5.2.2-windows-x64\blender.exe' -b --factory-startup --python tests\blender\r5t_b1_gxm_helper_smoke.py -- inputs\8.4.1_France1\France1.gxm .research-output\r5t_c\r5t_b1_gxm_helper_smoke.json
```

Derived Blender smoke results are under ignored `.research-output/r5t_c/`.
No new parser or analyzer code was added, so no test fixture changes were
needed.
