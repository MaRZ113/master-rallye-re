# Targeted demo EXE loader evidence

This is a read-only byte-string survey, not a call-graph reconstruction. Offsets below are file offsets of literal strings in `MRallye.exe`, not function addresses.

| Literal | demo-8.4.1 offsets | demo-9.3.1 offsets | retail offsets |
|---|---|---|---|
| `.gxm` | `0x1F20FC`, `0x1F2129` (`*.gxm`) | `0x2737A8`, `0x27CCE1` (`*.gxm`) | `0x2E8CD8`, `0x2EBFDD` (`*.gxm`) |
| `.gxi` | `0x1F336C`, `0x1F5B7A`, `0x1F5BCE` | `0x2735F4`, `0x27ECFE`, `0x27ED4E` | `0x2E8E14`, `0x2F4ED6`, `0x2F4F26` |
| `.gxb` | `0x1F4860` | `0x273694` | `0x2E9E88` |
| `.gxp` | absent from this literal search | `0x273684` | `0x2E9E78` |
| `.dxt` | `0x1F4A90` | `0x2735EC` | `0x2E8E0C` |

The little-endian DXT magic `ED FE 00 00` occurs three times in each EXE; the GX image magic `39 30 01 00` was not found as a literal four-byte sequence. Neither observation identifies a loader function or proves file-access order. Retail retains extension literals despite no GXI/GXM/GXB/GXP assets in its supplied corpus. Precise xrefs and function addresses require a targeted disassembly or ProcMon trace and remain open.

A continuation found targeted executable xrefs, immediate callers, `.gxi`/`.dxt` branch code and the 8.4.1 `OutputDebugStringA` sink. See `runtime/targeted-exe-xrefs.md`. The table above remains a literal-string inventory only.
