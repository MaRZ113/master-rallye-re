# CarSheet technical comparison

`demo-8.4.1:DataGx/Frontend/VehicleSelect/CarSheet.gxb` has the strict GXB image header `0x00013039`, dimensions 340 × 427, and exactly 580,720 pixel bytes. The same-build `CarSheet.tga` is 340 × 427, 32-bit uncompressed truecolor with bottom origin, 18 header bytes, and a 26-byte footer. Flipping GXB rows and swapping R/B yields the TGA pixel plane exactly (**CONFIRMED_BY_BYTES**).

`demo-9.3.1:DataGx/Frontend/VehicleSelect/CarSheet.gxb` is 340 × 569 (773,848 bytes total); no same-path TGA counterpart was found. The different dimensions and hashes document changed sheet content, but thumbnails alone cannot identify cars. Vehicle names in `cut-content.md` come from resource paths only.
