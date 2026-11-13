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
Built from the GC `TRUCK.pod` into `.research-output/evo2-collection/<key>-scene|pilot`. Results: see the table
added below after the batch.
