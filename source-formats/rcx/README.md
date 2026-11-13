# Rally Championship Xtreme (PC) — RCX/QTO/TEX

Migrated 2026-11-13 from the owner-local research folder
`E:\RallyWorkshop_Sources\exclusive_research` (code and reports only; no extracted
game payloads). Source executable `Rally.exe` SHA-256
`efc94948966ffe14b5dcfef6ea2b712db6f1e817b044dd0823c7425fa231a355`.

## Summary of the 2026-10-31 feasibility study (originally in Russian)

* `Data/Cars` holds 56 RCX archives: 28 cars, each with a normal and an `_arcade`
  variant. All start with `c6 5e 0b b0 04 00 00 00`.
* `Data/CarStats` holds 29 binary `.cog` files and one `.bin`; physics semantics are
  not decoded.
* RCX is a compressed archive; the decoder at `Rally.exe` VA `0x4829c0` (called from
  `0x45d437..0x45d471`) is reimplemented in `rcx_extract.py`. All 56 archives /
  3032 entries decode to their declared sizes.
* Members: QTO v7.2 meshes (57-byte draw records, fixed vertex stream), MSH part
  records (62 x 136 bytes, affine matrices), TEX v1 textures (A8R8G8B8, X8R8G8B8,
  DXT1, DXT3 + mips), `collision_xmesh.edg`, `damage_xmesh.qto`.
* Astra pilot: 62 QTO + 22 TEX pass structural checks; see `ASTRA_PILOT_STATUS.md`
  and `ASTRA_GATES_REPORT.md`. Not yet runtime-tested in Master Rallye.

## Files

| File | Purpose |
|---|---|
| `rcx_extract.py` | bounded RCX archive decoder |
| `qto_inspect.py` | QTO mesh parser and diagnostic OBJ |
| `tex_decode.py` | TEX decoder |
| `inventory_rcx.py` | archive census |
| `rcx_scene_adapter.py` | Astra -> universal vehicle scene (needs `master_rallye` from `research/vehicles`) |
| `test_rcx.py` | synthetic tests; set `RCX_ASTRA_PATH` for the real-corpus test |

Car list: Astra, Citroen Saxo, Escort Maxi, Ford Puma, Ford Puma SP, Hyundai Accent,
Lancer Evo5, Lancer Evo6, Mini Cooper, Nissan Micra, Peugeot 106, Proton Compact,
Seat Cordoba, Seat Ibiza, Skoda Octavia, VW Golf, Audi Quattro, Ford Focus,
Honda Civic, Hyundai Coupe, Lancia Stratos, Peugeot 206, Renault Megane,
Skoda Felicia, Subaru Impreza 98 / 00 / 00sun / 01.
