# GXI image container (R-DEMO)

Evidence: **CONFIRMED_BY_CORPUS** for the common structural variant. Targeted demo EXE xrefs confirm a `.gxi` source/cache branch (**CONFIRMED_BY_EXE**); clean Trooper runtime DXT regeneration is now byte-identical to shipped and offline bytes (**CONFIRMED_BY_RUNTIME + CONFIRMED_BY_BYTES**).

Little-endian layout:

| Offset | Field |
|---:|---|
| 0 | `u32 0x00013039` |
| 4 | `u16 width` |
| 6 | `u16 height` |
| 8 | exactly `width * height * 4` pixel bytes |

The strict reader is `src/master_rallye/gxi.py`, shared byte-layout code is in `gx_image.py`. It rejects zero dimensions, truncation, and trailing bytes. The pixel bytes behave as top-down RGBA in paired conversions: reverse rows and swap R/B to obtain the observed DXT bottom-up BGRA payload. This interpretation is **CONFIRMED_BY_CORPUS** for exact pairs; it is not a claim about the game renderer.

- `demo-8.4.1`: 2,045 of 2,046 GXI parse. `DataGx/Test/Jump.oldf/Jump2562-tga.gxi` declares dimensions inconsistent with its file length and is retained as an anomaly.
- `demo-9.3.1`: 677 of 677 GXI parse.
- `retail`: no GXI files in the supplied corpus.

For same-directory, same-stem GXI/DXT candidates, 1,124/1,157 in 8.4.1 and 326/326 in 9.3.1 regenerate byte-identically using the DXT header `(0xFEED, 1, CRC32(BGRA payload), width, height)`. All 33 8.4.1 mismatches are under `DataGx/Fonts`; some have different dimensions. A matching name alone does not prove current semantic identity. See `research/r-demo/resource-pairs.json` for each pair.

For the controlled `demo-8.4.1:DataGx/Vehicles/Trooper/Black-tga.gxi` pair, the original and offline reconstructed DXT SHA256 are both `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82`. The clean runtime-generated copy has the same SHA256 and complete bytes; see `research/r-demo2/dxt-regeneration.md`.
