# Correlating Debug messages with file access

Status: **PENDING**. No ProcMon trace or complete Debug session log has been supplied for this continuation. Visual equivalence after removing a DX file does not prove that DX was never opened.

For a short clean scratch demo 8.4.1 session, filter Process Monitor to the exact `MRallye.exe` PID and `CreateFile`, `ReadFile`, `WriteFile`, `QueryOpen` and `CloseFile`. Narrow paths to the scratch `DataGx/Vehicles/Trooper/` and relevant `.gxm`, `.dx`, `.gxi`, `.dxt`, `.gxb` extensions. Save the raw trace outside Git under ignored `.research-output/r-demo/runtime-logs/`; export timestamps, process/PID, operation, path, result and detail for only the relevant events.

Capture Debug output concurrently. For the clean DXT regeneration case, look for a `Black-tga.gxi` read, `black-tga.dxt` create/write/close and nearby `Reading GXI` / `Saved cached texture` messages. Use order and approximate timestamps; clock bases may differ. For the Trooper car/complete/wheel loader matrix, repeat only the minimum GXM+DX, GXM-only and DX-only cases on restored scratch baselines and record opened/read/written files beside the visible result.

| Case | Visual result from first pass | Debug messages | File opens/reads/writes | Interpretation |
|---|---|---|---|---|
| Trooper car GXM+DX / GXM-only / DX-only | Recorded in `loader-matrix.md`. | Pending. | Pending. | DX file-access role unknown. |
| Trooper complete GXM+DX / GXM-only / DX-only | Recorded in `loader-matrix.md`. | Pending. | Pending. | DX file-access role unknown. |
| Trooper wheel GXM+DX / GXM-only / DX-only | Recorded in `loader-matrix.md`. | Pending. | Pending. | DX file-access role unknown. |
| Trooper Black-tga GXI plus original/recreated DXT | Original/offline bytes match. | Pending. | Pending. | Runtime regeneration byte identity unknown. |

Summarize actual event sequences here after traces arrive. Do not infer `never opened`, `cache`, or `ignored` from missing visual differences alone.
