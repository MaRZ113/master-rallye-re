# texFinder legacy inventory

## Scope and disposition

The recovered archive was inspected read-only. It contains 4,003 files: 2,385
PNG, 1,243 DXT, 90 TXT, 83 DX, 83 MTL, 82 OBJ, 16 Python, two ZIP, one CSV, and
one JSON file. No file from the archive was copied into production source.

The large DX/DXT/TXT trees are original or reconstructed game material. The
PNG/OBJ/MTL trees are derived game assets. Both classes remain external and are
**GAME_ASSET_DO_NOT_COMMIT**. The ZIP files remain external because they contain
duplicate scripts and/or game-derived material.

## Useful components

| Legacy component | Purpose / I/O | Important assumptions | Relationship to modern project | Classification / disposition |
|---|---|---|---|---|
| `master_rallye_clean_dx_to_obj.py` | vehicle DX -> OBJ/MTL | heuristic draw scan, first UV set, legacy UV flip | Used only to reproduce v1/v3 experiments; modern `dx.py` is more complete and authoritative | **VERIFIED_USEFUL** as historical experiment driver; **OBSOLETE** as canonical parser |
| `master_rallye_clean_dxt_converter.py` | DXT -> PNG/TGA | FEED header, raw 32-bit plane, selectable channel/row policies | Its BGRA plus vertical-row mode agrees with modern evidence | **VERIFIED_USEFUL**; behavior reimplemented, code not vendored |
| `master_rallye_clean_png_to_dxt.py` | PNG + same-size DXT template -> DXT | preserve 20-byte header; RGBA -> BGRA; bottom-up rows; optionally resizes | Six diverse legacy round trips were byte-identical; modern safe writer forbids resize | **VERIFIED_USEFUL** concept; code not vendored |
| `master_rallye_clean_obj_to_dx.py` (v1) | OBJ + original DX template -> patched DX | same vertex count; patches known arrays; preserves topology/table bytes; optional footer update | Establishes the safe template-patch principle. Default UV/footer behavior is not byte-preserving | **VERIFIED_USEFUL** principle; implementation remains reference only |
| `master_rallye_clean_obj_to_dx_v2.py` | donor OBJ shape projected onto template topology | nearest-vertex / nearest-surface transfer; template topology retained | Possible future experimental authoring helper, not a serializer | **USEFUL_HYPOTHESIS** |
| `master_rallye_clean_obj_to_dx_v3.py` | rebuild vertex/index buffers and record ranges | clean complete/wheel layout, 40-byte footer, legacy global-index order | Modern parser reads its Astero result but rejects it; conflicts with proven winding/local addressing | **CONTRADICTED**; do not migrate |
| `master_rallye_clean_blender_materials_v2.py` | OBJ material reconstruction | names, helper slots, TXT alpha flags, white-pixel heuristics | Useful hypothesis catalogue only; runtime semantics remain unknown | **USEFUL_HYPOTHESIS** |
| `master_rallye_clean_blender_hot_swap_textures.py` + README | replace/reload preview textures in Blender | ad-hoc directory and object conventions | UX ideas may inform a later canonical writer UI | **HISTORICAL_ONLY** |
| beta profile scripts V2/v6/v7/v8 | evolving Pajero/livery experiments | hard-coded profiles and manual Blender state | Superseded by v9; names are not format truth | **OBSOLETE** / **HISTORICAL_ONLY** |
| `master_rallye_clean_beta_profiles_v9.py` | Pajero body/wheel profile switching | hard-coded inferred red/blue/yellow/hybrid branches | Preserved as asset-archaeology hypotheses | **USEFUL_HYPOTHESIS** |
| `master_rallye_collect_unused_vehicle_textures.py` + README | scans and copies/moves candidate unused textures | known sidecar aliases; “unused” inferred from references | Destructive/copy modes are inappropriate; modern `audit-textures` is read-only | **USEFUL_HYPOTHESIS**, legacy behavior not integrated |
| root `master_rallye_dxt_converter.py` | earlier DXT preview conversion | older orientation/channel experimentation | Superseded by clean converter and modern `dxt.py` | **HISTORICAL_ONLY** |
| root `tool_TextureFinder.py` | generic Noesis Texture Finder | third-party provenance/licensing not established | Not required by current tooling | **THIRD_PARTY_REFERENCE**; do not vendor |
| README/audit/CSV/JSON notes | historical observations | may mix verified facts and assumptions | Used only to identify reproducible experiments | **HISTORICAL_ONLY** |
| `MR_useful-scripts.zip` | duplicate legacy bundle | archive provenance and duplicate state | No reason to vendor | **HISTORICAL_ONLY** |
| `Original-Vehicles.zip` and all DX/DXT/TXT assets | source/game data | copyrighted external corpus | Modern tools read local user-owned copy only | **GAME_ASSET_DO_NOT_COMMIT** |
| all PNG/OBJ/MTL outputs | decoded/reconstructed game assets | derived from game resources | Validation output only | **GAME_ASSET_DO_NOT_COMMIT** |

## Conclusions

The archive is useful as a source of experiments, not authority. The modern
parser and corpus evidence remain canonical. No generic Texture Finder code,
legacy parser, Blender shader script, game asset, or derived conversion output
was vendored.
