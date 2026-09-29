# R5T-D.1 split center — source boundary and next capture

## Source-to-runtime trace

The static trace currently reaches these steps:

```text
France1 RaceTest XML
  -> EggLists_Version4 / SplitTimes records
  -> XML Egg parsing and AI_List factory path
  -> gaRaceSplitTimeAI instance
       Split Time ID at +0x14
       Radius at +0x18
       ExtraTime at +0x1C
  -> runtime callback argument `context`
  -> [context + 0x50] = P
  -> float3 at [P + 0x4C, +0x50, +0x54]
  -> 3D proximity test against car XYZ
```

The Retail XML parser dispatches `EggLists_Version4` through `0x0052ECD0` and
the list/Egg parsing path (`0x0053AD60` / `0x0053AE50`). The Egg parser reads
the `en3d Matrix` and its `AI_List`; the AI factory registry is queried by
component name. The `gaRaceSplitTimeAI` property loader at `0x0048D340` only
maps ID, Radius, and ExtraTime. This establishes how the component's named
settings are loaded, but it does not prove which parsed Egg or object supplies
the context later passed to slots 4 and 5.

The runtime edits reject three direct XML-position assignments as the source
of the actual trigger center:

1. The main `SplitTime0` Egg transform moves the yellow GPS/sign object, but
   the split event stays at its old location.
2. The `SplitTime0-0..3` checkpoint visuals move, but the split event stays at
   its old location.
3. Moving RaceLine[112] does not visibly move the event.

These results do not establish that those objects have no other role. They
only fail to support their edited positions as the gameplay center. The
candidate transform group described in the earlier D.0 report is therefore
**NOT_SUPPORTED** as a direct trigger-position source and is no longer the
next probe.

## France1 static comparison values

The existing France1 XML report provides reference coordinates, not recovered
gameplay-center coordinates:

| Split | Visual sign Row3 XYZ | Radius | ExtraTime | nearest RaceLine to visual sign |
|---:|---|---:|---:|---|
| 0 | `(-2470.51, 84.36, -110.63)` | 21 | 77.5 | index 112, distance 6.181 |
| 1 | `(-2797.56, -4.64, 563.60)` | 13 | 82.5 | index 224, distance 4.834 |
| 2 | `(-1644.96, 38.88, 1009.46)` | 12 | 70 | index 336, distance 0.000 |

The old D.0 sibling group centroids were close to the visual signs and their
corner distances resembled Radius. Moving `SplitTime0-0..3` did not relocate
SplitTime0, so those four transforms do not identify SplitTime0's direct
center. The analogous SplitTime1/2 groups were not independently tested.
Until runtime values from `P` are captured, comparison to StartArea,
FinishArea, signs, checkpoints, or RaceLine cannot promote any candidate to
the owner/source.

## One read-only runtime debugger capture

Use the exact Retail executable identified in
[`findings.md`](findings.md). Load Retail France1 and start the race. Set one
breakpoint at the proximity method:

```text
Module-relative: MRallye.exe + 0x8CC50
Preferred VA:    0x0048CC50 (preferred image base 0x00400000)
Condition:       *(int32_t *)(ECX + 0x14) == 0
```

At the first hit, before executing the prologue, record:

| Value | Read at method entry | Purpose |
|---|---|---|
| `ECX` | register | `gaRaceSplitTimeAI this` |
| `*(int32_t *)(ECX+0x14)` | memory | should be Split Time ID `0` |
| `*(float *)(ECX+0x18)` | memory | France1 baseline Radius should be about `21.0` |
| `*(float *)(ECX+0x1C)` | memory | France1 baseline ExtraTime should be about `77.5` |
| `ctx = *(uint32_t *)(ESP+0x04)` | stack | actual context argument to the callback |
| `P = *(uint32_t *)(ctx+0x50)` | memory | runtime spatial-data object pointer |
| `*(uint32_t *)P` | memory | possible vtable/type clue for the owner object |
| `float[P+0x4C], float[P+0x50], float[P+0x54]` | memory | actual center used by the distance check |
| `*(uint32_t *)(ESP)` and call stack | stack/debugger | return address and virtual-dispatch path |

Disable the breakpoint after the first valid hit so the per-frame callback
does not repeatedly stop execution. Do not edit registers or memory. Coordinates
should be finite; do not assume in advance that they equal the visual sign or
checkpoint centroid. The return address/call stack and `P`'s vtable pointer
are the needed clues for the owner/caller follow-up.

This capture is needed because static analysis found many generic virtual-call
sites but did not resolve the unique caller for this method. It can confirm the
live center and reveal the runtime owner shape. It does not itself prove which
XML element originally populated that object; that requires following the
captured object/call stack in the same exact executable.

## Controlled data edit

**None prepared.** No XML/data source field has been identified that supplies
`P+0x4C..+0x54`. Editing the visual sign, checkpoint group, or RaceLine again
would repeat rejected/not-supported candidates. Select one data edit only
after the runtime capture and owner/source trace establish a specific source
field.
