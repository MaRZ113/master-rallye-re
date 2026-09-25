# Targeted GXM cache-path EXE xrefs

Read-only PE32 string/xref and bounded objdump inspection of unchanged demo `MRallye.exe` files. Virtual addresses use image base `0x400000`. The apparent combined Debug text is emitted by separate `Caching disabled.` or `Cached model out of date, missing or invalid format.` and `Reading GXM: [%s]` log calls. The two builds have closely parallel code, but runtime behavior differs.

| Build | `Caching disabled.` literal / push | `Reading GXM: [%s]` literal / push | Containing GXM path | Immediate caller |
|---|---|---|---|---|
| 8.4.1 | VA `0x5F4818` / `0x520CE3` | VA `0x5F4928` / `0x520CF5` | `0x520BB0` | `0x520902` |
| 9.3.1 | VA `0x673644` / `0x51F273` | VA `0x67375C` / `0x51F285` | `0x51F140` | `0x51EE92` |

At 8.4.1 `0x520CD5–0x520CE8` and 9.3.1 `0x51F265–0x51F278`, a byte field at object offset `+8` selects between the two cache-status literals. Each path then logs `Reading GXM` and `Making dx model for moModel named : [%s]`. The immediate callers first invoke the GXM path and, on a null return, invoke a second function (`0x520E60` in 8.4.1; `0x51F3F0` in 9.3.1). This is **CONFIRMED_BY_EXE** control-flow evidence of a source path plus fallback path. Actual 9.3.1 source/cache behavior for the tested resources is established separately by controlled ProcMon traces; see `runtime/procmon-findings.md`.

Both functions compare values before that status branch: 8.4.1 around `0x520C5E–0x520C7B`, 9.3.1 around `0x51F1EE–0x51F20E`. In 9.3.1, controlled ProcMon timestamp cases establish the observed source-newer rebuild and DX-newer direct-load behavior. The bounded static helper meaning and the 8.4.1 freshness rule remain **UNKNOWN**; do not infer those from parallel code shape. The full tested 9.3.1 result is in `model-cache-state-machine.md`.

The major cooker-stage strings (`Vertex welder`, `Building convex hull`, `Building BSP tree`, `Building cylinder`, `Parsing 2d geometry`, `Building land database`, `Inserting object nodes`, `Optimising model`) occur in both EXEs. This proves retained diagnostic code, not that all stages run in each build or resource. No executable was patched.

## R-DEMO2.1 cache-decision xrefs (read-only)

At 9.3.1 VA `0x51F1EE–0x51F20E`, the model-source path calls helper `0x5FD700` twice, compares one returned value to the other plus `0x14`, and stores the greater-than result before selecting the cache-status diagnostic branch at `0x51F265`. The imported API table includes `GetFileInformationByHandle`, `FileTimeToLocalFileTime`, `FileTimeToSystemTime`, `FindFirstFileA`, and `GetFileAttributesA`; it does not import `GetFileTime` or `CompareFileTime` by those names. The relevant helper's exact value meaning and its relationship to `LastWriteTime` remain **UNKNOWN** from this bounded analysis. Runtime controlled timestamps independently confirm that source-newer rebuilds and DX-newer loads.

The 8-byte DX probe now has a direct reader interpretation. In the 9.3.1 stream reader around VA `0x5466BD–0x546713`, two 4-byte reads through the stream vtable (`+0x44`) are individually checked for success. The first DWORD at `0x5466C9` is compared with `0xD00D`; the second at `0x5466F4` is compared with `0x83` (decimal 131). ProcMon observes reads `(offset 0,length 4)` and `(offset 4,length 4)` in the separate probe handle. This supports **CONFIRMED_BY_EXE** magic/version validation for the probe. It is not proof of general cache freshness or complete-file validity.
