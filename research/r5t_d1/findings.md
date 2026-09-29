# R5T-D.1 findings — split trigger center trace

## Scope and executable identity

This is a read-only trace of `gaRaceSplitTimeAI` in the supported Retail
executable. The exact file used by the Ghidra program path
`D:\Game\Master Rallye\MRallye.exe` hashes to
`BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4`.
It is PE32 x86 with preferred image base `0x00400000`. Analysis used a cloned
Ghidra project; the original executable and original Ghidra project were not
modified.

## Verified class and methods

`FUN_0048CB50` stores the string `gaRaceSplitTimeAI`, writes vtable pointer
`0x00690CE4`, and initializes a `0x24`-byte instance. The six consecutive
vtable entries are:

| Slot | Entry | Observed role |
|---:|---:|---|
| 0 | `0x0048CC00` | deleting destructor wrapper |
| 1 | `0x0048CBA0` | allocation/factory wrapper; allocates `0x24` bytes and calls the constructor |
| 2 | `0x0048D260` | serializes the three named fields |
| 3 | `0x0048D340` | reads the three named XML/property fields |
| 4 | `0x0048CC50` | runtime proximity/update method |
| 5 | `0x0048CFE0` | initialization and nearest-RaceLine correlation |

The next observed class vtable begins at `0x00690CFC`; its constructor names
`gaRaceStartCountdownAI`. Entries beyond slot 5 are not part of the split AI
vtable.

All class methods use `ECX` as `this`. At `0x0048CC50` and `0x0048CFE0`, the
first stack argument is at entry `[ESP+4]` and the function returns with
`RET 4`. At `0x0048D340`, there are two stack arguments and `RET 8`. Ghidra's
saved function signatures remain untyped; these conventions are read from the
Retail instructions and their stack cleanup.

| Field | Instance offset | Executable evidence |
|---|---:|---|
| Split Time ID | `+0x14` | `0x0048D340` passes the exact string `Split Time ID` and this address to the integer reader |
| Radius | `+0x18` | exact string `Radius` and this address passed to the float reader; `0x0048CC50` compares against this value |
| ExtraTime | `+0x1C` | exact string `ExtraTime` and this address passed to the float reader; event code later reads it |
| car-count / loop bound | `+0x0C` | read by update/init methods; populated during initialization |
| per-car one-shot bytes | pointer at `+0x10` | initialized by `0x0048CFE0`; `0x0048CD20` checks and sets one byte per car |

The constructor defaults ID to `0`, Radius to `20.0`, and ExtraTime to `90.0`.
France1's XML values override these defaults.

The factory wrapper `0x0048CBA0` directly allocates the instance and calls the
constructor. The update method `0x0048CC50` resolves per-car records through
`0x004D8EC0` / `0x004D6FB0` and calls event recorder `0x0048CD20` when its
distance test passes. The initializer is a separate virtual target. No unique
runtime virtual-dispatch caller was resolved for slots 2–5; this remains a
debugger follow-up, not a missing target-address verification.

## Runtime position path

Both the update method (`0x0048CC50`) and initializer (`0x0048CFE0`) follow the
same external pointer chain:

```text
this                         gaRaceSplitTimeAI instance
context = [entry ESP + 0x04]  opaque runtime argument
P = [context + 0x50]          opaque spatial-data object
center = float3(P + 0x4C)      XYZ offsets +0x4C, +0x50, +0x54
```

The class itself has no position field in its constructor or XML/property
loader. The executable confirms the context-to-XYZ chain, but does not identify
the runtime type of `context` or `P`, the producer of `P`'s coordinates, or the
source asset field that populates them. `0x0048CFE0` also clears bit 0 in an
unidentified field at `P+0x70`; that is a structural clue only, not an
assigned semantic.

### Proximity calculation

`0x0048CC50` copies the three center floats, loops over indices below
`this+0x0C`, resolves a `Car%d` record through engine lookup helpers, then reads
the resolved car object's position at `+0xB0`, `+0xB4`, and `+0xB8`. For each
resolved car, the method computes:

```text
sqrt((center.x-car.x)^2 + (center.y-car.y)^2 + (center.z-car.z)^2)
```

and calls `0x0048CD20` when that result is less than the float at `this+0x18`.
The normal finite-float comparison is strict `<`, in 3D, with an explicit
square root. There is no transform or crossing/heading test in this method;
the compared values are read directly and must already be in a common
coordinate space. Additional scheduling conditions outside this method are
not characterized here. A missing `Car%d` record skips that car. The event
method uses the per-car byte array to avoid recording the same split repeatedly.

The user's Radius `21 -> 100` runtime edit makes the event trigger earlier,
independently confirming that the named Radius field affects the spatial
extent (`CONFIRMED_BY_RUNTIME_EDIT`).

## Initialization and RaceLine direction

`0x0048CFE0` reads the same center chain, scans the RaceLine records (stride
`0x48`; compared float3 begins at record `+0x38`), chooses the nearest point by
3D distance, and writes `Race/SplitTime<ID>/Percentage` as
`nearestIndex / RaceLinePointCount`. It then initializes per-car split state.

This directly supports the dependency direction:

```text
runtime split center -> nearest RaceLine sample -> stored split percentage
```

It does not support `RaceLine[n] -> gameplay trigger center`. The user's move
of `RaceLine[112]` without an observed trigger movement is consistent with
that result. The static France1 indices 112/224/336 were computed from visual
sign positions; because the actual center is still unknown, those exact runtime
indices have not been reproduced from the initializer.

## Runtime evidence kept separate

- Main `SplitTime0` Egg `en3d Matrix Row3` moves the yellow visual sign but not
  the gameplay event: sign role **CONFIRMED_BY_RUNTIME_EDIT**; Row3 as trigger
  center **REJECTED / NOT_SUPPORTED**.
- The `SplitTime0-0..3` visible checkpoint objects move when their transforms
  are edited, but the event stays at its old location: visual role
  **CONFIRMED_BY_RUNTIME_EDIT**; their transforms as trigger center
  **NOT_SUPPORTED**.
- Moving `RaceLine[112]` did not visibly move the event:
  **NOT_SUPPORTED** as the direct trigger-position source.
- Radius affects the event extent: **CONFIRMED_BY_RUNTIME_EDIT**.
- The gameplay center's runtime storage chain is
  **CONFIRMED_BY_EXECUTABLE**; its owner type and producer/source field remain
  **UNKNOWN**.
- `ExtraTime` is read by the event path and contributes to writes to
  `Race/Countdown/.../TimeToAdd` in particular state/difficulty branches.
  Its gameplay meaning remains **UNKNOWN**; this dataflow alone does not assign
  a time-bonus or penalty interpretation.

The earlier R5T-D.0 four-sibling transform candidate is superseded for
SplitTime0 by the runtime result above; SplitTime1/2 sibling positions were not
independently tested. The four edited SplitTime0 transforms are not supported
as that event's direct trigger-position source.
The earlier prepared transform edit is historical preparation, not the next
recommended experiment. See `split-center-trace.md` for the single debugger
handoff and the unresolved source boundary.

## Status

**R5T-D.1: MORE WORK NEEDED.** The executable's proximity algorithm and the
runtime XYZ pointer chain are established. No supported XML/data field has yet
been found to move those XYZ values, so no controlled data edit is prepared.
The next useful action is one read-only debugger capture at the proximity
method to record the SplitTime0 center, context/object pointers, and virtual
caller's stack.

No Blender code, course data, XML, executable, or Ghidra original project was
modified. No writer was added.

## Verification

Commands run:

- `Get-FileHash -Algorithm SHA256 'D:\Game\Master Rallye\MRallye.exe'` —
  matched the executable hash above.
- `python -m unittest discover -s tests\synthetic -v` — **144 tests passed**.
- `python -m json.tool research/r5t_d1/split-runtime-fields.json` — valid JSON.
- `git diff --check` and `git diff --cached --check` — clean.

No XML or executable bytes were edited, so this phase has no source-data
byte-diff count. Reported binary addresses are preferred VAs for the exact
executable hash above; structure offsets are in-memory offsets.
