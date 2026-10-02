# G1 — RaceLine, course limits and Cameras: current findings

## Scope and executable

Static executable observations below were made against Retail `MRallye.exe`,
SHA-256 `BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4`.
The exact file at `corpora/retail/MRallye.exe` was re-hashed before corpus
analysis. This is not runtime evidence for any G1 route or limit behavior.

## Current result

- **RaceLine:** `CONFIRMED_BY_EXECUTABLE` as an ordered per-car nearest-marker,
  progress and rank input. `Marker Pos` is consumed; no `Marker Dir` read was
  found in the identified RaceLine update/init path. AI steering and broad
  route meaning remain `UNKNOWN`.
- **Four limit lists:** `CONFIRMED_BY_EXECUTABLE` as the exact input lists to
  `gaLimitsAI`, which publishes per-car `LimitState` classifications. Their
  literal names are not being promoted to runtime boundary names beyond the
  list lookup. Reset consequences remain unresolved.
- **Cameras:** the executable has `gaCameraManagerParams` camera parameter
  accessors, but the RaceTest `MarkerLists/Cameras` to camera-parameter link was
  not established. Its XML `Pos` and `Dir` are only structurally preserved and
  visualized read-only.
- **Blender:** RaceLine and the four limit lists are displayed in literal
  source order with individual read-only helpers. Cameras receive position
  helpers. Marker Dir previews/rays are diagnostic only; rays are opt-in.
- **Authoring:** G0's StartArea/FinishArea/SplitTime allowlist was not expanded.
  All new G1 lists remain read-only.

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

Two fixed, hash-guarded France1 probe candidates were prepared under the
ignored `research-output/g1/probes` directory:

- RaceLine indices 265–268, to compare per-car `LastMarker`, `Progress` and
  `Rank` while render/physical course geometry remains fixed.
- LeftInnerLimit indices 98–100, to compare the executable's `LimitState`
  classification around the translated inner-list segment while the other
  three limit lists remain fixed.

Exact hashes, old/new values and observation instructions are in
[`runtime-handoff.md`](runtime-handoff.md). Neither candidate has been run in a
game runtime. No route/limit/camera authoring is enabled.

## Evidence boundaries

- Runtime-confirmed G0/G0.1 behavior is unchanged and remains documented in
  `research/g0` and `docs/course-race-logic-authoring.md`.
- RaceLine `LastMarker`/`Progress`/`Rank` and limit `LimitState` dataflow are
  executable findings, not a human test of edited XML.
- The RaceLine-to-GXM spatial match is not a source/compiler/runtime link.
- Limit name-based interpretation, AI steering, recovery, camera-list binding,
  and downstream reset behavior remain unresolved.
- No G1 list was added to the stable XML writer. No course binary writer was
  changed.
