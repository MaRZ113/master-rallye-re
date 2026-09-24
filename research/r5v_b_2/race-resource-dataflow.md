# Race and preview resource dataflow

## Race name producer

The race broker constructor `0x4ABCE0` places `Race/Car` + `/CarType` at broker offset `+0x64`, `/CarID` at `+0x68`, `/WheelType` at `+0x6C`, and `/CarClass` at `+0x74`. Live race setup `0x44A320` iterates `Race/NumCars`. Its ordinary-mode path calls `0x44A510`; modes 5/6/8 call `0x44A710`. The former reads `Race/CarN/CarID` (`0x4AC660`), indexes registry records with stride `0x34`, obtains the owned name at record `+0x20`, and writes it to `Race/CarN/CarType` (`0x4ACA40`) and `/WheelType` (`0x4ACB40`). The campaign variant reads `MasterRallye/CarN/CarID` (`0x4B0630`) and performs the same name transfer. `0x4C0B20` later reads `CarType` into race object setup/physics construction.

## Frontend preview

Retail scene `DataScene/FrontendScreens/VehicleSelect.xml` binds `gaFrontendCarMoverAI` model ID to `Frontend/VehicleSelect/CarModel`. Raw instructions in the preview mover at `0x44C4DD–0x44C58A` read that numeric ID, reject only `-1`, calculate `registry + 0x24 + ID*0x34` (the record `+0x20` name), and build `Vehicles/<name>/complete`. `0x44C58A` passes the path to `0x4F5B70`. Thus a correctly initialized ID25 with name `Astero` is sufficient for this preview path. Ghidra groups this mover in a much larger function near `0x44A8E0`; the raw instruction window is the reliable boundary evidence.

## Race render actor: conditional edge

The virtual race actor method at `0x4B6A00` is installed by constructor `0x4B6750` (vtable `0x691128`, method slot `0x69113C`). `0x4B6B17` tests `Frontend/Active` via `0x4ADB70`. When true, `0x4B6B3D–0x4B6B63` obtains the actor's `Race/CarN/CarType` through broker getter `0x4AC610` (whose raw `0x4AC627` reads broker `+0x64`) and assigns it to actor name field `+0x20`. At `0x4B6E45`, the method reads that field; `0x4B6F9F–0x4B7027` builds `vehicles/<name>/car` and loads it through `0x4F5B70`. `0x4B7100` appends literal `/wheel`; `0x4B71E1` loads the wheel resource through `0x4F5B70`. Literal suffixes were checked directly in retail `.data` at `0x6B1960` and `0x6B1974`.

When `Frontend/Active` is false, that dynamic assignment is skipped. The actor's `+0x20` field can instead come from its scene `Car Name` property (`0x4B6960` parser). Retail RaceTest XML has many hardcoded `Car Name="Jump"` entries. `0x449843` and `0x449930` call the `Frontend/Active` setter with 1; its initialization at `0x449100` is 0. These instructions do not prove its value at the specific Quick Race actor construction event. Consequently the unconditional edge `ID25/Astero → race car.dx/wheel.dx` is **not yet established**. The dynamic branch is proven; branch reachability for P1 is open.

Texture/DXT dependencies are expected to follow the loaded DX assets, but this phase did not independently trace each texture load. No race resource path was inferred from the older `0x443D40` function with no proven callers.
