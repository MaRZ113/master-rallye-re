# retail resource, physics, selection and persistence path

## What is established

The frontend `0x481E20` returns absolute ID `local+14` for class 2. `0x4819B0` fetches singleton record `+0x04 + ID*0x34` and calls `0x45A150` on it, then reads its four stat integers. Retail initializer `0x45A0B0` stores an owned internal name string at record `+0x20`; `0x443D40` builds a `Vehicles/<name>/car` resource string and the binary has neighboring `/wheel` and `complete` presentation paths. Asset evidence for Astero's `car.dx`, `wheel.dx` and `complete.dx` is in R5V-A/R4A. The exact call from selected record `+0x20` to every resource role is not yet completely typed.

`DataGame/Game.xml` loads `vehicles.xml`; retail has a `Vehicles/Astero/` physics namespace with 147 fields. Runtime also uses temporary `Vehicles/Car%d/...` instance keys, as shown by `0x4BC590` and other code. These are distinct from named model physics definitions. The bridge from record name or ID to the named Astero physics namespace has not yet been proven. Therefore setting record25's string to Astero is a plausible reuse strategy, not a demonstrated complete resource/physics binding.

## Other paths and risk

`0x480B60` reads a saved quick-race car ID via `0x4ADFB0` and passes it to `0x481E50`; `DataGame/frontend.xml` marks `Frontend/QuickRace/Car0`, `Car1`, and `Frontend/Network/Car0` as `SavePlayerState=True`. `RallyeCup.xml` and `MasterRallye.xml` also persist integer car IDs. There is no demonstrated validation for 25 on reload. Use a disposable profile and avoid saving for any later human test. No save format claim is made.

The `DataScene` corpus contains named AI `Car Name` fields, while race data has numeric `CarID`/`CarClass` fields. Opponent generation and indexed lookup of a player-selected 25 have not been fully audited. A duplicate Astero would reduce asset risk but not prove AI/event bounds safe. The first proof should stay in quick race, with no campaign integration.

## Remaining chain

Before a candidate can be built, trace selected ID 25 through quick-race confirmation and race creation; identify the exact model-name provider used by `0x443D40`, named physics key creation, `complete.dx` preview, wheel resolution, and any ID upper-bound checks. No source-data or executable patch was made in R5V-B.
