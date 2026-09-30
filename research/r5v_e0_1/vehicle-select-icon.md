# Vehicle Select icon and carsheet binding — retail

## Scene mapping

Retail DataScene/FrontendScreens/VehicleSelect.xml contains statically
instantiated T1_Car, T2_Car and T3_Car widgets. T3 has T3_Car1 through
T3_Car11; there is no T3_Car12 for class2 local index 11 / absolute ID25.
Each widget names an image-bank index in the shared
DataGx/Frontend/VehicleSelect/carsheet resource. These bank indices are not
vehicle IDs. For example, Astero at ID16 uses T3_Car3 bank index 5.

| Class2 local | Absolute ID | Scene widget | Carsheet index |
|---:|---:|---|---:|
| 0 | 14 | T3_Car1 | 6 |
| 1 | 15 | T3_Car2 | 13 |
| 2 | 16 | T3_Car3 | 5 |
| 3 | 17 | T3_Car4 | 11 |
| 4 | 18 | T3_Car5 | 8 |
| 5 | 19 | T3_Car6 | 7 |
| 6 | 20 | T3_Car7 | 0 |
| 7 | 21 | T3_Car8 | 28 |
| 8 | 22 | T3_Car9 | 26 |
| 9 | 23 | T3_Car10 | 21 |
| 10 | 24 | T3_Car11 | 30 |
| 11 | 25 | no widget | no binding |

The screen updater FUN_00481950 loops over 12 positions while constructing
Button%dX property names, but the XML provides Button0XPos through
Button10XPos and only eleven T3 car widgets. The loop does not prove that a
twelfth icon widget or its storage exists.

## Asset inventory

The retail carsheet contains 32 indexed 128x128 DXT frames (0–31). The file
carsheet_025_000.dxt exists, is 65,556 bytes, and has SHA-256
675c37f6ba61527a4e1c5b97bf942b06c98dfdcab15be2033deb3f7ca1009065. Its
existence does not create a widget mapping. The carsheet container is
carsheet.dxb, SHA-256
712d655cd01fe2a6c7b5d3f9fd6b47234fdcc0430f1fcf4a85e383454131547f.

No evidence links frame 25 to Trooper. The icon failure is classified exactly
as **MAPPING_MISSING**: the retail indexed texture exists, but the scene lacks
the T3_Car12 binding. The owner's report that the ID25 Vehicle Select icon is
absent agrees with this static finding.

## Evidence classification

- T3 widget count and bank indices: **PROVEN**, retail scene inventory.
- Frame 25 file existence and hash: **PROVEN**, DXT inventory.
- ID25 icon mapping: **PROVEN absent** in the inspected retail scene.
- Frame 25 depicts Trooper: **UNKNOWN**; index order alone is not evidence.
- 11 -> 12 capacity alone creates a safe twelfth widget: **not proven**.

No scene or texture was modified.
