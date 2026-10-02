# G1 isolated Retail France1 runtime probes

**Status:** prepared and hash-verified; neither candidate has been run in a
game runtime. These are two separate tests. Do not combine the XML files.

## Shared baseline

| Item | Value |
|---|---|
| Runtime build | Retail |
| Expected runtime EXE SHA256 | `BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4` |
| Source RaceTest XML | `DataScene/RaceTest/France1.xml` |
| Source XML SHA256 | `BEAA2180912FFD54F313A149962E295F9894239014481D2C7BA2DB84FB1E08E1` |
| Candidate directory | `D:\Game\Master Rallye\research-output\g1\probes` (ignored research output) |

Use a disposable Retail runtime copy and install exactly one candidate as that
copy's `DataScene/RaceTest/France1.xml`. Keep a hash-verified baseline XML copy
to restore between runs. Do not modify DX, GXM, TXT, DXT, HNT, RaceLine-adjacent
lists, StartArea, FinishArea, SplitTime, or any other resource.

The preparation/verification tool is deliberately limited to the two fixed
recipes:

```powershell
python tools\g1_route_limit_probe.py inspect --source "<baseline France1.xml>"
python tools\g1_route_limit_probe.py verify --kind raceline --source "<baseline France1.xml>" --edited "<RaceLine candidate>"
python tools\g1_route_limit_probe.py verify --kind limit --source "<baseline France1.xml>" --edited "<Limit candidate>"
```

It checks the exact baseline hash and verifies that only the predeclared
`Marker Pos` `Value` attributes changed.

## Probe A — RaceLine Pos

| Item | Value |
|---|---|
| Edited XML | `D:\Game\Master Rallye\research-output\g1\probes\France1_raceline_265-268.xml` |
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

| Item | Value |
|---|---|
| Edited XML | `D:\Game\Master Rallye\research-output\g1\probes\France1_leftinner_98-100.xml` |
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

## Handoff discipline

- Run baseline and candidate in the same Retail executable/runtime copy.
- Run only one candidate per test and restore the baseline before switching
  from RaceLine to LeftInnerLimit.
- Record the loaded XML SHA256 and all changed resource files.
- These are prepared tests only. No G1 runtime result is asserted here.
