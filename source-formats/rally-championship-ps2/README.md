# Rally Championship (PS2, SLES-50763) — disc, HOG/WH, MAP, CAR

Source: `E:\RallyWorkshop_Sources\sources\Rally Championship PS2\Rally Championship (Europe) (En,Fr,De,Es,It,Sv).bin`
(MODE2/2352, one track). Extracted with `../total-drivin/tools/psx_iso.py` into
`.research-output/rally-championship-ps2/disc` (147 files).

## Key facts

* `SLES_507.63` (PS2 ELF, one PT_LOAD: file 0x1000 -> VA 0x100000, VA = file offset + 0xFF000,
  gp = 0x629A70) **keeps its STABS debug types**: `MapHeader`, `TRACK_DEFINITIONS`,
  `CSnowAnimator` (500 flakes, ground positions), `CRainAnimator` (700 drops, sound),
  `SURFACE_TYPE` (29 types incl. `ST_SNOW`, `ST_ICE`, `ST_PSEUDO_WET_*`), `TYRE_TYPE`
  (tarmac/gravel/ice/snow), the full `strings` enum. Types are readable with
  `strings -n 6 SLES_507.63 | grep <Name>:`.
* `TRACK_DEFINITIONS[]` (140-byte records) at VA `0x5FEAF0`: map file id, stage name, flag
  sprite, tyre type, flags (`0x10` rain, `0x02` snowfall), length (km, float), rally / stage
  index, string ids (description, surface, weather), source track name
  (`TRACKS\BANAnn.LWO.MEK`), fog colour / saturation far / near / sky / far distance, object
  sun base / amplitude, car reflection. Dump: `ps2_tables.py`.
* Map path: `sprintf("MAPS\STAGE%d\MAP%02d.HOG", id/10, id)` at `0x100F58`; `STAGEn` is only
  a file bucket (id / 10), not a country.
* HOG = `WART1.10` container (count, header 0x26, member name). `CARS\CARS.HOG` holds 132
  members; each map HOG holds one `MAPnn.DAT`.
* Map members are compressed with the **"WH" streaming codec** (`'W','H'` + u32 expanded size,
  bit buffer initialised to 0x80000000, 64 KiB ring at 0x462600). Decoder entry `0x19CA30`,
  output pointer `0x19C918`, state set at `0x19B894..0x19B8E4`. `wh_emulate.py` runs the game's
  own routine under Unicorn (MIPS64 LE; whole stream in memory, timer at 0x10000000 = 0), so no
  re-implementation was needed. All 34 maps decode to their declared sizes.
* `MAPnn.DAT`: `MapHeader` (headerSize 1704, version 20): checkpoints (16), start/finish lines,
  start positions/rotations, camera positions, sun normal, lo/hi colour, map origin, block map
  dimension, fog, draw distance, object models, faces (48-byte records), vertices (16-byte
  records, xyz float). Header offsets are relative to a load base; the vertex array is found by
  scanning (`compare_tracks.ps2_points`).
* `CARS\*.CAR` (27 cars, about 1.4 MB, 256x256 textures) and `M_CARS\*.CAR` (same 27,
  about 0.9 MB, 128x128 textures, multiplayer set) are **uncompressed** relocatable blobs: u32
  section count then offset/size tables. Mesh layout not decoded yet.
* `TWEAK0.PAR` holds per-car tweak blocks (`host0:Honda-Civic.twk`, `Physics.twk`,
  `Surfaces.twk`); source for physics mapping.

## Files

| File | Purpose |
|---|---|
| `wh_emulate.py` | decode a WH-compressed HOG member by emulating `SLES_507.63` (needs `unicorn`) |
| `ps2_tables.py` | dump `TRACK_DEFINITIONS[]` with resolved weather/surface strings |
| `compare_tracks.py` | PC `.map` vs PS2 `MAPnn.DAT` vertex-cloud comparison (heuristic, see report) |
| `topdown.py` | top-down point renders for visual checks |

Inventory and PC/PS2 comparison: [`../rcx/INVENTORY_PC_PS2.md`](../rcx/INVENTORY_PC_PS2.md).
