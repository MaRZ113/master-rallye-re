# Frontend vehicle identity writers

Vehicle identity presentation uses separate writers. A correct value in
Vehicle Select, Quick Race, or runtime race state does not guarantee that a
different screen refreshes its own Broker string correctly.

## Consumer map

| Channel | Broker output | Producer / lookup | Input identity | ID26 presentation | Current status |
|---|---|---|---|---|---|
| Vehicle Select manufacturer | `Frontend/VehicleSelect/ManufacturerName` | `FUN_004819B0`, group `0x33` | selected registry vehicle / absolute ID | `MERCEDES` | runtime confirmed |
| Vehicle Select model | `Frontend/VehicleSelect/ModelName` | `FUN_004819B0`, group `0x34` | selected registry vehicle / absolute ID | `ML-320` | runtime confirmed |
| Quick Race combined name | `Frontend/QuickRace/CurrentVehicleString` | `FUN_0047B040`, group `0x35`, three lookup sites | selected absolute vehicle ID | `MERCEDES ML-320` | runtime confirmed |
| Race Options manufacturer | `Frontend/QuickRace/CurrentManufacturerString` | `FUN_0047A540`, lookup `0x0047A65F`, group `0x33` | selected ID from `FUN_004ADFB0`, retained in ESI | `MERCEDES` | runtime confirmed |
| Race Options model | `Frontend/QuickRace/CurrentVehicleString` | `FUN_0047A540`, lookup `0x0047A6C4`, group `0x34` | selected ID from `FUN_004ADFB0`, retained in ESI | `ML-320` | runtime confirmed |
| Vehicle Setup combined name | `Frontend/VehicleSetup/CarName` | `FUN_0044F8E0`, lookup `0x0044FA29`, group `0x35` | EDI physical Vehicle ID | `MERCEDES ML-320` | prior channel pass |
| Race Details combined name | `Frontend/RaceDetails/CurrentVehicleString` | `FUN_0047C080`, group `0x35`, three lookup sites | absolute `RaceData/CompetitorN/CarID` via `FUN_004B0AF0` / `FUN_004B0630` | `MERCEDES ML-320` | runtime confirmed in single-player Master Rallye and Rallye Cup |

The Race Details writer is shared by Master Rallye and Rallye Cup. The normal
single-player path looks up Competitor0; the same writer also has split-screen
Competitor0 and Competitor1 branches. Their exact instruction spans and
resume addresses are in `../unlock/racedetails-localization.md` and the G.1
candidate manifest.

The Race Details pre-fix captures had `RaceData/Competitor0/CarID=26` and
`Race/Car0/CarID=26`, but the Broker output was `GALOCAL UNKNOWN` in both
modes. This was an independent group-`0x35` lookup, not a wrong mode or physical
ID alias. Final captures and human visual checks confirm `MERCEDES ML-320` in
both modes. The candidate returns the existing combined Mercedes string only
when the absolute selector is 26; every other ID executes the original
group-`0x35` lookup unchanged. The owner reports stock ID0 Race Details
regression and a full stage/Results PASS on the same candidate. No frontend
return or human split-screen test is claimed.

The Vehicle Select lock-requirement text is a separate group-6 channel:
`FUN_004819B0` uses the generic `CAR LOCKED` selector and an ID-dependent
requirement selector. ID26 mirrors stock ID3's requirement selector 9. This
does not change any vehicle-name localization group.

`Race/CarN/CarID`, `CarType`, and `WheelType` describe physical/runtime
identity, not localization selectors. The fixes are presentation-only and
retain physical CarID 26 and the Mercedes runtime family. No global `gaLocal`
behavior or donor localization entry is changed.

The failed first lock-control run used a Root without the generated
VehicleSelect scene. That deployment issue is resolved: corrected-root runtime
testing confirmed locked art, disabled acceptance, and natural unlock. It is
recorded with the final Race Details captures in `../unlock/runtime-captures.json`.

Challenge and Trophy/unlock-reward consumers were not changed and are not
qualified for addon ID26.
