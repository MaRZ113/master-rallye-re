# GXP image container (R-DEMO)

The November demo contains 38 `.gxp` files, all under `DataGx` and mostly frontend backgrounds. Every one passes the same strict eight-byte image structure as GXI/GXB: `u32 0x00013039`, `u16 width`, `u16 height`, then exactly `width * height * 4` bytes. This is **CONFIRMED_BY_CORPUS** for `demo-9.3.1`.

No direct same-stem TGA or DXT counterpart was found. However, 31/38 GXP files have 146 same-stem-plus-index DXT tiles, all reproduced byte-identically by rectangular top-down RGBA to bottom-up BGRA conversion with zero-filled padding and CRC32 headers. Seven GXP files have no such tile set. See `research/r-demo/gxp-dxt-tiles.md` and `gxp-dxt-tiles.json`. This is **CONFIRMED_BY_BYTES** for the paired files; GXP's runtime loading and tile-generation behavior remain **UNKNOWN**. A separate `gxp.py` API retains the extension identity rather than silently equating it to GXI or GXB.
