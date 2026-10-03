# Participant identity storage

All addresses below refer to the exact pristine image hash in [findings](findings.md).
Fields and accesses are **CONFIRMED_BY_EXE**; their occurrence in a future live
race is not inferred from static code or surviving Broker paths.

## Race wrapper: cached Broker keys, not numeric participant fields

`0x4ABCE0` initializes a wrapper whose members hold path/key handles.
`0x4ADA50` obtains the singleton; `0x4AC590` builds `Race/Car%d` and the methods
append a cached property key. Do not label wrapper +0x68 a stored numeric CarID.

| Semantic key | Wrapper offset | Getter / setter | Audited writes / reads |
|---|---|---|---|
| NumCars | +0x38 | setter `0x4AC3D0` | Quick Race `0x47B780`; init/results loops |
| PlayerType | +0x60 | `0x4AC5C0 / 0x4AC8E0` | `0x44A450`; camera `0x4B8810`, reset `0x4CC5F0` |
| CarType | +0x64 | getter `0x4AC610`, setter `0x4ACA40` | `0x44A510` registry family; body loader `0x4B6A00` |
| CarID | +0x68 | `0x4AC660 / 0x4ACAF0` | player `0x481417`; AI `0x458435`; `0x44ED50`, HUD/results |
| WheelType | +0x6C | setter `0x4ACB40` | `0x44A510`; wheel loader `0x4B6A00` |
| CarClass | +0x74 | `0x4AC730 / 0x4ACC10` | player `0x481435`; AI `0x458456`; four direct getter calls listed below |
| DriverID | +0x7C | `0x4AC7B0 / 0x4ACCD0` | AI `0x458468`; factory `0x42AA3D`, result collector `0x47D6D0` |
| OpponentClass | +0x54 | `0x4AC160 / 0x4AC530` | Registered, no direct CALL to either method found |

PlayerType 1 is the human branch, 2 the AI branch (`0x44A450`). The separate
`0x4AC930` method changes **Controller/DeviceMap/Player%d**, not a Race
participant identity field. `CarType`/`WheelType` are family strings; they are
not an AI type enum or class-local index.

The exhaustive direct-call cross-check for `0x4AC730` found:
`0x42CFFA` (AI reads Car0), `0x47B92C`, `0x47B95E` (Quick Race),
`0x4BBE8C` (race-description localization reads Car0).

## Distinct native structures

| Owner | Recovered offset / role | Access and confidence |
|---|---|---|
| Registry record, stride0x34 | record+4 absolute ID; +8 class; +0x20 family name | `0x45A0B0`; registry object offsets +8/+0xC/+0x24 respectively; CONFIRMED_BY_EXE |
| Frontend selection screen | +0x10 class; +0x14/+0x18/+0x1C local selections; +0x2C participant index | `0x481340`, `0x481E20/0x481E50`; CONFIRMED_BY_EXE |
| Chooser live frame at `0x458428` | ESI participant; [ESP+0x14] absolute ID; [ESP+0x18] DriverID | `0x4583EB..0x458468`; CONFIRMED_BY_EXE |
| Vehicle boot actor | +0x14 participant index; +0x20 owned family string; +0x50 loaded model pointer | constructor `0x4B6750`, init `0x4B6A00`; CONFIRMED_BY_EXE |
| AI controller object (0xD4 allocation) | +0x40 difficulty; +0x44 **Car0 class**; +0x70 own CarN handle; +0x9C own physical speed ceiling | ctor `0x42CC30`, init `0x42CDB0`, physical reader `0x42D0D0`; CONFIRMED_BY_EXE |
| Results record (stride0x1C) | +0 participant; +4 DriverID; +8 CarID; +0xC time; +0x14 rank | `0x47C6B0/0x47C6C0`, `0x47D6D0`; CONFIRMED_BY_EXE; remaining flag/word semantics incomplete |

No single contiguous native record containing all Race Broker fields has been
established. CarClass is derived from the registry before publication; results
retain CarID rather than a recovered per-record class field. None of these
layouts establishes larger participant capacity.

## Critical stack distinction for patching

The chooser originally accepts `(firstAI, count, class, excludedID0, excludedID1)`.
At the intervention, +0x84/+0x88/+0x8C retain the first three arguments. The
two exclusion argument slots **have already been overwritten**: +0x90 is the
last driver-pool value 9 (`0x45834E` with two pushed arguments), and +0x94 is
the last admitted vehicle-pool ID (`0x4581EC`, optional `0x458226/25B/290/2C5`,
with three pushed arguments). Stack offsets in these write instructions include
their temporary PUSHes. Never guard on the original excluded player IDs there.
