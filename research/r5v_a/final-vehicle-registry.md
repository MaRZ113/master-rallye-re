# Final PC vehicle registry

Evidence: final EXE constructor at 0x458E70-0x4598CB, 0x34-byte records; model folders and physics blocks are separately matched case-insensitively. Indices are the constructor offsets, not XML or directory order. Display strings follow the 12-byte localization table at 0x6B99E8, with 23-25 checked against ICE CREAM VAN/UFO/FORKLIFT.

Active named entries: **25**, indices **0-24**. The array constructor reserves 26 records; index 25 has no explicit named initializer. Its runtime role is unresolved. Class groups are 0: 0-6, 1: 7-13, 2: 14-24.

| ID | Internal name | Display name | Folder | Class | Physics XML | Scene refs |
|---:|---|---|---|---:|---|---:|
| 0 | Landcruiser | TOMMEK DIRTBEAST | LandCruiser | 0 | Landcruiser | 0 |
| 1 | Pajero | DRAGHOV IMAGINO | Pajero | 0 | Pajero | 1 |
| 2 | Tata | TATA SAFARI | Tata | 0 | Tata | 1 |
| 3 | Terrano | NISSAN TERRANO II | Terrano | 0 | Terrano | 0 |
| 4 | Chevyblazer | CHEVROLET BLAZER | ChevyBlazer | 0 | Chevyblazer | 0 |
| 5 | Xtrail | NISSAN X-TRAIL | Xtrail | 0 | Xtrail | 0 |
| 6 | Frontera | VAUXHALL FRONTERA SPORT | Frontera | 0 | Frontera | 0 |
| 7 | Navara | NISSAN NAVARA | Navara | 1 | Navara | 0 |
| 8 | Forester | SUBPELKA WOOLDAND | Forester | 1 | Forester | 5 |
| 9 | Jump | DRAGON JUMP JEEP | Jump | 1 | Jump | 33 |
| 10 | Rmonster | RUSSIAN MONSTER | RMonster | 1 | Rmonster | 1 |
| 11 | Patrol | NISSAN PATROL | Patrol | 1 | Patrol | 0 |
| 12 | Newrav | REECE PICKUP | NewRav | 1 | Newrav | 0 |
| 13 | Kiasportage | KIA SPORTAGE | KiaSportage | 1 | Kiasportage | 0 |
| 14 | Wildcat | BOWLER WILDCAT | WildCat | 2 | Wildcat | 1 |
| 15 | Simmbugghini | SIMMONITE SIMMBUGGHINI | Simmbugghini | 2 | Simmbugghini | 0 |
| 16 | Astero | DRAGON ASTERO | Astero | 2 | Astero | 1 |
| 17 | Kangoo | SCHLESSER KANGOO | Kangoo | 2 | Kangoo | 1 |
| 18 | Megane | SCHLESSER MEGANE 2001 | megane | 2 | Megane | 1 |
| 19 | Mattserati | LEE MATTSERATI | Mattserati | 2 | Mattserati | 0 |
| 20 | Bruno | FORD ASM PRO-TRUCK | Bruno | 2 | Bruno | 1 |
| 21 | SeatBuggy | SCHLESSER BUGGY 1997 | SeatBuggy | 2 | SeatBuggy | 0 |
| 22 | Kamaz | KAMAZ TRUCK | Kamaz | 2 | Kamaz | 0 |
| 23 | Icecream | PRIVATEER ICE CREAM VAN | IceCream | 2 | Icecream | 0 |
| 24 | Ufo | STEEL MONKEYS UFO | Ufo | 2 | Ufo | 0 |

All 25 named entries have a model folder and physics block. The extra `DataGx/Vehicles/forklift` folder has no named constructor entry or `Vehicles/Forklift/` physics block. Nine additional physics blocks have no named final registry entry: Citroen, Mercedes, Trooper, Pajerostripe, Bowler, Terios, Navarabig, Megane2, Cherokee.

Scene-reference counts include literal `Car Name` fields in shipped scene XML; they do not prove campaign selection. `frontend_references`, `unlock_state`, and `resource_id` remain unresolved per vehicle. Numeric ID at record +0x04 equals the table index; class at +0x08. The other numeric field at +0x1C is retained without a semantic label.

See `final-vehicle-registry.json` for per-record file inventory, hashes, and source addresses.
