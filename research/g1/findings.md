# G1 — RaceLine, course limits and Cameras: current findings

## Scope and executable

Static executable observations below were made against Retail `MRallye.exe`,
SHA-256 `BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4`.
The exact file at `corpora/retail/MRallye.exe` was re-hashed before corpus
analysis. This section records static evidence; human runtime edit results are
listed separately in [`runtime-results.md`](runtime-results.md).

## Current result

- **RaceLine:** `CONFIRMED_BY_EXECUTABLE` as an ordered per-car nearest-marker,
  progress and rank input. A human-tested local edit to markers 265–268 caused
  a localized progress-indicator disturbance at the edited region, upgrading
  `Marker Pos -> runtime race progression` to `CONFIRMED_BY_RUNTIME_EDIT`.
  No obvious AI steering change was observed in that probe; this does not prove
  RaceLine is unused by AI globally. No `Marker Dir` read was found in the
  identified update/init path, so its runtime role remains `UNKNOWN`.
- **Four limit lists:** `CONFIRMED_BY_EXECUTABLE` as the exact input lists to
  `gaLimitsAI`, which publishes per-car `LimitState` classifications. Their
  literal names are not being promoted to runtime boundary names beyond the
  list lookup. The fixed `LeftOuterLimit[58..60]` runtime comparison changed
  `LimitState` from 1 to 2 at the same route sample/progress; an earlier
  recovery onset was also observed. `LeftInnerLimit[98..100]` remains
  `INCONCLUSIVE_RUNTIME_PROBE`. No direct edit was run against either
  right-side list. Reset consequences beyond the observed local recovery onset
  remain unresolved.
- **Cameras:** the executable has `gaCameraManagerParams` camera parameter
  accessors, but the RaceTest `MarkerLists/Cameras` to camera-parameter link was
  not established. Its XML `Pos` and `Dir` are only structurally preserved and
  visualized read-only.
- **Blender:** RaceLine and the four limit lists are displayed in literal
  source order with individual marker helpers and a source-order polyline.
  Their bounded G1.1 workflow authors only existing `Marker Pos` values;
  topology and `Marker Dir` remain read-only. Cameras remain read-only.
  Marker Dir previews/rays are diagnostic only; rays are opt-in.
- **Authoring:** the G0/G0.1 fields remain supported. G1.1 adds only the
  existing position fields on RaceLine and the four literal limit lists; it
  does not add list/marker topology, direction, or Camera editing.

**G1 status:** `PASS` — RaceLine progression and LeftOuterLimit state-change
runtime results close the G1 evidence gate. **G1.1 status:** implementation is
`READY_FOR_ROUTE_AUTHORING_RUNTIME_TEST`; the tested source probes are now exposed by
the bounded Blender XML authoring path, but a human test of that UI/export
workflow remains separate from the earlier probe-file tests.

## Retail marker corpus

The curated corpus has 36 principal courses. The machine reports are generated
from their exact RaceTest XML files and carry the Retail EXE hash above:

- [`marker-corpus.json`](marker-corpus.json) and
  [`marker-corpus.md`](marker-corpus.md) contain list inventory and RaceLine
  geometry.
- [`raceline-corpus.json`](raceline-corpus.json) contains per-course
  source-order lengths, spacing, closure ratios, duplicate counts, turns and
  six Marker Dir/tangent cosine distributions.
- [`limits-corpus.json`](limits-corpus.json) contains all per-course
  RaceLine-projection, side-sign and inner/outer progress comparisons.
- [`gxm-raceline-correlation.json`](gxm-raceline-correlation.json) records the
  two paired Demo 8.4.1 source GXM comparisons.

All six lists occur once in 36/36 courses; all listed markers have `Marker Pos`,
`Marker Dir`, and one additional `Marker Type` field. Count ranges (min / median
/ max) are:

| List | Total | Per-course count |
|---|---:|---:|
| RaceLine | 12,604 | 136 / 355 / 470 |
| LeftInnerLimit | 7,582 | 107 / 212 / 336 |
| LeftOuterLimit | 6,519 | 85 / 181.5 / 323 |
| RightInnerLimit | 7,533 | 130 / 210 / 335 |
| RightOuterLimit | 6,442 | 97 / 188 / 323 |
| Cameras | 2,975 | 56 / 79.5 / 127 |

Across RaceLine, the source-order X/Z polyline has 36-course median length
7,653.55, median per-course marker spacing 20.08, 3 consecutive duplicate
segments total, and 390 turns over 45 degrees. First-to-last/length ratios
range from 0.0212 to 0.5893 (median 0.3891); therefore no closing edge is
invented in Blender. Pooled Marker Dir alignment cosines are broadly distributed
for forward, backward and central tangents in both 3D and X/Z. This static
distribution does not support a simple universal tangent interpretation, and
the executable path does not read Marker Dir.

Across all courses, LeftInner/LeftOuter side signs are on one dominant
source-order side for all 36 courses (mean per-course dominance about 99.2%);
RightInner/RightOuter have the opposite dominant sign for all 36 (about
99.1–99.2%). When pairing nearest inner/outer markers by approximate RaceLine
progress within 0.0125, the outer marker is farther in X/Z for 97.9% of 7,455
left-side pairs and 97.9% of 7,415 right-side pairs. This is
`HIGH_CONFIDENCE_GEOMETRIC_CORRELATION`, not runtime proof of road edges or
their consequences.

`gaLimitsAI` uses a 3D nearest-marker helper. For the France1 probe all four
limit lists have a constant Y value of 280.3, so the nearest-marker ordering
within each list is equivalent to X/Z ordering for that course. This is not
true of every course/list in the 36-course corpus; per-course Y uniqueness is
retained in `marker-corpus.json`.

## Source GXM comparison

Demo 8.4.1 France1 `_raceline` has 954 triangles/954 used position indices;
Italy1 `raceline` has 690 triangles/692 used position indices. After the
established source-GXM-to-runtime axis mapping, their X/Z points are often near
RaceTest RaceLine segments (France1 median 0.831, 93.9% within 5; Italy1 median
8.047, 96.7% within 20). Their vertical bounds are distinctly offset from the
RaceTest list bounds. This is only a static spatial relation. The resources
remain distinct; the name and proximity do not prove shared runtime semantics.

## Probe readiness

The fixed RaceLine and LeftInnerLimit France1 probes were human-tested:

- RaceLine indices 265–268: localized progress-bar disturbance observed;
  `CONFIRMED_BY_RUNTIME_EDIT` for RaceLine position influence on progression.
- LeftInnerLimit indices 98–100: no clear visible effect; retained as
  `INCONCLUSIVE_RUNTIME_PROBE`, not a failed or negative test.

The isolated LeftOuterLimit markers 58–60 probe completed with a runtime state
change. The runtime and state-capture results are in
[`runtime-handoff.md`](runtime-handoff.md) and
[`runtime-results.md`](runtime-results.md). The probe result supports local
`LimitState` sensitivity to that edited boundary; it does not assign road-edge
semantics to all four list names or prove a general reset policy.

## G1.1 bounded authoring

The shared source-preserving RaceTest editor can now change only `Marker Pos`
XYZ for existing markers in exactly `RaceLine`, `LeftInnerLimit`,
`LeftOuterLimit`, `RightInnerLimit`, and `RightOuterLimit`. The writer refuses
ambiguous/missing lists and preserves every marker's identity, ordinal,
`Marker Dir`, unknown fields, and all other XML bytes. Blender keeps source
order explicit, updates each diagnostic polyline when a point moves, and shows
per-marker index/approximate progress and neighboring gaps. Stable Marker Dir,
Cameras, and all non-listed marker families remain outside the exporter.

`Marker Pos` authoring is ready for one human Blender-to-runtime validation.
RaceLine and the LeftOuterLimit source mutations already have separate runtime
evidence; this next check validates the new authoring interaction and exported
artifact path rather than reopening their established consumer results. See
[`research/g1_1/findings.md`](../g1_1/findings.md) and
[`research/g1_1/runtime-handoff.md`](../g1_1/runtime-handoff.md).

## Evidence boundaries

- Runtime-confirmed G0/G0.1 behavior is unchanged and remains documented in
  `research/g0` and `docs/course-race-logic-authoring.md`.
- RaceLine position influence on visible local race progress has a human
  runtime edit result. The exact output of each individual internal field
  remains based on the executable trace unless explicitly captured.
- LeftInnerLimit has one inconclusive runtime probe. LeftOuterLimit[58..60]
  has one state-diff and earlier-recovery observation. The other three list
  families have no individual human boundary-mutation test. Limit-state
  dataflow and reset-manager consumption are executable findings; broad reset
  behavior is not confirmed by gameplay.
- The RaceLine-to-GXM spatial match is not a source/compiler/runtime link.
- Limit name-based interpretation, AI steering, recovery, camera-list binding,
  and downstream reset behavior remain unresolved.
- Only bounded `Marker Pos` XYZ on the five G1 lists is now added to the
  RaceTest XML authoring surface. No marker topology, `Marker Dir`, Camera, or
  course binary writer was changed.
