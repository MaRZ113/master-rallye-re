# Frontend selection, events and persistence

## Final selection

`DataScene/FrontendScreens/VehicleSelect.xml` instantiates `gaFEScreenVehicleSelectAI`, a `CarModel` presentation egg and car mover/spinner AIs. It does not enumerate car names. `DataGame/frontend.xml` stores `Frontend/QuickRace/Car0`, `Car1` and `Frontend/Network/Car0` as integer fields with `SavePlayerState=True`. These are persistent index candidates, not a proven full savegame structure.

The executable converts class-local selection to absolute ID at **0x481E20**: class 0 adds 0, class 1 adds 7, class 2 adds 14. The inverse path at **0x481E50** compares against 7 and 14. The final constructor class distribution is exactly 7/7/11 for IDs 0-24. At **0x4819B0** the selected absolute ID addresses `base + 0x04 + ID*0x34`; this is direct static-registry use. The menu's previous/next path at **0x481EB0–0x481F3F** retrieves `Frontend/VehicleSelect/VehicleList`, derives length from vector end-minus-begin divided by four, and compares against current index. Its **bound is dynamic with respect to that vector**, but the code that builds/populates the vector remains untraced. A new registry record would not automatically prove a new selectable frontend item.

## Physics and resource binding

`DataGame/Game.xml` loads `vehicles.xml`; that file has 34 named per-vehicle physics sections in the final build and no order/index declaration for playable cars. Existing named registry records all have corresponding physics blocks. It defines dimensions, chassis, steering, engine, suspension and damage parameters. `Damage.xml` and `collision.xml` supply additional shared parameters. The EXE also has `Vehicles/Car%d/... ` strings for runtime car instances; do not confuse those with the per-model XML namespaces.

At **0x443D40** the gameplay loader constructs a `Vehicles/<name>/car` path; adjacent code and `/wheel` string indicate separate resource roles, consistent with R4A runtime results. The exact call chain from record name to path and full role selection is partially traced. An arbitrary name has no data-only proof.

## AI, events and progress

The final scene corpus has **308 literal `Car Name` fields** in `DataScene` XML, across ten distinct names. For example `RaceTest/Italy1.xml` uses `gaBootAICar` with `Car Name="Jump"` and `Car Active` fields. These are string references; they do not establish that every campaign opponent uses strings. The final registry JSON lists scene files for each named record. No Forklift scene reference was found.

`DataGame/RallyeCup.xml` and `MasterRallye.xml` store class-specific player car integers, with defaults 0, 7 and 14. `MasterRallye.xml` also stores `Car0/CarID` etc. `Progress.xml` contains **17 named unlocked-car/cheat booleans** keyed by reward concepts rather than a 25-entry per-car array. Their fields are marked `SavePlayerState=True`. This shows persistence exposure, but does not prove a fixed bitset or the binary save encoding. Campaign integration is unnecessary for the first slot proof; quick race should be isolated from existing saves until bounds are audited.

## Open limits

VehicleList population, locked/unlocked filtering, AI/opponent enumeration, selected-ID validation before all callers and savegame rehydration are unresolved. The frontend vector can grow dynamically, but its source may still be hardcoded. No extra-slot runtime claim follows from the dynamic vector bound.