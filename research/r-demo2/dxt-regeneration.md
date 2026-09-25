# GXI to DXT: clean runtime result

**CONFIRMED_BY_RUNTIME + CONFIRMED_BY_BYTES** for `demo-8.4.1:DataGx/Vehicles/Trooper/Black-tga.gxi` and its same-folder `black-tga.dxt`. The user supplied the clean runtime-regenerated file, kept under ignored `.research-output/r-demo2/input/`; `tools/scanner/r_demo_texture_compare.py` produced the ignored three-way report `.research-output/r-demo2/black-tga-three-way.json`.

| Copy | Size | SHA256 |
|---|---:|---|
| Shipped original DXT | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` |
| Offline GXI reconstruction | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` |
| Clean runtime regeneration | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` |

All complete bytes, the 20-byte header and payload agree. Header: magic `0x0000FEED`, version 1, CRC32 `0x6B3FE5F6` (valid), width 16, height 16. Payload SHA256 is `9503245a0161a939de15c2414db2d336e761822fa6cff8136e4148f58f1f782e`. The tested transformation is source top-down RGBA to bottom-up BGRA plus this header/CRC. The clean scratch miss and generated-file IO are independently confirmed by the 9.3.1 ProcMon capture; see `runtime/procmon-findings.md`. This 8.4.1 three-way byte comparison and 9.3.1 event trace are separate evidence. The 33 September font same-stem mismatches remain exceptions; this single runtime result does not override them.

## Runtime evidence closeout

The live Black-tga cache miss is now traced: GXI metadata size 1,032 bytes, two reads (8-byte header plus 1,024-byte 16×16 RGBA body), a newly created 1,044-byte DXT written in 261 DWORD writes, then reopened/read in the same 261 pairs. Cache order and immediate reload are **CONFIRMED_BY_RUNTIME_TRACE**. For this asset, shipped, offline-reconstructed and runtime-regenerated DXT are byte-identical at SHA256 `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` (**CONFIRMED_BY_BYTES**). This does not generalize to the 33 known September font mismatches.
