# ID26 availability predicate

## Recovered stock behavior

`FUN_0045A150` consumes a native vehicle-record pointer and reads its absolute
Vehicle ID at `+0x04`. Its retail ID switch checks the corresponding
`Progress/UnlockedCars/*` path; `Progress/Cheats/UnlockCars` and
`Progress/Cheats/UnlockAll` bypass the ordinary per-vehicle predicate. The
default switch arm is available. The audited stock matrix for IDs 0 through 25
is preserved in `stock-unlock-matrix.json`.

Quick Race class reachability is independent. `FUN_00480B60` builds the class
list from opened-mode and cup-cheat state. A fresh profile exposing T1 does not
imply that every T1 vehicle is available.

## ID26 policy

For this qualification vehicle only, the existing wrapper at the Vehicle
Select call site `0x004819CE` supplies a temporary ID3 record to the native
availability function when the physical record is ID26. ID3 is the T1
CupCar1 oracle:

| State | Expected ID3 | Expected ID26 |
|---|---:|---:|
| `T1CupCar1=False`, car cheats false | locked | locked |
| `T1CupCar1=True`, car cheats false | available | available |
| `UnlockCars=True` or `UnlockAll=True` | available | available |

All other physical IDs use their original record. The wrapper does not change
the record's ID, the class-local mapping, runtime `CarID`, or ID25's native
`Bonus2` check.

## Evidence boundary

The locked and unlocked JSON captures confirm the gate's reported result and
Vehicle Select fields. They do not prove widget art or the accept-button
interaction. Those are tested separately with the corrected scene overlay.
