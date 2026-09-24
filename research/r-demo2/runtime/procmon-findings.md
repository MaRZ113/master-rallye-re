# ProcMon cache file order: pending trace

ProcMon is installed locally. No filtered capture has been supplied yet, so **no file-access order is confirmed**. Keep raw PML/CSV under ignored `.research-output/r-demo2/procmon/` and commit only a derived summary.

Filter to the actual scratch demo `MRallye.exe` process (PID plus scratch executable path if multiple copies exist), then include `CreateFile`, `ReadFile`, `WriteFile`, `QueryOpen`, `SetEndOfFile`, and `CloseFile`. Filter paths to the one exact tested `car`, `complete`, `wheel`, or `Black-tga` resource pair; avoid global system activity. Capture from before triggering the load until the resource appears or the game exits. Export CSV with event timestamp, process/PID, operation, path, result and detail.

Minimal runs: (1) 9.3.1 `complete.gxm` present / `complete.dx` absent (cache miss); (2) `complete.gxm` absent / generated `complete.dx` present (DX fallback); (3) wheel GXM-only and DX-only, visual behavior already established; (4) clean GXI present / DXT absent. Record the **actual** open/read/write order and any DebugView lines; `GXM read → DX create/write → DX load` is a hypothesis until captured. Later test GXM newer, DX newer, equal times, and either file missing in separate scratch states to determine invalidation policy.

After a filtered CSV export is placed under the ignored R-DEMO2 tree, `tools/runtime/demo_procmon_extract.py --input <csv> --output <ignored-json> --path-fragment complete. --pid <PID>` extracts only matching MRallye CreateFile/ReadFile/WriteFile/QueryOpen/SetEndOfFile/CloseFile events. Inspect actual `Result` and `Detail`; a CreateFile event alone is not proof that the complete file was read. The tool is synthetic-tested but not yet exercised on a live ProcMon export.
