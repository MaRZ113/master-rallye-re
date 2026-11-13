# Source formats (other games -> Master Rallye)

Branch `research/source-formats`: format research and standalone readers for the games
in the owner-local corpus `E:\RallyWorkshop_Sources` (games, tools, earlier research).
Only code and reports live here; extracted game data stays in `.research-output/`
(gitignored) or outside the repository.

The import pipeline (Universal Vehicle Scene, Workshop, native DX writers) stays on
`research/vehicles`; copies of its format readers are kept in `decoders/` for reference
(source commit `research/vehicles` 34fc9bc, 2026-11-13).

| Folder | Game | State |
|---|---|---|
| `common/` | corpus-wide audits (format matrix, tool audit, smoke/priority probes), shared tools | migrated |
| `dakar2/` | Dakar 2 (Xbox / GC / PS2) | migrated; Pajero, Nissan in MR (T4 pilot) |
| `evo2/` | 4x4 Evolution 2 (PC) | migrated; 4Runner in MR |
| `michelin/` | Michelin Rally Masters | migrated; RAV4 in MR |
| `paris-dakar/` | Paris-Dakar Rally (PC) | migrated; Pajero Silver in MR |
| `rcx/` | Rally Championship Xtreme | migrated from `exclusive_research`; Astra pilot |
| `txr3/` | Tokyo Xtreme Racer 3 (PS2) | new: container + model + textures, VehiCROSS extracted |
| `CLASSES.md` | class map (T4 = trucks) | owner decision 2026-11-13 |
| `total-drivin/` | Total Drivin' / Grand Tour Racing '98 (PS1) | new: LZW, levels, car geometry; textures open |
| `evo2-gc/` | 4x4 Evolution 2 (GameCube) | new: RVZ reader, 4 GC-only vehicles extracted |
| `decoders/` | reference copies of the research/vehicles source readers | migrated |

Not migrated on purpose: third-party Noesis scripts (`E:\RallyWorkshop_Sources\tools\research-pinned`,
no licence), extracted payloads, private previews, import/MR-specific pipeline code.
