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
| Diagnostic forced proof | Car1 physical CarID becomes 26 after normal selection | `CONFIRMED_BY_RUNTIME` for the tested T1 / three-AI Quick Race path |
| Natural Quick Race T1 AI eligibility | Append physical ID26 to the explicit T1 absolute-ID list `[0,1,2,3,4,5,6,26]` | `CONFIRMED_BY_RUNTIME` for H.1 natural Quick Race |
| Rallye Cup / Invitation / Master Rallye T1 eligibility | Same sparse T1 list is appended at each dynamic roster-creation owner; persisted roster owners are untouched | H.2 `STATICALLY VERIFIED / READY_FOR_HUMAN_RUNTIME` |
| Challenge | Authored event roster is left unchanged | Not auto-injected by H.2 |
| Practice | No distinct stock Practice AI-roster owner found in bounded frontend/setup audit | Not applicable to the separate dynamic-pool scope |

The proof guard is Car1-specific only to isolate actor materialization. It is
not the natural-pool policy. H.0.1's ordinary hardened candidate contains
neither the proof guard nor a randomizer. The H.1 candidate has no forced
CarN and no randomizer; it appends only physical ID26 to the native T1 source
pool, preserves all pre-existing IDs, and keeps T2 IDs 7–13 and T3 unchanged.

## Expected proof participant

* Car0: physical ID0, T1 human.
* Car1: forced physical ID26, T1 AI, native DriverID path.
* Car2/Car3: distinct stock T1 AI IDs in 1–6.
* `Race/NumCars=4`, `Race/NumPlayers=1`.

The corrected H.0.1 active-race capture reports Car1 ID26/T1/DriverID8,
`CarType=Mercedes`, and `WheelType=Mercedes`; the human confirmed the actor,
AI driving, progress, finish, and Results-row presence. The Results row's
`GALOCAL UNKNOWN` is a separate name-selector defect; the H.0.1 display fix is
static-only until a post-Results human capture confirms it. The runtime
checker classifies AI `PlayerType` by comparing Car1 with Car2/Car3 and
distinguishing them from Car0; it reports observed enum values without
hardcoding an unverified numeric AI constant.
H.1 natural Quick Race selection and its fixed Results display string are now
`CONFIRMED_BY_RUNTIME` from the 2026-10-07 runtime captures; the display name
is `JEAN-PIERRE STRUGO`, classified `REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER`;
exact ML-320 pairing is unproven. H.2's mode-specific pool changes remain
static/candidate evidence pending separate new Cup/Master runtime validation.
The demo group-`0x39` Mercedes ID2 -> selector 2 ->
`JOSE MARIA SERCIA` association is classified `DEVELOPER-PLACEHOLDER` for a
Mercedes T1 Results identity. H.1 does not alter native DriverID selection or
publication.
