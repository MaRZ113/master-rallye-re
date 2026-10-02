# Retail `gaLimitsAI` executable path

## Binary identity

Retail `MRallye.exe`, PE32 x86, preferred base `0x00400000`, SHA-256
`BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4`.

## Class and exact list bindings

Constructor `0x004CD870` references `gaLimitsAI`; the vtable begins at
`0x0069152C`. Per-car update is `0x004CD9B0`; initializer/list lookup is
`0x004CDF00`; nearest-marker helper is `0x004CE140`; the follow-on geometry
classification helper is `0x004CE4F0`.

Initializer `0x004CDF00` looks up these exact MarkerLists and stores their
list pointers in the class instance:

| List name | Instance field |
|---|---:|
| `LeftInnerLimit` | `this + 0x10` |
| `RightInnerLimit` | `this + 0x14` |
| `LeftOuterLimit` | `this + 0x18` |
| `RightOuterLimit` | `this + 0x1C` |

If one of the required lists is absent, the initializer reports the unresolved
limit configuration. Runtime records use the same observed `0x48` stride and
position float3 at `+0x38..+0x40` in the nearest-marker helper.

## Position, direction and geometric classification

For each car, the update passes a car position vector to `0x004CE140`. That
helper minimizes 3D squared distance against the selected marker list, using
all three stored position components. It searches near a cached marker ordinal
and periodically searches the full list. `Marker Dir` is not read in this
examined path.

The update then constructs inner and outer classification tests from the
selected point and adjacent list points. The point/corner coordinates used for
these tests come from marker X/Z; the constructed test-plane Y is derived from
car Y plus the executable float at `0x00691544`, whose raw float value is
`80.0`. The geometry is passed to shared point/region helpers. This confirms
an executable use of the four position lists, but does not justify treating
their XML names as general-purpose road-edge labels.

Bounded sequence observed in `0x004CD9B0`:

1. Test the selected left/right inner-marker geometry.
2. If the point is not classified within the inner region, test the outer
   geometry.
3. Publish per-car `Race/Car%d/LimitState` and emit the available diagnostics.
4. When outside the outer classification, increment an outside counter; the
   observed branch reaches state `2` after eight consecutive samples, while
   earlier samples remain in state `1`.

The debug keys/strings include `Debug/Limits`, `Car inside inner limit %d %d`,
`Car inside outer limit`, `Car outside %f,%f, markers L %d, R %d`, and
`Limits not found`. The state values are the bounded behavior visible in the
identified update, not a full reset policy.

## Reset-manager relationship

`gaVehicleResetManager` has a separate constructor/initializer/update cluster
beginning at `0x004CC2D0`; its state wiring references
`Race/Car%d/LimitState`. `gaLimitsAI` publishes this key, but its update does
not directly invoke the reset manager. The exact consumer conditions and any
subsequent reset/recovery behavior remain `UNKNOWN` in G1.

## Corpus geometry and scope

The exact 36-course counts, per-course RaceLine projections, side signs, and
nearest-progress inner/outer comparisons are in `limits-corpus.json`. Analysis
uses X/Z projection for horizontal corridor comparison and retains distance to
the projected 3D point. Across the corpus, left-named lists occupy a consistent
dominant signed side of source-order RaceLine and right-named lists the opposite
side; at similar progress the outer list is farther in X/Z in about 97.9% of
matched pairs on each side. This is `HIGH_CONFIDENCE_GEOMETRIC_CORRELATION`,
not runtime proof of physical road edges.

The France1 candidate region is unusually controlled: all four limit lists
have constant Y `280.3`, so nearest-marker choice within one list is equivalent
to X/Z nearest choice for that course. Many other course/list pairs have
varying Y, so that simplification must not be generalized.

## Evidence and unknowns

- Exact four list-name lookups and per-car `LimitState` producer:
  `CONFIRMED_BY_EXECUTABLE`.
- Position input and 3D nearest-marker calculation:
  `CONFIRMED_BY_EXECUTABLE`.
- Marker Dir use in this path: no read observed; no gameplay direction meaning
  is asserted.
- Inner/outer classification shape is executable-bounded as above; exact
  downstream response and reset policy remain `UNKNOWN`.
- No Limit XML runtime probe has been run yet. See
  [`runtime-handoff.md`](runtime-handoff.md).
