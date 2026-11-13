# Colin McRae Rally 04 (PC) - car formats (started 2026-11-13)

Owner target: **Mitsubishi Lancer Evolution VII** (`Data/Cars/MitLncr`). Cars: Audi, Cit2CV,
CitSaxo, Escort, FiatPunt, FocWRC, ForTran, Forr200, Golf, Lan037, LanSD, Mgb, Mgzr, MitLncr, MitPaj,
P205t16, P206, Puma, Sub22B, Sub44S, Xsara (+ shared `Textures/CSRefMap.dds`, `Specular`).

Per car: `<car>.P3D` (model), `<car>.big` (textures), `DamWheel.p3d`, `Shadow.P3D`, `feshadow.big`,
`Two_play/` (split-screen LOD copy).

## BIG (`BIGF`)

`'BIGF'`, u32 count, u32 alignment (0x800) x2, then 0x14 bytes, then entries
`char name[16]?`/`u32 size`, `u32 offset` (e.g. `EVOBod.dds` size 0x1555F0 at 0, `EVOBodB.dds`...).
Texture names: `EVOBod` body + `B`/`M`/`Du` variants (damage, dirt), `EVOGla*` glass with damage
stages, `EVOLit*` lamps (`on`/`of`), `EVOInt` interior, `EVODrive`/`EVOGlove`/`EVOFac*` crew.

## P3D (`CP3D`)

Header `'CP3D'`, u16 1, u8 7, u8 2, u32 body size; the body is a memory image whose pointers are
file offsets. Objects seen:
* transform nodes: 0x80-byte records with a 4x4 float matrix (identity rest pose);
* material records: pointer tables to NUL-terminated texture names (base + damage/dirt stages);
* mesh blocks: header (index count, sub-mesh count, ...), `u32 vertex_ptr` (= own offset + 12),
  `1, 0`, vertices 36 B (float pos[3], float normal[3], u32 colour, float uv[2]), then
  `u32 index_ptr`, `1, 0`, u16 indices = one triangle strip with degenerate joins.
  Body block (#62): 3579 vertices, 5686 indices, 58 sub-meshes (sub-mesh/material table: open).
* blocks repeat in groups (wheel LODs/damage states first, body later); 173 vertex buffers.

`tools/cmr04_p3d.py` lists blocks and decodes strips (index count heuristics; sub-mesh table and
material binding not decoded yet). Units: metres, +X length (body -2.0..1.98), +Y up, Z width.

## Open
Sub-mesh table (58 ranges -> material), node hierarchy (wheels, doors, damage parts), which group
is LOD0, BIG entry layout check, DDS formats.
