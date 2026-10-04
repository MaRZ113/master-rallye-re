# G1 runtime results

Human-observed outcomes for the two isolated France1 RaceTest probes. The
candidate files are research-only and do not expand the stable G0/G0.1 writer.

## RaceLine Pos — progression effect confirmed

**Probe:** `RaceLine` markers 265–268, each translated by `(-36.239355, 0,
+16.932487)` in X/Y/Z. The road/render geometry was unchanged. Candidate SHA256:
`F8EE03CCBD03EA4E41F46A66267AD38C3121763E3231222F9D4EF44B4DD97342`.

**Human observation:** as the player passed the edited region, the progress
indicator visibly jerked/changed locally. Outside that region behavior remained
normal. No obvious AI driving/steering change was noticed in this probe.

**Status:** `RaceLine Marker Pos -> runtime race progression` is
`CONFIRMED_BY_RUNTIME_EDIT`. The observed local progress-bar disturbance
matches the executable path through nearest/current sample, `LastMarker`,
`Progress`, and `Rank`. This does not prove RaceLine is the sole ranking input
or that it defines AI steering. AI result:
`NO_OBSERVABLE_AI_STEERING_CHANGE_IN_THIS_PROBE`.

Practical authoring note for a future explicit phase: source order and sample
positions matter. Retail median spacing is about 20 world units, with course
variation; this is a corpus observation, not a format constant. A bounded
authoring tool should resample a route at approximately uniform spacing rather
than treating arbitrary sparse control points as final samples. `Marker Dir`
runtime role remains `UNKNOWN`. Readiness classification:
`READY_FOR_BOUNDED_AUTHORING` in a later explicit phase; RaceLine remains
read-only in the stable writer.

## LeftInnerLimit Pos — inconclusive

**Probe:** `LeftInnerLimit` markers 98–100, translated toward the route by
`(-5.855248, 0, +19.123705)`. Candidate SHA256:
`05F112004E04FB398C25BCDED572F342ACF2B616BDFE040CBFE2BA0F75816700`.

**Human observation:** no clearly visible player behavior change and no obvious
AI behavior change.

**Status:** `INCONCLUSIVE_RUNTIME_PROBE`. This is not a failed or negative
semantic test: the executable classifies inner/outer states into `LimitState`,
and a transition between those states may have no obvious visual response. The
executable evidence that four exact limit lists feed `gaLimitsAI`, and that
`gaVehicleResetManager` consumes `LimitState`, remains unchanged. Reset behavior
is not established by this observation.

## LeftOuterLimit Pos — local LimitState change observed

**Probe:** `LeftOuterLimit` markers 58–60, translated by
`(-33.453008, 0, -21.929346)` in source X/Y/Z (40 units in X/Z). Candidate XML
SHA256: `A398EDE6934F95146EAB8C81E38DA10B737EFD05E79C9BA0851F96874A0D8911`.
The only authored fields were those three `Marker Pos` values; RaceLine, the
other limit lists, course geometry, and race logic stayed at baseline.

**Human-observed runtime state comparison:** at the corresponding local route
section, both runs reported `LastMarker=250` and `Progress=0.55`. The baseline
reported `LimitState=1`; the candidate reported `LimitState=2`. The player
physics positions captured from `Physics/Car0/Transform` were approximately
`(-2428.03, 669.75)` and `(-2432.76, 671.07)` in X/Z for baseline and candidate,
respectively. Their horizontal separation is about 4.9 units, so this is a
same-section comparison rather than a bit-identical world-position comparison.
The candidate entered OFF COURSE/reset earlier; the baseline could travel
farther before equivalent recovery. `Race/Car0/Transform` was not a reliable
live-position observable in these tests. `RaceState` did not discriminate the runs;
`Resetting` was too transient to use as a stable comparison. `ResetNo` and
`ResetBeingPrinted` were supporting observations within each session only;
their absolute values are not comparable across separate sessions.

**Status:** `LeftOuterLimit Marker Pos -> local LimitState classification` is
`CONFIRMED_BY_RUNTIME_STATE_DIFF`. Earlier observed off-course/recovery onset
is `CONFIRMED_BY_RUNTIME_EDIT` for this candidate and setup. A reset is not
required to claim the classification result, and the probe does not establish a
universal meaning for LimitState values or the full reset policy.

The current authoring implementation now exposes only those pre-existing
`Marker Pos` XYZ attributes on RaceLine and the four literal limit lists. The
separate Blender-to-runtime authoring handoff is in
[`research/g1_1/runtime-handoff.md`](../g1_1/runtime-handoff.md); no additional
human test is claimed here.

## Research output locations

Tracked reports and evidence notes live under `research/` in the Course
worktree. The candidates used for the earlier human G1 tests were staged at
`D:\Game\Master Rallye\research-output\g1\probes`; that location is historical
and is not the Course branch's default output folder. New Course probe output
defaults to
`D:\Game\Master Rallye\master-rallye-re-course\research-output\g1\probes`.
The probe tool prints the resolved absolute output root, candidate XML, and
manifest paths. `--output-root <path>` can select another location inside the
active Course worktree. The sibling general/AI worktree has its own independent
`research-output` directory.
