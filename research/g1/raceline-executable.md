# Retail RaceLine executable path

## Binary identity

Retail `MRallye.exe`, PE32 x86, preferred base `0x00400000`, SHA-256
`BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4`.

## Consumer and exact list

The `gaRaceLineAI` class string is referenced by constructor `0x0048ACB0`;
factory wrapper `0x0048AD40` creates it. Its vtable begins at `0x00690C80`.
The relevant entries are update `0x0048AE30` and initializer `0x0048B520`.

Both functions go through the scene/list lookup helpers with the exact list
string `RaceLine`. The update's missing-list path references
`***Raceline not found in scene***` at `0x0048AE71`. This establishes that the
RaceTest MarkerList named exactly `RaceLine` is consumed by this class.

## Runtime record and order

The class calculates list count as `(end - begin) / 0x48`; records are stepped
in `0x48`-byte increments. The point read by initializer/update is the float3
at record `+0x38`, `+0x3C`, `+0x40`. This is the executable-backed runtime
`Marker Pos` mapping. The code iterates the supplied list sequence and stores
the selected record ordinal; no sorting or nearest-neighbor construction of a
new list was found in this path. Thus the runtime search consumes source list
order.

The identified path reads the position fields but does not read a Marker Dir
field. It does not establish that no other subsystem ever reads Marker Dir.

## Per-car update

Update `0x0048AE30` resolves each car and reads XYZ at car record
`+0xB0/+0xB4/+0xB8`. It compares this car position with RaceLine record
`+0x38..+0x40` using 3D squared Euclidean distance to choose the nearest
sample. No square root is needed for this nearest-point comparison.

The current `Race/Car%d/LastMarker` value seeds a local search around the prior
ordinal (approximately ±12 records). A periodic per-car full-list scan is also
present. The chosen ordinal is written back to `Race/Car%d/LastMarker`.
Accordingly, within this method `LastMarker` is a cached nearest source-order
sample/cursor; it is not itself proof of a checkpoint event.

The update derives normalized `Race/Car%d/Progress` from the chosen sample
index and a local neighboring-sample distance interpolation. The formula is
not a cumulative arc-length traversal of the whole route. It also sorts the
per-car progress values and writes `Race/Car%d/Rank`; ranking by this progress
value is therefore directly supported by the executable.

Initializer `0x0048B520` computes the ordered adjacent-point distance sum and
publishes `Race/TotalDistance` alongside the per-car RaceLine state. The exact
relationship between that total and every later gameplay consumer was not
followed here.

### Known keys

| Key | Bounded executable role |
|---|---|
| `Race/Car%d/LastMarker` | Per-car cached nearest RaceLine ordinal/search cursor |
| `Race/Car%d/Progress` | Per-car normalized RaceLine sample progress |
| `Race/Car%d/Rank` | Order derived from per-car progress values |
| `Race/TotalDistance` | Ordered adjacent RaceLine distance total initialized by the class |

The reset-manager area also references `Race/Car%d/LastMarker`; the exact
reset/recovery behavior of that shared state is outside this trace. No inspected
RaceLine update edge established AI steering.

## SplitTime relation

The separate `gaRaceSplitTimeAI` initializer at `0x0048CFE0` compares the
already-established split center against RaceLine records using the same
`0x48` stride and `+0x38` float3. It selects a nearest sample and initializes
`Race/SplitTime<ID>/Percentage = nearestRaceLineIndex / RaceLinePointCount`.
Direction of dependency is split center → nearest RaceLine sample/percentage;
RaceLine is not the split trigger source. This agrees with the R5T-D.1 runtime
edit that moved RaceLine[112] without moving the tested trigger.

## Corpus geometry

`raceline-corpus.json` carries exact per-course values and all six pooled/per-
course direction cosine distributions. Across 36 Retail RaceLine lists there
are 12,604 markers with Pos and Dir. Source order is the analysis order; no
closing segment is synthesized. Pooled cosine medians for forward/backward/
central tangent comparisons are close to zero and distributions span nearly
[-1, +1]. Static Marker Dir does not show a single consistent alignment rule.
The identified executable path consumes Pos, not Dir.

## Evidence and unknowns

- Exact list lookup, record stride, position offset, nearest sample, state keys
  and rank/progress computations: `CONFIRMED_BY_EXECUTABLE`.
- Order retention: `CONFIRMED_BY_EXECUTABLE` for this consumer's iteration;
  no list-reordering pass was observed.
- Exact racing-line meaning, AI steering, ranking outside the observed progress
  sort, reset outcome, and full wrap/route behavior: `UNKNOWN`.
- No edited RaceLine runtime probe has been run yet. See
  [`runtime-handoff.md`](runtime-handoff.md).
