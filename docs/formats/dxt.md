# `.dxt` format notes (R0)

Status: **CONFIRMED** uncompressed texture wrapper; channel naming is **HIGH**.

Despite the extension, these files are not DDS containers and do not contain
DXT1/DXT3/DXT5 block payloads.

## Layout

| Offset | Representation | Interpretation | Confidence |
|---:|---|---|---|
| `0x00` | `ED FE 00 00` / `uint32 0xFEED` | magic | **CONFIRMED** |
| `0x04` | `01 00 00 00` / `uint32 1` | constant; possibly version | **CONFIRMED** value / **LOW** meaning |
| `0x08` | varying `uint32` | unknown identifier/hash/checksum candidate | **UNKNOWN** |
| `0x0C` | `uint32 W` | width | **CONFIRMED** |
| `0x10` | `uint32 H` | height | **CONFIRMED** |
| `0x14` | `W * H * 4 bytes` | one uncompressed 32-bit pixel plane | **CONFIRMED** |

Archive-wide evidence: all 6,960 files have magic `0xFEED`, word `1`, and exact
size `20 + W*H*4`. Observed dimensions range over rectangular and square power-
of-two combinations from 4/8-pixel axes through 256. There are no trailing bytes
for stored mip levels. Runtime-generated mipmaps remain possible but untested.

## Targeted examples

- Astero `glass-tga.dxt`: header width/height 32x32; file size 4,116 =
  `20 + 32*32*4`; alpha is 255 for all 1,024 pixels.
- Astero `asterowheelrim-tga.dxt`: 16x16; file size 1,044.
- Astero `asteropanels128-tga.dxt`: 128x128; file size 65,556.
- Astero `asterowheel64-tga.dxt`: 64x64; file size 16,404.
- Astero `asterolight1-tga.dxt`: 32x32; all pixels have non-opaque alpha and
  there are 209 distinct alpha values.
- Astero `windscreen32-tga.dxt`: 32x32; all pixels have non-opaque alpha and
  there are 66 distinct alpha values.

The fourth byte is the alpha channel: its variation agrees with sidecar
`HasAlpha/UsesAlpha=Yes` for light/windscreen textures and remains 255 in the
opaque samples. **HIGH**.

The first three payload bytes are most likely BGRA order. Brake-light samples
have average channels `(105.1, 102.4, 251.9)` and `(5.1, 17.6, 127.9)`, making
the third stored byte the semantic red channel. This is **HIGH**, not promoted
to absolute confirmation without an independent known-color reference.

## Prototype

`tools/prototypes/dxt_decode.py` validates the header/size and writes PNG. It
requires the caller to select/accept channel order (`bgra` default, `rgba`
alternative). No decoded copyrighted texture is stored in the repository.

## Unresolved

- meaning/derivation of word `0x08`;
- vertical origin (top-down versus bottom-up) under the renderer;
- whether runtime sampling treats color channels linearly or as sRGB;
- whether word `1` is a version, type, or flags field.
