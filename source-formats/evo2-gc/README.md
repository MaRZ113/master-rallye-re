# 4x4 Evolution 2 (GameCube, GE4E7D) — exclusives vs PC

`tools/rvz.py`: minimal Dolphin RVZ reader (zstd groups, RVZ packing; junk regions
returned as zeros) + GameCube FST extraction; needs Python 3.14+ (`compression.zstd`).
The disc has 27 files; `TRUCK.pod` uses the same POD2/SMF/TIFF formats as the PC game
(readers in `../decoders/evo2_formats.py`).

## Roster difference (`tools/compare_trucks.py`)

PC `TRUCK.POD`: 150 TRK, 1126 members. GC `TRUCK.pod`: 152 TRK, 1242 members.

| GC-only TRK | truckName (as stored) | Model / textures | Class |
|---|---|---|---|
| `CFRT.TRK` | Calmini Nissan Frontier Race Truck (2001) | `CALMINI.SMF` (+ `CALMINI0` LOD), `CALMINI*.TIF` | Race Truck |
| `JWR.TRK` | Jeep Wrangler Rubicon | `JEEPWRGR.SMF` (+ LOD), `WRGRTIRE*` tyres | Compact SUV |
| `SMT.TRK` | "Vauxhall Frontera" (model field: Stillen Silverado Monster Truck) | `STILLEN.SMF` (+ LOD) | Race Truck |
| `WDRT.TRK` | Warn Dodge Dakota Race Truck | `WARN.SMF` (+ LOD) | Race Truck |

Also GC-only: the `31X10..44X15 MUD` tyre family (36 SMF + TIF). PC-only: two duplicate
Dodge Ram 1500 Regular Cab TRK variants (`DR1RS42/43`). `SMT.TRK` carries a stale
truckName; the geometry is the Stillen Silverado monster truck, not a Frontera.
`GCMODEL.POD` (track/world SMB models) and `PS2BIG.POD` (track textures) are not vehicles.

`tools/smf_export.py` exports any SMF to OBJ/MTL/PNG; previews are private in
`.research-output/evo2-gc/`.
