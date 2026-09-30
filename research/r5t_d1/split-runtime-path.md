# R5T-D.1 `gaRaceSplitTimeAI` executable path

## Exact-build anchor

Retail `MRallye.exe`, SHA-256
`BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4`, PE32
x86, preferred image base `0x00400000`.

The constructor at `0x0048CB50` stores the string `gaRaceSplitTimeAI` and
assigns vtable `0x00690CE4`. The next class table begins at `0x00690CFC`, so
only entries 0–5 below belong to this class.

| Vtable slot | Address | Finding |
|---:|---:|---|
| 0 | `0x0048CC00` | deleting destructor wrapper |
| 1 | `0x0048CBA0` | factory/allocation wrapper |
| 2 | `0x0048D260` | serializes ID, Radius, ExtraTime |
| 3 | `0x0048D340` | loads XML/property ID, Radius, ExtraTime |
| 4 | `0x0048CC50` | proximity/update method |
| 5 | `0x0048CFE0` | split initialization and RaceLine percentage setup |

These functions are virtual targets in the class table; Ghidra does not have
direct-call xrefs for their runtime callers. The method entry addresses and
class table were verified against the exact Retail bytes.

### Resolved call edges and limits

- Factory wrapper `0x0048CBA0` allocates `0x24` bytes and directly calls
  constructor `0x0048CB50`.
- The virtual caller of slots 2–5 was not resolved to a unique callsite. The
  executable has many generic virtual dispatch sites; a live return address
  and stack trace are needed to identify the caller of this component's update
  and initializer.
- Proximity/update `0x0048CC50` calls the engine lookup helpers
  `0x004D8EC0` / `0x004D6FB0` to resolve per-car state and calls
  `0x0048CD20` when the distance condition passes.
- Initializer `0x0048CFE0` follows the same context-derived center, searches
  the RaceLine records, and initializes split state. Its virtual caller is
  unresolved.
- Property loader `0x0048D340` uses typed property readers for the exact
  strings and destination fields documented below. The helper implementations
  are not assigned broader semantics here.

## Slot 4 — proximity/update (`0x0048CC50`)

Entry convention: `ECX=this`; `[ESP+4]` is the context pointer; `RET 4`.

At `0x0048CC5B–0x0048CC68` the method loads `context+0x50`, then copies 12
bytes beginning at `P+0x4C` into a local XYZ. This is the center used by the
proximity arithmetic in this method.

For each index from zero to `this+0x0C - 1`, the method creates the key
`Car%d` and resolves a car record using `FUN_004D8EC0` and `FUN_004D6FB0`. If
the record exists, it follows record `+0x08` and reads the car XYZ at
`+0xB0/+0xB4/+0xB8`. The x87 instructions at `0x0048CCC0–0x0048CCEF` calculate
3D Euclidean distance. `FCOMP [this+0x18]` at `0x0048CCF7`, followed by the
condition-bit test, calls `0x0048CD20` for a finite distance strictly less
than Radius.

This is a 3D spherical proximity region centered on the context-derived XYZ.
For France1 SplitTime0, the main Egg `en3d Matrix` Row3 is now confirmed as
that center by baseline/relocated debugger captures and the final moved
on-road runtime edit.

This method contains no explicit coordinate transform, axis selection, gate
plane test, direction check, or distance-squared shortcut. It performs a
point-distance test every time the update callback runs. Other gating outside
this method has not been ruled out.

### Event recording (`0x0048CD20`)

The event method indexes a byte array at `this+0x10` using the car index. It
returns if that byte is already set; otherwise it sets it before writing split
state. Exact string references include:

- `Race/Car%d/Time`
- `Race/Car%d/SplitPoint`
- `Race/SplitTime%d/Car%d`
- `Race/Countdown/Car%d/TimeToAdd`
- `Race/Countdown/GlobalTimer/TimeToAdd`

`Split Time ID` at `this+0x14` selects the split-state key. ExtraTime at
`this+0x1C` is read in countdown/time-to-add branches. The code establishes
that dataflow, but not the user-facing semantic of ExtraTime.

## Slot 5 — initialization (`0x0048CFE0`)

Entry convention: `ECX=this`; `[ESP+4]` is the context pointer; `RET 4`.
The method follows the same `context+0x50 -> P -> XYZ` chain as slot 4, then
compares that float3 to a sequence of RaceLine points. Each record advances by
`0x48` bytes; the compared float3 begins at record `+0x38`. It finds the
minimum 3D distance and stores:

```text
Race/SplitTime<ID>/Percentage = nearestRaceLineIndex / RaceLinePointCount
```

It also initializes `Race/Car%d/SplitPoint` and per-split/per-car state. Thus
the code's direction is **center to RaceLine-derived percentage**, not
RaceLine point to center. The runtime test moving RaceLine[112] without an
observed trigger relocation is consistent with this.

The exact nearest RaceLine indices produced by the initializer were not
recorded. Earlier static values 112/224/336 were computed from visible-sign
positions and are not executable results. The France1 SplitTime0 runtime
center is now confirmed to equal its Egg Row3 by debugger captures and the
moved-on-road runtime test. SplitTime1/2 share the same XML component structure
but were not independently relocated in runtime tests.

## Slot 3 — XML/property loader (`0x0048D340`)

The loader maps exact property strings to fields:

| Property string | Field |
|---|---:|
| `Split Time ID` | `this+0x14`, integer reader |
| `Radius` | `this+0x18`, float reader |
| `ExtraTime` | `this+0x1C`, float reader |

The instance constructor sets vtable `0x00690CE4`, self-reference `+0x08`,
zeroed count/state fields `+0x0C/+0x10/+0x14`, default Radius `20.0`, and
default ExtraTime `90.0`. The component configuration has no position field in
this loader.

## Evidence boundary

**CONFIRMED_BY_EXECUTABLE:** class string/vtable, XML property-to-offset map,
center pointer reads, XYZ offsets, 3D square-root distance, Radius comparison,
car-position offsets, per-car one-shot state, and center-to-RaceLine
percentage initialization.

For France1 SplitTime0, the source-to-runtime relation is
**CONFIRMED_BY_DEBUGGER** and **CONFIRMED_BY_RUNTIME_EDIT**: the main Egg's
`en3d Matrix` Row3 XYZ matches this center in baseline and relocated debugger
captures, and the final on-road Row3 edit moved the award location. The runtime
type of `context` and `P` remains **UNKNOWN**. SplitTime1/2 use the same
component structure but were not independently moved in these tests.
