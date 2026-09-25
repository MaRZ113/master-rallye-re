# Historical Debug/file-access correlation plan

Status: **HISTORICAL; superseded in part by R-DEMO2.1**. The visual loader matrix alone still cannot prove whether a DX was opened, read, or used by another subsystem. R-DEMO2.1 added real ProcMon evidence for 9.3.1 model cache miss/build, source-missing compiled fallback, stale rebuild, fresh hit, and GXI→DXT miss; it also added a separate 8.4.1 DebugView stage capture. See `research/r-demo2/runtime/procmon-findings.md` and `debugview-findings.md`.

The 9.3.1 cache traces are not a per-resource access matrix for the earlier 8.4.1 car/complete/wheel visual tests. For those exact 8.4.1 cases, DX open/read/use status remains untested. The same caution applies to other resources and builds not named in the trace findings. No blanket `never opened`, `cache`, or `ignored` conclusion follows from visual equivalence.

The original proposed filter was the scratch `MRallye.exe` PID, `CreateFile`, `ReadFile`, `WriteFile`, `QueryOpen`, and `CloseFile`, restricted to the relevant scratch `DataGx/Vehicles/Trooper/` paths. This protocol is retained as historical documentation, not an active R-DEMO2.1 gate. Later work should first state which build and exact unresolved path it targets.

| Case | Evidence now available | Bounded conclusion |
|---|---|---|
| 8.4.1 Trooper car/complete/wheel GXM+DX, GXM-only, DX-only visual matrix | Human visual results in `loader-matrix.md`; no corresponding per-resource ProcMon matrix in R-DEMO2.1 | Visual roles are recorded; exact DX file access/use remains untested |
| Trooper Black-tga GXI/DXT byte identity | Three-way 8.4.1 byte comparison in `research/r-demo2/dxt-regeneration.md` | Runtime output bytes equal shipped/offline bytes for this asset |
| GXI→DXT cache miss event order | Separate 9.3.1 ProcMon capture in `research/r-demo2/runtime/procmon-findings.md` | Source/cache events confirmed for the named tested path |
| 9.3.1 model cache branches | Five ProcMon exports and controlled timestamp cases | See `model-cache-state-machine.md`; both-missing/equal-time remain unknown |
