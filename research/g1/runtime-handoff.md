# G1 Retail France1 runtime probe record

**Status:** RaceLine progression probe passed; LeftInnerLimit probe was
inconclusive; one isolated LeftOuterLimit candidate is prepared and awaiting a
human runtime test. Never combine the candidate XML files.

## Shared baseline

| Item | Value |
|---|---|
| Runtime build | Retail |
| Expected runtime EXE SHA256 | `BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4` |
| Source RaceTest XML | `DataScene/RaceTest/France1.xml` |
| Source XML SHA256 | `BEAA2180912FFD54F313A149962E295F9894239014481D2C7BA2DB84FB1E08E1` |
| RaceLine / LeftInner legacy candidates | `D:\Game\Master Rallye\master-rallye-re\research-output\g1\probes` (repository-local ignored output) |
| New probe default output | `D:\Game\Master Rallye\research-output\g1\probes` (runtime-root untracked output) |

Use a disposable Retail runtime copy and install exactly one candidate as that
copy's `DataScene/RaceTest/France1.xml`. Keep a hash-verified baseline XML copy
to restore between runs. For the outstanding OuterLimit test, do not modify
DX, GXM, TXT, DXT, HNT, RaceLine, other limit lists, StartArea, FinishArea,
SplitTime, or any other resource. The probe tool prints the resolved output
root, candidate XML and manifest paths after each command. `--output-root`
overrides the runtime-root default without changing it.

The preparation/verification tool is deliberately limited to three fixed
recipes (RaceLine, LeftInnerLimit, and LeftOuterLimit):

```powershell
python tools\g1_route_limit_probe.py inspect --source "<baseline France1.xml>"
python tools\g1_route_limit_probe.py prepare-outerlimit --source "<baseline France1.xml>"
python tools\g1_route_limit_probe.py verify --kind raceline --source "<baseline France1.xml>" --edited "<RaceLine candidate>"
python tools\g1_route_limit_probe.py verify --kind limit --source "<baseline France1.xml>" --edited "<LeftInnerLimit candidate>"
python tools\g1_route_limit_probe.py verify --kind outerlimit --source "<baseline France1.xml>" --edited "D:\Game\Master Rallye\research-output\g1\probes\France1_outerlimit_58-60.xml"
```

It checks the exact baseline hash and verifies that only the predeclared
`Marker Pos` `Value` attributes changed.

## Probe A — RaceLine Pos

**Runtime status:** `CONFIRMED_BY_RUNTIME_EDIT` for RaceLine Marker Pos
influence on race progression. At indices 265–268 the progress indicator
visibly jerked/changed locally as the player passed the edited region; outside
that region behavior remained normal. No obvious AI steering change was
observed in this probe. This does not establish that RaceLine is unused by AI.

| Item | Value |
|---|---|
| Edited XML | `D:\Game\Master Rallye\master-rallye-re\research-output\g1\probes\France1_raceline_265-268.xml` |
| Edited XML SHA256 | `F8EE03CCBD03EA4E41F46A66267AD38C3121763E3231222F9D4EF44B4DD97342` |
| Exact list | `MarkerLists/List[@Name='RaceLine']` |
| Field | `Marker Pos` X/Z only; Y is unchanged |
| Zero-based marker indices | 265, 266, 267, 268 |
| Shared delta | `(-36.239355, 0, +16.932487)`; 40.0 units in X/Z |

| Index | Baseline XYZ | Candidate XYZ |
|---:|---|---|
| 265 | `(-2433.70, -18.10, 909.55)` | `(-2469.939355, -18.10, 926.482487)` |
| 266 | `(-2426.12, -18.34, 928.55)` | `(-2462.359355, -18.34, 945.482487)` |
| 267 | `(-2419.14, -18.34, 946.63)` | `(-2455.379355, -18.34, 963.562487)` |
| 268 | `(-2409.33, -18.34, 964.44)` | `(-2445.569355, -18.34, 981.372487)` |

These four consecutive samples lie on a low-turn section around normalized
source-order progress 0.593–0.600. Physical/render road geometry is unchanged.

### What to capture

Use the same car count/opponent setup for baseline and candidate. Compare the
per-car runtime values `Race/Car%d/LastMarker`, `Race/Car%d/Progress`, and
`Race/Car%d/Rank` as cars approach and pass the affected section. The identified
Retail updater is `0x0048AE30`; its RaceLine instance uses `this + 0x2C` for the
car count and resolves the exact `RaceLine` list during update. If using a
debugger, record the candidate XML hash and the observed per-car values on both
sides of the edited region. A meaningful observation is a localized change in
sample/progress/rank data while the visible/physical road remains unchanged.

Do not treat participant steering or a visible trajectory change as required
for this probe; neither is established by the current executable trace. If
those three resource values do not change, record that result without
concluding that RaceLine is unused; first confirm the runtime loaded this exact
XML candidate and inspect the runtime list count/positions.

## Probe B — LeftInnerLimit Pos

**Runtime status:** `INCONCLUSIVE_RUNTIME_PROBE`. Markers 98–100 were edited as
prepared, but the human tester saw no clearly visible player behavior change
and no obvious AI behavior change. This is not a failed/negative result:
`gaLimitsAI` produces `LimitState`, and the tested inner-to-between classification
may not have a visible response.

| Item | Value |
|---|---|
| Edited XML | `D:\Game\Master Rallye\master-rallye-re\research-output\g1\probes\France1_leftinner_98-100.xml` |
| Edited XML SHA256 | `05F112004E04FB398C25BCDED572F342ACF2B616BDFE040CBFE2BA0F75816700` |
| Exact list | `MarkerLists/List[@Name='LeftInnerLimit']` |
| Field | `Marker Pos` X/Z only; Y is unchanged |
| Zero-based marker indices | 98, 99, 100 |
| Shared delta | `(-5.855248, 0, +19.123705)`; 20.0 units toward the nearby RaceLine segment in X/Z |

| Index | Baseline XYZ | Candidate XYZ | X/Z distance to RaceLine before → after |
|---:|---|---|---:|
| 98 | `(-2380.94, 280.30, 945.47)` | `(-2386.795248, 280.30, 964.593705)` | 34.020 → 17.680 |
| 99 | `(-2354.25, 280.30, 961.16)` | `(-2360.105248, 280.30, 980.283705)` | 27.827 → 10.829 |
| 100 | `(-2311.86, 280.30, 956.46)` | `(-2317.715248, 280.30, 975.583705)` | 31.104 → 11.324 |

Baseline points map approximately to RaceLine progress 0.599–0.611 by nearest
source-order X/Z segment. All France1 limit lists have constant Y `280.3`; the
executable's per-list 3D nearest-marker choice therefore has the same marker
ordering as X/Z for this France1 probe. Do not extrapolate this simplification
to every Retail list.

### What to capture

Keep all other three limit lists unchanged. Compare baseline and candidate at
the road section around source-order progress 0.60, including the old and
translated left-inner segments. Capture `Race/Car%d/LimitState`; the executable
update is `0x004CD9B0`, and `gaLimitsAI` publishes that state after inner/outer
classification. If `Debug/Limits` is available in the runtime setup, preserve
its exact diagnostic output too. Do not infer a reset from a state transition:
the downstream reset policy has not been established.

The discriminating result is whether the classification boundary follows the
modified LeftInnerLimit segment locally while RightInnerLimit, both outer
lists, RaceLine, and the visible course remain unchanged. Record exact car,
position/section, state before/after, XML hash, and whether the runtime reports
an inner/outer/outside diagnostic. The current evidence does not predict a
universal numerical state transition for every sampled point.

## Probe C — LeftOuterLimit Pos (awaiting runtime test)

This is the only outstanding G1.1a runtime probe. It edits the outer list alone
near a clear France1 road section. It does not alter RaceLine, either inner
list, RightOuterLimit, road/render geometry, or race logic.

| Item | Value |
|---|---|
| Exact XML source | `D:\Game\Master Rallye\Data.sma_unpacked\DataScene\RaceTest\France1.xml` |
| Source SHA256 | `BEAA2180912FFD54F313A149962E295F9894239014481D2C7BA2DB84FB1E08E1` |
| Expected runtime | Retail `MRallye.exe`; SHA256 `BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4` |
| Candidate XML | `D:\Game\Master Rallye\research-output\g1\probes\France1_outerlimit_58-60.xml` |
| Candidate SHA256 | `A398EDE6934F95146EAB8C81E38DA10B737EFD05E79C9BA0851F96874A0D8911` |
| Probe manifest | `D:\Game\Master Rallye\research-output\g1\probes\France1_outerlimit_58-60.xml.manifest.json` |
| Baseline reference manifest | `D:\Game\Master Rallye\research-output\g1\probes\France1_retail_baseline.manifest.json` |
| Exact list/field | `MarkerLists/List[@Name='LeftOuterLimit']`, `Marker Pos` XYZ; Y remains unchanged |
| Zero-based indices | 58, 59, 60 |
| Shared displacement | `(-33.453008, 0, -21.929346)` in source X/Y/Z; 40 units in X/Z toward the nearby route |

| Index | Baseline XYZ | Candidate XYZ | X/Z distance to nearby RaceLine before → after |
|---:|---|---|---:|
| 58 | `(-2424.16, 280.30, 670.24)` | `(-2457.613008, 280.300000, 648.310654)` | 47.545 → 12.328 |
| 59 | `(-2457.06, 280.30, 710.67)` | `(-2490.513008, 280.300000, 688.740654)` | 32.809 → 6.104 |
| 60 | `(-2455.33, 280.30, 723.22)` | `(-2488.783008, 280.300000, 701.290654)` | 43.120 → 4.209 |

The candidate compresses this local outer-list segment toward the normal
drivable trajectory. Compare baseline and candidate at the same physical road
position. The primary observation is `Race/Car0/LimitState` (also capture
states 1 and 2 if available) and any `Debug/Limits` output. The executable
shows state 1 during an outside-outer counter and state 2 after eight
consecutive outside samples; do not require recovery/reset behavior for a
positive result. Record the baseline state at the same road position rather
than assuming a universal baseline value. If the candidate position is outside
the edited outer classification, the expected state is 1 during the counter,
then 2 after eight consecutive outside samples; otherwise the change may not
reach a visible state transition.

Competing outcomes:

- **H1 — local outer-boundary classification follows the edit:** the same car
  position near the changed samples produces a changed LimitState or
  outside-outer classification in the candidate compared with baseline.
- **H2 — this local road trajectory does not reach the tested classification:**
  the exact candidate is loaded, but no state transition is observed.
- **H3 — other dependencies dominate:** state/diagnostic behavior is
  inconsistent or differs outside the edited region; record exact conditions
  without assigning a cause.

The first LeftInnerLimit test remains `INCONCLUSIVE_RUNTIME_PROBE`; do not treat
this outer test as a retry with the same edit. It changes a different exact
list and is designed to move the outer boundary across/near a drivable line.

## Handoff discipline

- Run baseline and candidate in the same Retail executable/runtime copy.
- Run only one candidate per test and restore the baseline before changing the
  installed XML.
- Record the loaded XML SHA256 and all changed resource files.
- Record candidate hash, current `Race/Car0/LimitState`, car position/section,
  and `Debug/Limits` output. Do not modify any other resource.
