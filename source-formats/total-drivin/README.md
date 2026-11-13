# Total Drivin' / Car and Driver Presents: Grand Tour Racing '98 (PS1, Eutechnyx 1997)

Owner target: **Citroën ZX Rallye Raid** (Dakar class). Status 2026-11-13: containers,
compression and car geometry decoded; textures decoded (td_texture.py); wheels are parameter records;
the ZX is one of the four Dakar models (candidates DAKAR1/2 and DAKAR7/8, owner to confirm
from previews). Not imported into Master Rallye.

## Disc (Europe, SLES-00307, MODE2/2352 track 1)

`tools/psx_iso.py` (trivial ISO9660 walk on 2352-byte
sectors, user data at +24) extracts: `SLES_003.07` (PS-X EXE), `INTRO.COM`,
`CLUMP0..5.COM` (one per language), `ARDONE.BIN` / `ARDSS.BIN` (race overlays, Oberon-2
modules), `LEVELS.DAT` (72.7 MB), `ARDS*.STR`, `INTRO.STR`.

## Compression (`tools/td_lzw.py`)

Reimplemented from SLES_003.07 `0x800168D0`. Chunk = `u32 packed, u32 unpacked,
i32 literal_bits, LSB-first bit stream`. `literal_bits = 8`: flag bit 1 -> dictionary code
(+256), flag 0 -> 8-bit literal; `literal_bits = -1`: plain LZW starting at 9 bits.
256 = reset, 257 = end, dictionary 0x102..0xFFF. Next chunk at `offset + 4 + packed`.
`.COM` files are chunk sequences (CLUMP0: frontend data 0.5 MB, 0.1 MB, frontend module
1.7 MB, then an uncompressed tail).

## LEVELS.DAT

Table of 56 records `(u32 0, u32 offset, u32 size)`; each level = 3 chunks:
terrain/texture data, VRAM upload records (`u16 x, y, w, h` + pixels; high bit of h marks
another record type, not decoded), and the object chunk (track, cameras, cars).
Every level carries the 8 cars of its class: `<CLASS><n>` (BODY + 4 wheel records),
`<CLASS>A<n>` / `<CLASS>B<n>` LODs. Classes: RALLY, BUGGY, SPORTS, INDY, DAKAR.
DAKAR cars: levels 10-13, 15 (ISLAND3-6, B), 43-45, 47 (DESERT4-6, B), 52 (HONGKON7).
Cars are unlicensed (no maker names in the data).

## Object node (`tools/td_model.py`)

`name[32]`, `u8 kind` (3 = mesh, 2 = wheel record), `i32 position[3]`,
`i32 rotation[9]` (4096 = 1.0), `u16, u16, i16, u16 vertex count, u16`, vertices as
packed `u32` (x signed 10 bits, y signed 11, z signed 11; x2 to match the following
`i16 bbox[6]`), 20-byte face records (`i16 normal[3], i16 d, u16 flags, u16 material,
u32 colour/texture id, u32 first corner`), `u32 corner count`, corners
`(u8 vertex, u8 texture page/CLUT, u8 u, u8 v)`. DAKAR bodies: 116-140 vertices.

## Textures (`tools/td_texture.py`, decoded 2026-11-13)

VRAM chunk records: `u16 x, y, w, h`; h bits 14-15 = kind (2 = CLUT row, 0/1 = pixel rect);
the records tile the chunk exactly (level 10: 679 records). Car material table follows the
`<CLASS><n>` name: header (RGB of the flat body colour at +0x24, entry count at +0x20), then
28-byte entries `u16 page_code, u16 clut, u32 E2 window` x2 (one per frame buffer) + `u32 type`.
Types: 8 textured 4-bit, 0x10 textured two-state (brake lamps: buffers differ), 1 body colour,
2 trim, 0x0a glasshouse. `clut` is the standard PS1 CLUT word (matches the CLUT records exactly);
`page_code >> 3` = 4-bit page x index on the y = 256 row (the race code copies the material word
straight into the GT3/GT4 tpage/clut fields: ARDONE.BIN 0x96D8); the E2 window picks the livery
copy inside the page. Face record u32 +12 = material entry; corner u32 = vertex | lighting index
<< 8 | u << 16 | v << 24. Record normals are not consistently outward.

The 8 DAKAR cars share one body with different liveries on pages 8-11. Owner: ZX = DAKAR1 (red)
or DAKAR2 (blue/white). Wheel records (kind 2): position + radius 54, no mesh.

## Open

Lighting table (corner byte 1), exact scale to metres (pilot scales to the donor wheelbase).
