# GXB image container (R-DEMO)

All 40 GXB files in `demo-8.4.1` and all 42 in `demo-9.3.1` pass the same strict eight-byte structural layout as GXI (`0x00013039`, u16 width and height, exact RGBA32-sized payload). The API remains separate because common bytes do not prove a common loader role. Retail has no GXB files in the supplied corpus.

Five same-directory, same-stem GXB/TGA pairs exist. Three have exact pixel equivalence after vertical row reversal and RGBA-to-BGRA channel swap. Both supplied TGA files that differ are `demo-9.3.1` font resources (`Mrallye`, `Silly`); their mismatch is recorded, not resolved by a different build's asset.

`demo-8.4.1:DataGx/Frontend/VehicleSelect/CarSheet.gxb` matches its TGA pixels exactly. The TGA uses 18 header bytes, a 32-bit uncompressed truecolor image with bottom origin, and a 26-byte footer. See `research/r-demo/carsheet.md`.

Evidence: structure **CONFIRMED_BY_CORPUS**; conversion **CONFIRMED_BY_BYTES** for matching pairs; runtime role **UNKNOWN**.

The first-pass Trooper loader tests do not test GXB. Its runtime loading path remains **UNKNOWN**; the Debug/file-access protocol will include `.gxb` where relevant.
