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

## Next isolated probe

The next human test is the fixed `LeftOuterLimit` 58–60 candidate described in
[`runtime-handoff.md`](runtime-handoff.md). It changes only those three
`Marker Pos` values and is prepared to compare baseline and edited
`Race/Car0/LimitState` at the same road section. No result is asserted yet.

## Research output locations

Tracked corpus analyses and findings live under `research/` in the repository.
The RaceLine and LeftInnerLimit candidates used in the completed human tests
were originally copied under the runtime-root directory
`D:\Game\Master Rallye\research-output\g1\probes`; that location is historical.
The current fixed probe tool defaults new artifacts to the branch-local
`<repository>\research-output\g1\probes`. `--output-root <path>` selects and
prints an exact absolute destination inside the repository, keeping generated
research results with the checked-out branch.
