# Player selection dataflow

## Campaign-side key

`0x4819B0` calls `0x481E20`, obtains absolute ID in EDI and stores it to `Frontend/VehicleSelect/CarModel` through `0x4D8000` at `0x4819ED–0x4819F6` when unlock evaluation permits it. For class 2/local 11, `0x481E20` adds 14, giving 25. `0x47BB00` reads `CarModel` through `0x4D6760` and writes that same integer to `MasterRallye/PlayerT3Car0`; its `0x47BD05–0x47BDA9` instructions do not subtract 14. Retail `DataGame/MasterRallye.xml` initializes this key to 14. `0x453AB0` reads the key for frontend restoration, and `0x453980` is a writer from an absolute ID. These facts contradict the B.2 prompt's proposed `PlayerT3Car0=11` edge.

## Quick Race path

`0x481340` is a subroutine within the large function Ghidra labels `0x480B60`. At `0x481391`, it calls `0x481E20`; at `0x481396`, EDI receives the absolute ID. At `0x48140F–0x481417`, it passes that ID to the race broker (`0x4ADA50` with the car index from screen `+0x2C`) and `0x4ACAF0`, which targets `Race/CarN/CarID` (broker field `+0x68`). It also reads class at registry base plus `ID*0x34` and writes `Race/CarN/CarClass` through `0x4ACC10`. A branch at `0x481456` stores the same EDI value to `Frontend/QuickRace/Car0` via `0x4ADF50`.

`0x47B780` restores `Frontend/QuickRace/Car0` through `0x4ADFB0`, writes that integer to `Race/Car0/CarID` via `0x4ACAF0`, and indexes the registry for class. No second local-to-absolute conversion occurs in this restore path: it expects the already absolute value saved by `0x481340`.

The Quick Race path is therefore `class 2/local 11 → 0x481E20 → ID25 → Race/Car0/CarID`, subject to unlock/selection gates in the frontend. Numeric ID25 is inside the allocated 26-record registry; record25 still needs normal initialization in the future phase.
