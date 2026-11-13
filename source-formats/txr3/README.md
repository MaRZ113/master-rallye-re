# Tokyo Xtreme Racer 3 / Shutokou Battle 01 (PS2, SLPM-65308, Genki 2003)

Owner target: **Isuzu VehiCROSS (UGS250)**. Status 2026-11-13: body geometry, UVs and
all 58 textures extracted and previewed; wheels, LODs and materials beyond the diffuse
texture are not decoded yet. Not imported into Master Rallye.

## Disc layout

ISO9660: `SLPM_653.08`, `BUILD.TOC` (542,196 bytes), `BUILD.DAT` (1,797,230,592 bytes,
LBA 637917), `MOV/` (PSS), `IRX/`.

### BUILD.TOC

| Offset | Meaning |
|---|---|
| 0x00 | u32 entry count (27109) |
| 0x04..0x37 | header fields (not needed for extraction) |
| 0x38 + 20*i | `u32 sector, u32 packed size, u32 sectors, u32 0, u32 unpacked size` |

Sectors are 2048-byte units **relative to BUILD.DAT**; 27,107 records cover sectors
445,739..877,553 contiguously. Sectors below 445,739 hold the sound region (not indexed
here). There are no file names.

### Compression

26,795 entries are `uclpack` containers: magic `00 E9 55 43 4C FF 01 1A`, BE flags,
method `0x2B`, level, BE block size, then blocks of `BE out_len, BE in_len, data`
(terminated by out_len 0). Method 0x2B here is **NRV2B with a 32-bit little-endian bit
buffer** (`ucl_nrv2b_decompress_le32`), not the 8-bit variant. 312 entries are stored raw;
one entry (#3) uses a different byte-flag LZ (not needed).

`tools/genki_unpack.c` (gcc -O2) unpacks every entry to `NNNNN.bin` + `index.tsv`
in ~25 s; all UCL entries decode to their declared size.

## Car data

* **Car table** = entry 26677: 119 records x 128 bytes: maker[20], model[32],
  body code[12], grade[44], then `i32 weight, displacement cc, rotary flag, ?, power PS`.
  VehiCROSS = record 53: `ISUZU / VehiCROSS / UGS250 / BaseGrade`, 1750, 3165 cc, 215 PS.
* **Car models** = entries 135..381, in pairs. The even entry is the car (section 0 model,
  section 1 TIM2 set, section 2 226-byte table); the odd entry is a nested container
  (variant data, not decoded). Order follows the body-code sort of the car table
  (dummy first, `1JAUM` Golf second ...); **VehiCROSS = entry 355** (confirmed by the
  ISUZU/VehiCROSS badge textures).

### Model section (`0IVX00.1` `LDMX00.2` `MRON00.2`)

* Object list, then material records: 16-byte header (texture index = byte +14),
  ambient / diffuse / specular vec4, `u32 0x32`, GS register words.
* Draw data are DMA/VIF packets. Every batch:
  `UNPACK V4-32 x4` (GIF tag + 3 qwords), `UNPACK V3-32` positions, `UNPACK V2-32` UV,
  `UNPACK V4-16` normals (w = 0x7FFF draws; other w = strip restart). One batch = one
  triangle strip.
* Units metres, +Y up. The data are **mirrored in X**; the exporter negates X and
  flips winding (badge text then reads correctly).

VehiCROSS: 1072 batches, 14,502 vertices, 12,358 triangles, 33 materials, 58 textures.

## Tools

| File | Purpose |
|---|---|
| `tools/genki_unpack.c` | BUILD.TOC/DAT unpacker (UCL NRV2B LE32) |
| `tools/txr3_model.py` | car container -> OBJ + MTL + PNG textures |
| `../common/tools/tim2.py` | PS2 TIM2 reader (4/8-bit CLUT with CSM1 unswizzle, 16/24/32-bit) |
| `../common/tools/textured_render.py` | z-buffered textured preview of OBJ+MTL |

Outputs (private, gitignored): `.research-output/txr3/`.

## Open

* Wheels: not part of entry 355; candidates are the small `03000000` containers
  (entries 393..19034) — to be identified.
* Odd companion entries (nested containers), section 2 table, alpha-tested cladding,
  light-flare quads (must be dropped for MR), LODs.
