# 4x4 Evo 1 / 4x4 Evo 2 (PC) / 4x4 Evo 2 (GC): vehicle comparison and MR collection (2026-11-13)

Owner request: compare the three games, pick the models that suit Master Rallye best, port them with MR
materials into a separate class for now, and list what existed only in 4x4 Evo 1.

Sources (read only): `E:\RallyWorkshop_Sources\sources\4x4 Evo\TRUCK.POD` (build 58), `...\4x4 Evo 2\TRUCK.POD`,
GC `TRUCK.pod` from the disc (research/source-formats `evo2-gc/tools/rvz.py`). All three are POD2 with the same
TRK/SMF grammar (Evo 1 TRK version 6, Evo 2 version 7). Counts below come from every `TRUCK/*.TRK` and the body
SMF named by `truckModelBaseName`.

## Rosters

| | 4x4 Evo 1 | 4x4 Evo 2 PC | 4x4 Evo 2 GC |
|---|---|---|---|
| TRK catalogs (incl. 2WD/4WD/trim duplicates) | 174 | - | - |
| Vehicles (make + model) | 81 (18 of them promo "Sport Trac" liveries) | 67 | 72 |
| Distinct body models | 67 | 55 | 59 |
| Body triangles (median / range) | 1897 / 1354-2814 | 1894 / 1354-2802 | 1961 / 1354-3006 |
| Body texture | 512x512 8-bit RAW + ACT palette | 512x512 TIFF, dual plane (colour mask: catalog paints) | same as PC |
| Paint catalog | TRK colours (palette) | colorList HSV records (recolouring, decoded) | race/GC exclusives: none |

* **Evo 2 reuses Evo 1 geometry.** 48 vehicles exist in both; their body triangle counts are equal or differ
  by 2-6 (seam fixes), e.g. Silverado 2802/2802, Tahoe 2588/2588, Land Cruiser 1890/1886. Mitsubishi
  "Pajero Rally" (Evo 1) and "Montero Rally" (Evo 2) are the same mesh (1559). Evo 2 adds better textures (TIFF
  with the paint mask) rather than new bodies.
* **GC = PC + 5 vehicles + 6 remodelled bodies.** 61 of 67 shared vehicles are identical; Xterra (1897 -> 2559),
  Durango (1890 -> 2634), Land Cruiser (1886 -> 2548) and Yukon (2600 -> 3006) have new, denser GC bodies.
  GC-only: Calmini Nissan Frontier, Warn Dodge Dakota, Stillen Silverado monster, Jeep Wrangler Rubicon, Tahoe Z71
  (catalog name; Tahoe body).
* `SUV.pod`, `TOY.POD`, `MTMT.POD` in the Evo 1 folder are POD1 fan add-ons ("Created with PODTool", NFS IV traffic
  SUV, a toy truck, a monster "MDJ"), not game content: excluded.

## Only in 4x4 Evo 1 (did not reach Evo 2)

| Vehicle | Evo 1 model | Body tris | Evo 1 class |
|---|---|---|---|
| Ford Excursion Ltd | EXCULIM / EXCLIM2 | 1722 | Full-Size SUV |
| Ford Expedition | EXPED | 1800 | Standard SUV |
| Ford Explorer Ltd | EXPL | 1846 | Standard SUV |
| Ford Explorer Sport | EXPLSP | 1815 | Compact SUV |
| Ford Explorer Sport Trac | SPTRACK | 1933 | Standard SUV |
| Ford Explorer Sport Trac promo liveries (18: CNET, EGM, IGN, GameSpot, ...) | same body | 1933 | Cheat |
| Ford F-150 Lariat / XLT SuperCrew (2WD, 4WD) | F1502WD / F1504D | 1908 | Full-Size Truck |
| Ford F-150 Race Truck | FORDTRF | 1502 | Race Truck |
| Ford F-250 XL / XLT / Lariat SuperCab | F250 / F2502WD | 1901 | Full-Size Truck |
| Nissan Pathfinder XE / SE / LE | PATHLE | 1715 | Standard SUV |

The whole Ford range left with Evo 2 (licence); the Pathfinder slot became the Infiniti QX4 (same platform).
Porting these needs an Evo 1 path: TRK version 6 and 8-bit RAW + ACT textures (the RAW/ACT reader already exists
for SUSP.RAW); geometry is the same SMF.

## Only in 4x4 Evo 2 (PC and GC)

Chevrolet Blazer K5, Dodge Ram 1500 + Ram Race Truck, GMC Sierra Trophy Truck, GMC ARB Sierra monster, Infiniti QX4
(+ Rally Edition), Jeep Liberty Sport (+ Rally), Jeep Wrangler Sport, Jeep ARB Wrangler Rally Edition, Nissan
Frontier (Desert Runner, Supercharged Crew Cab, Race Truck), rally editions of 4Runner, Blazer, Durango, LX 470.

## What suits Master Rallye

MR's cars are rally/raid-prepared, liveried, slightly toy-like off-roaders of 2001; MR body meshes and 512-class
textures are the same generation as Evo's (~1.9k triangles, 512x512 body atlas), so every Evo body fits technically.
Stylistically:

1. **Best fit - prepared and race versions** (sponsor liveries, roll cages, bull bars, light pods; numColors 0 =
   fixed livery like MR): the 11 Rally Edition / Race SUVs, the 5 race trucks, the ARB monster, and the GC
   exclusives already piloted. They also carry stock parts, so the KIT row (bare / stock / full) applies.
2. **Good with PAINT** - stock SUVs/pickups: civilian look, but the Evo 2 catalog paints (decoded recolouring,
   PAINT row) make them a T1-like set. Prefer the GC body where it was remodelled (Xterra, Durango, Land Cruiser,
   Yukon).
3. **Evo 1 exclusives** - Fords and Pathfinder: same style as (2); need the Evo 1 texture path first.
4. Duplicates of MR retail (Land Cruiser, Montero/Pajero, Xterra/Terrano-like) are lowest priority.

## Collection pilot (this commit)

`evo2_gc_pilot.py` registers the 17 vehicles of group 1 (keys = GC TRK names) with author class T2 and target
"EVO (separate class, owner to place)"; donors: Pajero for SUVs, Navara for pickups, Patrol for the monster.
Built from the GC `TRUCK.pod` into `.research-output/evo2-collection/<key>-scene|pilot`. Results below.

### Batch results (2026-11-13)

Native states PASS (`PASS_SOURCE_OFF_STATE_EQUIVALENCE`) for 15 of 17; preview sheet
`.research-output/evo2-collection/evo2_collection.png`. Dimensions in metres (true Evo size, feet x 0.3048).

| Key | Vehicle | Donor | L | W | H | Wheel r |
|---|---|---|---|---|---|---|
| T4R4 | Toyota 4Runner Rally Edition | Pajero | 4.77 | 1.83 | 1.64 | 0.47 |
| JGCRSUV | Jeep Grand Cherokee Race SUV | Pajero | 4.72 | 2.07 | 1.86 | 0.37 |
| DDRE4 | Dodge Durango Rally Edition | Pajero | 4.98 | 1.92 | 1.83 | 0.47 |
| JLRE4 | Jeep Liberty Rally Edition | Pajero | 4.73 | 2.13 | 1.79 | 0.47 |
| LLX470RE | Lexus LX 470 Rally Edition | Pajero | 5.04 | 2.11 | 1.82 | 0.47 |
| IQX4RE4 | Infiniti QX4 Rally Edition | Pajero | 4.77 | 2.12 | 1.68 | 0.47 |
| XTERRT | Nissan Xterra Race SUV | Pajero | 4.65 | 1.93 | 1.69 | 0.38 |
| CBRE4 | Chevrolet Blazer Rally Edition | Pajero | 4.61 | 1.89 | 1.66 | 0.47 |
| MPRT2D | Mitsubishi Montero Rally | Pajero | 4.52 | 2.11 | 1.79 | 0.39 |
| AJWS | Jeep ARB Wrangler Rally Edition | Pajero | 4.25 | 2.06 | 1.73 | 0.38 |
| DDRT | Dodge Dakota Race Truck | Navara | 5.62 | 1.82 | 1.82 | 0.47 |
| DRTT | Dodge Ram Race Truck | Navara | 5.52 | 2.32 | 1.70 | 0.47 |
| GS1TT | GMC Sierra 1500 Trophy Truck | Navara | 5.99 | 2.30 | 1.76 | 0.47 |
| FRRT | Nissan Frontier Race Truck | Navara | 5.08 | 2.00 | 1.64 | 0.37 |
| AMT | GMC ARB Sierra Monster Truck | Patrol | 5.80 | 2.29 | 3.23 | 0.84 |

Deferred: **CTTT2** (TrailBlazer Race SUV) and **TTTT2** (Tundra Race Truck) have no lamp lens objects (tail
lamps painted on the body), and the MR Classic pilot needs a brake draw; next = synthesised lamp quads at the
painted lamp UVs. Adapter fix in this commit: zero-length source normals (Durango Rally and both deferred bodies)
take their faces' normal.

Not done yet (owner decisions / next steps): roster rebuild with these cars (V-CAP registry build + Vehicle Manager),
the separate class itself (the SDK and the MRVC registry know T1-T3 + the frontend-only T4 layer; a fifth Vehicle
Select class needs the T4-style native layer extended), kit packages (stock parts present on all 15), gameplay.

## Evo 1 path and Ford / Pathfinder pilots (2026-11-13)

`evo2_gc.create_scene(..., game='evo1')` reads 4x4 Evo 1 `TRUCK.POD` (build 58) with the same adapter:

* **TRK version 6** carries every field the adapter uses (suspension types, `static_bpos`, `stockPartList[]`,
  `colorList[]` in the Evo 2 grammar: HSV delta + swatch RGB). Evo 1 stock-part names missing from the Evo 2 table
  (`HighDrivingLights`, `FenderFlares`, `Winch`, `MudFlaps`) map through `STOCK_EVO1`; Evo 2 output is unchanged
  (4Runner Rally scene rebuilt equal except the new `version` field).
* **Textures**: `<name>.RAW` = square 8-bit index plane (512x512 bodies, 256x256 LOD `<name>0`), `<name>.ACT` = 256
  RGB triplets, `<name>.OPA` = same-size 8-bit plane with 0/128/255 levels. 128 covers painted body panels, so OPA is
  not treated as alpha (preview opaque, member snapshot retained); glass uses the Evo 2 MR policy (alpha 140 copy).
* **Catalog variants**: `<x>2`/`<x>4` = 2WD/4WD stock, `<x>42` = 17 and `<x>43` = 19 stock parts (prepared). The 18
  Sport Trac promo liveries are separate `.SMF/.RAW` pairs over the same 1933-triangle body (candidates for PAINT
  packages, not separate cars). F-150 Race has only the high stop lens `LightBC` (no LightBL/LightBR).

Pilots (keys = Evo 1 TRK names, author class T2, target EVO; SUV donor Pajero/audio 1, pickup donor Navara/audio 7);
all `PASS_SOURCE_OFF_STATE_EQUIVALENCE`; preview `.research-output/evo1-collection/evo1_collection.png`:

| Key | Vehicle | Donor | L | W | H | Wheel r |
|---|---|---|---|---|---|---|
| FEXCL43 | Ford Excursion Ltd (prepared) | Pajero | 5.94 | 2.34 | 2.18 | 0.40 |
| FEXDEB4 | Ford Expedition (stock, no prepared catalog) | Pajero | 5.20 | 2.35 | 1.86 | 0.38 |
| FEXPL4 | Ford Explorer Ltd (stock, no prepared catalog) | Pajero | 4.84 | 2.09 | 1.70 | 0.38 |
| FES2D43 | Ford Explorer Sport (prepared) | Pajero | 4.71 | 2.07 | 1.85 | 0.37 |
| FEST43 | Ford Explorer Sport Trac (prepared) | Navara | 5.36 | 2.15 | 1.88 | 0.38 |
| F150XCRW43 | Ford F-150 XLT SuperCrew (prepared) | Navara | 5.86 | 2.44 | 2.02 | 0.40 |
| F250XTSS4 | Ford F-250 XLT SuperCab (stock, no prepared catalog) | Navara | 5.88 | 2.39 | 1.84 | 0.40 |
| FF150TT2 | Ford F-150 Race Truck | Navara | 4.89 | 2.03 | 1.98 | 0.47 |
| PATHXE43 | Nissan Pathfinder XE (prepared) | Pajero | 4.76 | 2.04 | 1.84 | 0.37 |

Next: Evo 1 catalog paints (colorList recolouring needs the Evo 1 paint mask; candidate = OPA level 128 or palette
index ranges, unproven), Sport Trac promo liveries as a paint package, `full` kit for the three stock-only cars,
brake lamps via the Vehicle SDK Brake Glow-ON module (F-150 Race: high stop only), roster rebuild + EVO class.
