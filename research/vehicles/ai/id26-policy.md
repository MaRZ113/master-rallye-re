# Mercedes ID26 AI policy

## Physical identity

ID26 remains the G.1 Mercedes physical VehicleRecord: T1 class code 0, T1
local index 7, model/wheel family Mercedes, `Vehicles/Mercedes` physics, and
G.2 `stock_audio_profile_id=0`. No physical ID, VehicleRecord, frontend,
unlock, audio, or asset change is part of the H proof.

## Current and intended AI semantics

| Axis | Policy | Status |
|---|---|---|
| Player unlock | Mirrors the stock T1 Cup ID3 gate | `CONFIRMED_BY_RUNTIME` in G.1; unchanged |
| Stock Quick Race T1 membership | ID26 absent from retail IDs 0–6 | `CONFIRMED_BY_EXE` |
| Diagnostic forced proof | Car1 physical CarID becomes 26 after normal selection | `READY_FOR_HUMAN_RUNTIME` |
| Natural T1 AI eligibility | Append physical ID26 to the explicit T1 absolute-ID list | `NOT STARTED`, gated on forced AI runtime pass |
| Natural selection in other modes | No inference | `UNKNOWN` |

The proof guard is Car1-specific only to isolate actor materialization. It is
not the intended final policy. The later natural candidate must have no forced
CarN, must preserve IDs 0–25, and must keep T2 IDs 7–13 and T3 unchanged.

## Expected proof participant

* Car0: physical ID0, T1 human.
* Car1: forced physical ID26, T1 AI, native DriverID path.
* Car2/Car3: distinct stock T1 AI IDs in 1–6.
* `Race/NumCars=4`, `Race/NumPlayers=1`.

The checker classifies the AI `PlayerType` by comparing Car1 with Car2/Car3
and distinguishing them from Car0. It reports observed enum values without
hardcoding an unverified numeric AI constant.
