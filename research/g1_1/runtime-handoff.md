# G1.1 Blender-to-runtime authoring validation handoff

**Status:** prepared; no new human runtime test has been performed in G1.1.
The RaceLine and LeftOuterLimit edits described below have earlier runtime
results as isolated research-probe files. This handoff validates that the
Blender authoring path emits those exact candidate bytes and keeps the fields
isolated.

## Shared baseline and runtime

| Item | Value |
|---|---|
| Course | Retail France1 |
| RaceTest source | `DataScene/RaceTest/France1.xml` |
| Source SHA256 | `BEAA2180912FFD54F313A149962E295F9894239014481D2C7BA2DB84FB1E08E1` |
| Runtime | Retail `MRallye.exe` |
| Runtime SHA256 | `BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4` |
| Blender | 5.2.2, unified `master_rallye_io` add-on |
| Export | New RaceTest XML plus `.mr-race-edit.json`; never overwrite the source |

Use one disposable Retail runtime copy. Restore the hash-verified baseline
between candidate tests. Do not alter DX, GXM, TXT, DXT, HNT, RaceLine when
testing a limit, other limit lists, StartArea, FinishArea, SplitTime, or any
compiled resource. Compare the candidate XML and manifest SHA256 before
installing it. Keep RaceLine and limit tests in separate XML files/runtime
loads.

## Candidate A — RaceLine progression

The already runtime-tested source edit is `RaceLine` markers 265–268 with
source-space delta `(-36.239355, 0, +16.932487)`. The candidate SHA256 is
`F8EE03CCBD03EA4E41F46A66267AD38C3121763E3231222F9D4EF44B4DD97342`.
Move only those four RaceLine point helpers to the resulting world positions
using the standard `(x, y, z) -> (x, -z, y)` source-to-Blender conversion, then
export from the selected Race Logic root.

Expected manifest:

- exactly four changes, all `race.route.raceline.marker_position`;
- indices 265, 266, 267, 268 in RaceLine source order;
- no limit, Marker Dir, topology, or other semantic changes;
- output SHA256 equal to the candidate hash above.

That byte identity means the Blender-authored XML is the same file already
tested by the human RaceLine probe. If loading it again, compare baseline and
candidate `Race/Car0/LastMarker`, `Race/Car0/Progress`, and `Race/Car0/Rank`
through the edited region. Expected prior behavior was a local visible progress
indicator disturbance where the samples were encountered and no obvious AI
steering change in that probe. Do not infer that AI never consumes RaceLine.

## Candidate B — LeftOuterLimit classification

The already runtime-tested source edit is `LeftOuterLimit` markers 58–60 with
source-space delta `(-33.453008, 0, -21.929346)`. The candidate SHA256 is
`A398EDE6934F95146EAB8C81E38DA10B737EFD05E79C9BA0851F96874A0D8911`.
Move only those three LeftOuterLimit point helpers, then export to a different
new XML path.

Expected manifest:

- exactly three changes, all `race.limit.left_outer.marker_position`;
- indices 58, 59, 60;
- no RaceLine, other limit, Marker Dir, or topology changes;
- output SHA256 equal to the candidate hash above.

If this candidate is loaded again, capture a baseline and candidate broker
snapshot at the same physical road section. Prefer:

```text
Physics/Car0/Transform
Race/Car0/LimitState
Race/Car0/LastMarker
Race/Car0/Progress
Race/Car0/RaceState
```

`Physics/Car0/Transform` is the live position source for the comparison.
The earlier state captures had `LastMarker=250`, `Progress=0.55`, and
`LimitState` baseline 1 versus candidate 2; the physics transform differed by
about 4.9 X/Z units. A repeated exact state transition at the same section is
the primary observation. Earlier off-course/recovery onset is a supporting
observation; reset/recovery is not required for the classification result.

## What to report

For each separate candidate, report source and exported hashes, manifest
changed paths/count, runtime EXE hash, whether that exact XML loaded, capture
location/route progress, and the five runtime values above. The earlier
RaceLine and LeftOuterLimit runtime effects are established; a no-change UI
replay does not revoke those results unless the candidate hash and runtime load
are verified. The Right-side lists and LeftInnerLimit remain individually
untested by a runtime boundary edit.
