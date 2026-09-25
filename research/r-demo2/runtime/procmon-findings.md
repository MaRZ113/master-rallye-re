# ProcMon trace findings — demo 9.3.1

All five user-supplied CSV files were parsed using the actual ProcMon schema: `Time of Day`, `Process Name`, `PID`, `Operation`, `Path`, `Result`, `Detail`, `Event Class`, and `Sequence`. Raw exports remain ignored. Semantic classification uses file events and initial probe results, never the human filename.

| Actual trace | ProcMon-derived result |
|---|---|
| `9_3_1_complete_miss_Trooper.CSV` | Source exists, DX initially missing; 23,473 GXM reads totaling 260,220 bytes; DX `Created`; 7,494 writes totaling 134,349 bytes; reopened and read in 7,494 matching offset/length pairs. |
| `9_3_1_complete_hit_Trooper.CSV` | Source missing (`NAME NOT FOUND`), DX exists; no source body read or DX writes; 8-byte header probe, then full read through EOF at 134,349. **SOURCE_MISSING_COMPILED_FALLBACK**. |
| `9_3_1_SOURCE-MISSING COMPILED FALLBACK_Trooper.CSV` | Both exist; initial GXM time `08.10.2001 14:43:00`, DX `03.10.2001 10:06:44`; 23,473 GXM reads/260,220 bytes; existing DX overwritten in place; 7,494 writes and matching reload traversal. **STALE_CACHE_REBUILD**. |
| `9_3_1_dx-newer_Trooper.CSV` | GXM time `08.10.2001 14:43:00`, DX `24.09.2026 21:34:13`; zero source reads, zero DX writes; 8-byte probe and full DX load. **FRESH_CACHE_HIT**. |
| `9_3_1_black_miss_Trooper.CSV` | GXI EOF 1,032, exactly two source reads (offset/length 0/8 and 8/1,024); DXT created and written in 261×4 bytes, then read in the same 261 pairs. **GXI_DXT_CACHE_MISS**. |

Evidence levels: all event order/count statements above are **CONFIRMED_BY_RUNTIME_TRACE**. The LastWriteTime freshness branch is **CONFIRMED_BY_CONTROLLED_RUNTIME_TRACE**. DXT byte identity for this asset is separately **CONFIRMED_BY_BYTES** in `dxt-regeneration.md`.

`tools/runtime/demo_procmon_extract.py` now parses real CSV exports, whitespace-grouped integers (including NBSP), timestamps, EOF, `NAME NOT FOUND`, access/disposition/OpenResult, and Query* events. `tools/runtime/demo_cache_trace.py` emits an event-derived state label and traversal comparison. Machine-readable summaries are deliberately ignored under `.research-output/r-demo2/procmon/`.

The 8-byte read pair maps to header values with additional static evidence: 9.3.1 code at VA `0x5466C9` compares the first DWORD to `0xD00D`; VA `0x5466F4` compares the second DWORD to `0x83` (131). The probe is therefore header magic/version validation in this observed DX reader (**CONFIRMED_BY_EXE**); it is not a complete cache-validity test. See `targeted-cache-xrefs.md`.

No additional broad cache capture is required for this phase. Equal timestamps and both source/cache missing were not tested and remain **UNKNOWN**.
