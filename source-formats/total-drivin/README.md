# Total Drivin' / Car and Driver Presents: Grand Tour Racing '98 (PS1, Eutechnyx 1997)

Owner target: **Citroën ZX Rallye Raid** (Dakar class). Status 2026-11-13: containers,
compression and car geometry decoded; textures (VRAM records) and wheels not yet decoded;
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

## Open

VRAM record format (texture pages + CLUTs), wheel records (kind 2), scale to metres,
confirming which DAKAR model is the ZX.
