# R5T-D.1 split center — final runtime closeout

## Source-to-runtime trace

The validated France1 SplitTime0 path is:

```text
France1 RaceTest XML
  -> EggLists_Version4 / SplitTimes / Egg Name="SplitTime0"
  -> en3d Matrix Row3 XYZ
  -> XML Egg parsing and AI_List factory path
  -> gaRaceSplitTimeAI instance
       Split Time ID at +0x14
       Radius at +0x18
       ExtraTime at +0x1C
  -> runtime callback argument `context`
  -> [context + 0x50] = P
  -> float3 at [P + 0x4C, +0x50, +0x54] == Egg Row3 XYZ
  -> 3D spherical proximity test against car XYZ
```

**R5T-D.1: PASS.** The source-to-runtime relation is confirmed for France1
SplitTime0 by baseline and relocated debugger captures and a final moved-on-road
runtime edit. The runtime type of `P` remains unknown. SplitTime1/2 share the
same XML component structure but were not independently moved in runtime tests.

The Retail XML parser dispatches `EggLists_Version4` through `0x0052ECD0` and
the list/Egg parsing path (`0x0053AD60` / `0x0053AE50`). The Egg parser reads
the `en3d Matrix` and its `AI_List`; the AI factory registry is queried by
component name. The `gaRaceSplitTimeAI` property loader at `0x0048D340` maps ID,
Radius, and ExtraTime; it has no position property. The source-to-center
relationship for France1 SplitTime0 is established by matching baseline and
relocated debugger values plus a separate moved-on-road runtime test. The
runtime type of `P` remains unknown.

The evidence progression corrected the original negative interpretation:

1. Baseline debugger: SplitTime0 Row3 exactly matched runtime P XYZ.
2. StartArea-relocated debugger: SplitTime0 Row3 and P XYZ again matched. The
   sphere overlapped the grid, and all four cars were accepted during startup;
   per-car one-shot guards made later driving appear not to trigger it.
3. Final nearby on-road Row3 edit: SplitTime0 was awarded at the moved location
   before the normal split. This is the decisive causal runtime confirmation.
4. Moving `SplitTime0-0..3` moved those visual objects but did not define the
   gameplay center; moving `RaceLine[112]` did not visibly move the event.

The main Egg transform is therefore the source; the sibling objects and
RaceLine direct-position hypothesis remain separate and unsupported for
SplitTime0.

## France1 SplitTime0 debugger and runtime observations

| State | Egg Row3 XYZ | Runtime center / result | Evidence |
|---|---|---|---|
| Baseline Retail XML | `(-2470.51, 84.36, -110.63)` | `P+0x4C/+0x50/+0x54` = `(-2470.51, 84.36, -110.63)` | **CONFIRMED_BY_DEBUGGER** |
| StartArea-relocated XML | approximately `(-1664.44, 53.86, 172.76)` | P center matched `(-1664.44, 53.86, 172.76)` | **CONFIRMED_BY_DEBUGGER** |
| Final nearby on-road edit | `(-2415.42, 72.10, -124.94)` | SplitTime0 was awarded at this moved position before its ordinary location | **CONFIRMED_BY_RUNTIME_EDIT** |

In the baseline capture, `P = 0x1A0C3550` for that run and `P+0x58` contained
`1.0`. Heap and guard addresses vary between runs; only the field offsets and
observed values above are relevant. The final on-road edit held Radius `21`,
Split Time ID `0`, ExtraTime `77.5`, RaceLine, StartArea, FinishArea, and the
sibling visuals at baseline.

### Why the StartArea probe first appeared negative

At the one-shot acceptance path near `0x0048CD44`, the debugger stopped exactly
four times during loading/startup for SplitTime0. `EDI` identified cars 0, 1,
2, and 3. Each had a separate guard byte at the following run-specific
addresses:

| Car | Guard byte address in observed run |
|---:|---:|
| 0 | `0x1A0961C0` |
| 1 | `0x1A0961C1` |
| 2 | `0x1A0961C2` |
| 3 | `0x1A0961C3` |

The relocated sphere overlapped StartArea, so all four cars had already
activated SplitTime0 during startup. Their per-car one-shot guards prevented a
second activation when the tester later drove around the moved sign. This
supersedes the earlier interpretation that the sign moved while the gameplay
center stayed at the original location.

## Canonical read model and boundaries

- SplitTime0 Egg Row3 XYZ is both the yellow sign position and gameplay center:
  **CONFIRMED_BY_DEBUGGER**, **CONFIRMED_BY_RUNTIME_EDIT**, and
  **CONFIRMED_BY_EXECUTABLE**.
- Radius is the 3D spherical proximity threshold, with strict `distance <
  Radius` for finite values: **CONFIRMED_BY_RUNTIME_EDIT** and
  **CONFIRMED_BY_EXECUTABLE**.
- Split Time ID at `this+0x14` identifies/selects split event state:
  **CONFIRMED_BY_EXECUTABLE**, **SUPPORTED_BY_DEBUGGER**.
- `SplitTime0-0..3` are separate visual checkpoint objects; their transforms
  are **NOT_SUPPORTED** as SplitTime0's direct center. SplitTime1/2 sibling
  transforms were not independently tested.
- RaceLine[112] is **NOT_SUPPORTED** as the direct center. The initializer
  derives nearest RaceLine percentage from the already-existing split center.
- ExtraTime semantics remain **UNKNOWN**.
- Runtime type of `P` remains **UNKNOWN** even though its SplitTime0 XYZ source
  is confirmed.

No further runtime test or data edit is pending for R5T-D.1.
