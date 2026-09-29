# France1 split-trigger localization

## Question and confirmed separation

The split Egg has two roles that must stay separate:

| Role | Current representation | Evidence |
|---|---|---|
| Visual split marker | `Egg Name="SplitTimeN"`, `en3d Matrix` Row3 | **CONFIRMED_BY_RUNTIME_EDIT**: moving Row3 moves the yellow sign |
| Split event settings | `gaRaceSplitTimeAI`: Split Time ID, Radius, ExtraTime | ID and Radius are stored; Radius changing the trigger extent is **CONFIRMED_BY_RUNTIME_EDIT**; ExtraTime meaning is **UNKNOWN** |
| Gameplay trigger spatial center/shape | Not yet localized | **UNKNOWN** |

Moving only the SplitTime0 visual Egg moved the sign to StartArea. Driving near
that moved sign did not trigger the split; driving near its old location still
did. Therefore `SplitTime0/en3d Matrix Row3` as the trigger center is
**REJECTED / NOT SUPPORTED**.

## Candidate comparison from the Retail France1 XML

### Candidate 1 — four sibling Egg transforms

For every split ID 0–2, the `SplitTimes` list contains four sibling eggs named
`SplitTimeN-0` through `SplitTimeN-3`, each with its own `en3d Matrix`. Their
Row3 points form a compact repeated group:

| ID | Group center (XYZ) | Center to visual Egg | Corner distances | Radius |
|---:|---|---:|---|---:|
| 0 | `(-2470.510, 84.613, -110.630)` | 0.253 | 20.997–21.052 | 21 |
| 1 | `(-2799.970, -4.473, 563.820)` | 2.426 | 13.005–13.008 | 13 |
| 2 | `(-1644.960, 39.913, 1009.460)` | 1.033 | 12.011–12.056 | 12 |

This repeated geometry and Radius match make the four transforms the strongest
static candidate: **HIGH_CONFIDENCE_INFERENCE, not runtime-confirmed**. Names
and proximity alone do not prove the `gaRaceSplitTimeAI` link. The actual
trigger might use a center, gate, volume, or another representation derived
from this group.

### Candidate 2 — RaceLine samples

The nearest RaceLine samples to visual split positions are index 112, 224, and
336 at 6.181, 4.834, and 0.000 units. The +112 progression repeats across the
three splits, so this is **PLAUSIBLE** spatial/index correlation. There is no
XML reference or controlled edit proving that these RaceLine points drive the
split events. Nearby Cameras markers are farther away (nearest distances
18.546, 17.447, and 24.566); area/limit list markers are farther still.

### Rejected direct visual-transform candidate

The runtime edit moved the sign but left the event at its old location. Direct
Row3 trigger placement is **REJECTED / NOT SUPPORTED**, even though the static
group centroid and RaceLine samples are near the sign.

## One prepared controlled test

The four-point sibling group is the best candidate to test because it repeats
across all three split IDs and its corner distances closely track the known
Radius values. The prepared experiment moves only the four SplitTime0 sibling
Egg transforms near StartArea. It leaves the sign Egg and RaceLine where they
are, separating the candidate group from the other strongest correlation.

The source is the external Retail France1 XML with SHA-256
`beaa2180912ffd54f313a149962e295f9894239014481d2c7ba2db84fb1e08e1`. The
prepared copy and manifest are ignored local artifacts:

- `.research-output/r5t_d0/split0-companion-group-shift/DataScene/RaceTest/France1.xml`
- `.research-output/r5t_d0/split0-companion-group-shift/DataScene/RaceTest/probe-manifest.json`

Only these fields change:

| Egg | Baseline Row3 | Prepared Row3 |
|---|---|---|
| `SplitTime0-0` | `-2490.23 84.51 -117.84 1.00` | `-1684.16 53.76 165.55 1.00` |
| `SplitTime0-1` | `-2463.30 85.53 -130.35 1.00` | `-1657.23 54.78 153.04 1.00` |
| `SplitTime0-2` | `-2450.79 83.09 -103.42 1.00` | `-1644.72 52.34 179.97 1.00` |
| `SplitTime0-3` | `-2477.72 85.32 -90.91 1.00` | `-1671.65 54.57 192.48 1.00` |

All four XYZ positions receive the same translation `(806.07, -30.75, 283.39)`;
Row3 W and each Egg's other matrix rows remain unchanged. The group center moves
from `(-2470.51, 84.6125, -110.63)` to `(-1664.44, 53.8625, 172.76)`, within
0.004 units of the StartArea centroid.

The byte-isolation tool reverses these four Row3 replacements and verifies an
exact restoration of the source XML. It also reparses the edited XML and checks
that the visual SplitTime0 matrix, IDs/radii/ExtraTime, SplitTime1/2 matrices,
RaceLine, and StartArea are unchanged. Source asset bytes were not overwritten.

### Runtime observation plan

Use the prepared France1 XML in a separate Retail test copy. Keep SplitTime0
visual Egg Row3 at `-2470.51 84.36 -110.63 1.00`, ID `0`, Radius `21.00000`,
ExtraTime `77.50000`, SplitTime1/2, RaceLine, StartArea, and FinishArea at
baseline. Confirm the four sibling checkpoint objects may move visually; judge
the event independently from those objects and from the yellow sign.

- If Split Time 0 fires near the moved four-point group and no longer fires at
  the old location, the group is linked to trigger placement. This would not
  yet identify the exact center/shape or which point/derived field is consumed.
- If it remains at the old location, the sibling group is not sufficient; the
  unchanged RaceLine samples or another structure remain candidates.
- If neither location fires, first classify an arming/order/cache/runtime
  problem. That outcome alone does not reject the sibling group.

The edit is **PREPARED_NOT_RUNTIME_TESTED**. No runtime result is claimed.
