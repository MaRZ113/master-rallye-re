# Frontend identity and selection lifecycle

Frontend identity is multi-channel. The verified display consumers include
Vehicle Select manufacturer/model (`0x33`/`0x34`), Quick Race (`0x35`), Race
Options manufacturer/model, Vehicle Setup, and Race Details. Runtime
`CarType` and `WheelType` remain independent of display selectors.

The SDK's class-local mappings are sparse and explicit:

| Vehicle | Physical ID | Class | Local ordinal |
|---|---:|---|---:|
| Navara | 7 | T2 | 0 |
| R5VQualifier | 27 | T2 | 7 |
| Mercedes | 26 | T1 | 7 |

## Vehicle Select initialization and re-entry

`FUN_00480B60` (`0x00480B60`) reads the active
`Frontend/VehicleSelect/PlayerID`. In the Quick Race restore path it selects
the corresponding player context through `FUN_004AE700`, reads that player's
stored physical vehicle through `FUN_004ADFB0`, then calls
`FUN_00481E50` at `0x00480E5E` with the physical ID and scene object. This is
the native physical-ID-to-class/local restoration boundary. At the end of
construction, the J.2 hook at `0x00481152` publishes the resolved class and
class-local ordinal as `UI/XYButton/YValue` and `UI/XYButton/XValue`.

The first incorrect transition was in the inherited sparse reverse mapper's
ID27 arm at `0x0068E895`, not in the XY publication hook. The arm set
`this+0x10` to T2 (`1`) but wrote local ordinal `7` to `this+0x14`, which is
the T1 ordinal field. The per-class fields are T1 `+0x14`, T2 `+0x18`, and T3
`+0x1c`; the matching forward mapper also reads T2 from `+0x18`. As a result,
the selected T2 ordinal remained at its existing/default zero in the observed
constructor path. The publisher correctly exposed T2/local0, and the native
forward mapper resolved that to stock physical ID7/Navara. This matches the
human-observed CarModel/selectedCar 7 and XValue 0 while stored Quick Race
Car0 remained 27.

ID26 was unaffected because T1/local7 belongs at `+0x14`; stock ID7 remains
on the unmodified native T2/local0 path at `+0x18`. The corrected J.2
composite changes only the ID27 mapper displacement byte at `0x0068E897`
from `0x14` to `0x18`. The class stays T2, the physical ID stays 27, and the
existing publication hook then observes T2/local7 and publishes XValue 7.
No fixed ordinal or physical ID is forced globally.

This is an exact-bundle static dataflow finding that explains the reported
runtime symptom. The owner subsequently tested the exact corrected candidate
and confirmed ID27 re-entry works. Record that as
`HUMAN_CONFIRMED_PASS`; there is no new Broker capture for this result. The
native forward/reverse mapping remains `STATICALLY_VERIFIED`. See the
[J.2 closeout](j2/closeout-2026-10-09.md) for candidate identity and evidence
boundaries.
