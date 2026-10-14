# Vegetation deployment audit — 2026-10-14

Status: CONFIRMED_BY_BYTES deployment mismatch; runtime appearance remains user-observed.

All 72 existing private derived grass/shrub assets are present under `ps2-research/pc-port/.assets/grass/` and reproduce the committed source registry hashes. The game's configured `PS2Grass/` directory contains only 6 assets: Turkey3, France1 and ItalyS1, two categories each. The remaining 66 assets, covering 33 course pairs, are missing. No deployed asset hash mismatch was found. The installed proxy DLL equals the current reflection-coverage-fix build (`abf005f8ff2f9535a2abb644e2066a224fc389734dc5f36fbdec5694ff37f48a`).

This explains the exact three-course pattern without changing coordinates, density, culling or admission. The current game INI already selects `GrassMode=2`, `ShrubsMode=2` and `GrassAssetDirectory=PS2Grass`; a Mode 1 limitation is not the cause.

## Source path and admission

- `renderer/grass_pilot.cpp:177-180`: Mode 2 enables the multi-course branch, Mode 1 is Turkey3-only.
- `renderer/grass_pilot.cpp:187-196`: primary Turkey3 category asset must verify first.
- `renderer/grass_pilot.cpp:197-206`: other course assets are read from the directory once at construction; missing files are ignored and their `course_ready_` entry remains false.
- `renderer/grass_pilot.cpp:233`: course selection requires the exact admitted course ID and a ready asset. Missing course assets fail closed, rather than borrowing Turkey3 positions.
- `renderer/grass_native_integration.hpp:30`: verified live course certificate remains mandatory. No certificate weakening is needed.
- `overlay/patches/0001-renderer-integration.patch:731`: existing `ps2_grass_config` logs a literal requested_mode=1 and effective_mode as boolean. Thus the observed startup record is not trustworthy evidence that the user selected Mode 1; the INI and loader establish Mode 2. This report does not modify that patch or infer a new live draw from its startup record.

## Smallest correction — manual user action

No loader code change is required. Close the game. Manually copy **all 72** existing `.ps2grass` files from:

`D:/Game/Master Rallye/master-rallye-re-general/ps2-research/pc-port/.assets/grass/`

to the configured:

`D:/Game/Master Rallye Pristine/PS2Grass/`

Keep the verified current INI settings. Start a new process; resources are read at construction, so adding files after launch does not reload them. Do not replace the stock course files, change global texture paths or copy one course under another name. Generated texture-bearing assets remain private and excluded from Git/handoff archives. No automatic deployment was performed.

First runtime check: France2 with fixed camera near an original grass-bearing surface, then Italy1, Spain1 and Turkey1. Compare GrassMode/ShrubsMode 0 versus 2, then return to Turkey3 and test restart/menu performance. Full resources indicate source coverage, not independently confirmed gameplay coverage; some camera regions naturally have no detail source.

## Evidence and reproducibility

`deployment-inventory.json` contains all expected names/hashes, source point counts and local/deployed readiness; no mesh or image payload. Snapshot totals: 72 local verified, 6 deployed verified, 66 missing, 113814796 local bytes. `test_deployment_inventory.py` checks consistency with the independent committed full-coverage registry, unique names, complete category coverage and the observed three-course deployment.

The original renderer, implementation, staged integration patches, game assets and build roots were not changed by this audit. Latest session logs have only two grass startup records and no grass draw events; they also contain malformed legacy race records. No malformed JSON was silently repaired or upgraded to runtime draw proof.
