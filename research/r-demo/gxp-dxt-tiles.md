# GXP to tiled DXT correspondence

Corpus: `demo-9.3.1`. GXP files: 38; DXT tile candidates: 146.

Candidate rule: same folder and case-insensitive `<GXP stem>_000_NNN.dxt` with contiguous numbering. Tiles are laid left to right until their widths cover the source width, then continue on the next row. The source rectangle is converted from top-down RGBA to bottom-up BGRA within each tile; unused right and top tile pixels are zero. Complete DXT headers and CRC32 are checked.

| Status | GXP files |
|---|---:|
| all_tiles_byte_identical | 31 |
| no_same_stem_tiled_dxt | 7 |

## GXP without same-stem DXT tiles

- `demo-9.3.1:DataGx/Frontend/Backgrounds/BG_DemoEnd.gxp`
- `demo-9.3.1:DataGx/Frontend/Backgrounds/BG_Title.gxp`
- `demo-9.3.1:DataGx/Frontend/Backgrounds/BG_Title2.gxp`
- `demo-9.3.1:DataGx/Frontend/Backgrounds/BG_VehicleSetup_Suspension.gxp`
- `demo-9.3.1:DataGx/Frontend/Topbars/ControllerSelect.gxp`
- `demo-9.3.1:DataGx/Frontend/Topbars/Language.gxp`
- `demo-9.3.1:DataGx/Frontend/Topbars/RaceSelect.gxp`

This is **CONFIRMED_BY_BYTES** for the paired files and does not establish whether the game generates or loads the tiles at runtime. Per-file source and tile SHA256, dimensions, offsets, and comparison status are in `gxp-dxt-tiles.json`.
