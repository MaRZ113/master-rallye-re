# GXI to DXT: clean runtime result

**CONFIRMED_BY_RUNTIME + CONFIRMED_BY_BYTES** for `demo-8.4.1:DataGx/Vehicles/Trooper/Black-tga.gxi` and its same-folder `black-tga.dxt`. The user supplied the clean runtime-regenerated file, kept under ignored `.research-output/r-demo2/input/`; `tools/scanner/r_demo_texture_compare.py` produced the ignored three-way report `.research-output/r-demo2/black-tga-three-way.json`.

| Copy | Size | SHA256 |
|---|---:|---|
| Shipped original DXT | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` |
| Offline GXI reconstruction | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` |
| Clean runtime regeneration | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` |

All complete bytes, the 20-byte header and payload agree. Header: magic `0x0000FEED`, version 1, CRC32 `0x6B3FE5F6` (valid), width 16, height 16. Payload SHA256 is `9503245a0161a939de15c2414db2d336e761822fa6cff8136e4148f58f1f782e`. The tested transformation is source top-down RGBA to bottom-up BGRA plus this header/CRC. Actual cache decision and file API order still need ProcMon/DebugView. The 33 September font same-stem mismatches remain exceptions; this single runtime result does not override them.
