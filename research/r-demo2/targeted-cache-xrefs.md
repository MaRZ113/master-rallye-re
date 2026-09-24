# Targeted GXM cache-path EXE xrefs

Read-only PE32 string/xref and bounded objdump inspection of unchanged demo `MRallye.exe` files. Virtual addresses use image base `0x400000`. The apparent combined Debug text is emitted by separate `Caching disabled.` or `Cached model out of date, missing or invalid format.` and `Reading GXM: [%s]` log calls. The two builds have closely parallel code, but runtime behavior differs.

| Build | `Caching disabled.` literal / push | `Reading GXM: [%s]` literal / push | Containing GXM path | Immediate caller |
|---|---|---|---|---|
| 8.4.1 | VA `0x5F4818` / `0x520CE3` | VA `0x5F4928` / `0x520CF5` | `0x520BB0` | `0x520902` |
| 9.3.1 | VA `0x673644` / `0x51F273` | VA `0x67375C` / `0x51F285` | `0x51F140` | `0x51EE92` |

At 8.4.1 `0x520CD5–0x520CE8` and 9.3.1 `0x51F265–0x51F278`, a byte field at object offset `+8` selects between the two cache-status literals. Each path then logs `Reading GXM` and `Making dx model for moModel named : [%s]`. The immediate callers first invoke the GXM path and, on a null return, invoke a second function (`0x520E60` in 8.4.1; `0x51F3F0` in 9.3.1). This is **CONFIRMED_BY_EXECUTABLE** control-flow evidence of a source path plus fallback path, not a proof of which file each function opens in a given run.

Both functions construct model-related paths and compare two values before that status branch: 8.4.1 around `0x520C5E–0x520C7B`, 9.3.1 around `0x51F1EE–0x51F20E`. A timestamp/freshness check is plausible, but the called functions and value representation have not been identified sufficiently to claim a timestamp rule. The paired code shape alone does not identify whether the build difference is a global, configuration value, command-line argument, or a changed caller. A controlled ProcMon cache invalidation matrix is required.

The major cooker-stage strings (`Vertex welder`, `Building convex hull`, `Building BSP tree`, `Building cylinder`, `Parsing 2d geometry`, `Building land database`, `Inserting object nodes`, `Optimising model`) occur in both EXEs. This proves retained diagnostic code, not that all stages run in each build or resource. No executable was patched.
