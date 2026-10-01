# R5T-F.2.1 — human runtime handoff

Status: **READY_FOR_TREE_TAG1400_RUNTIME_TEST**. These are two new isolated Demo 9.10.0 runtime clones. No runtime result is claimed until the user tests them.

## Exact staged files

- Hybrid T runtime: `research-output\r5t_f21\runtime\hybrid-t\runtime`
  - DX SHA256: `51db114245db76de54a27c21cd8cb5ec1041850b4b91c35b1c381e36dcb919da`
  - EXE SHA256: `13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78`
  - RaceTest France1 XML SHA256: `6048ed26c78118f3f82d9ddbcaf4f75c6655b24d805189d3cf3bd772202dc0df`
- Hybrid U runtime: `research-output\r5t_f21\runtime\hybrid-u\runtime`
  - DX SHA256: `de656fdab5fed3c6186e11ef13d00e1da127852ce3572f1b0d861a56985b3561`
  - EXE SHA256: `13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78`
  - RaceTest France1 XML SHA256: `6048ed26c78118f3f82d9ddbcaf4f75c6655b24d805189d3cf3bd772202dc0df`
- Non-target files checked byte-identical across clones: 2862

Each clone differs only in `DataGx/Course/France1/france1.dx`; its RaceTest XML is at `DataScene/RaceTest/France1.xml`. Start `MRallye.exe` from that clone’s runtime directory and select France1. The two clones use the same non-DX runtime tree.

## Expected setup invariants

Both hybrids have fixed P from baseline (`4c9aef8897b9f368d34fcb88c6b3f628f5c308475ae38de697afbef657472316`), fixed S (`6d1b2294af455aa0f8dbfa5501cf8750fade73caee96a4a1d14eb74bbb374c84`), and fixed R (`39b8c55ad30d931bf459df380a05cecf72db0b2c805a86b6efc18e68d22df680`). T and U donor hashes are listed in `swap-manifest.json`. Both parse as revision 135; render arrays and draw batches validate; tag100, tag1339, tag1400, and tag1500 boundaries reach EOF exactly.

## Test each hybrid

At the known support locations, record OLD collision and NEW invisible collision independently. Also record course load, visible finish support location, FinishArea/RACE COMPLETE location, and any anomalies.

- OLD location (baseline): approximately `(-1471.7653, 68.4258, 352.5542)`.
- NEW location (modified): approximately `(-1451.7653, 68.4258, 352.5542)`.
- Hybrid T contains modified T and baseline U. Does collision occur at OLD or NEW?
- Hybrid U contains baseline T and modified U. Does collision occur at OLD or NEW?
- FinishArea and visible finish geometry should remain unchanged in either case.

## Decision guide (apply only after results)

- T=NEW and U=OLD: tag100 tree alone determines the tested physical state in this pairing.
- T=OLD and U=NEW: tag1400 carries or controls the tested state.
- Either fails to load or neither location behaves normally: report cross-section dependency or other anomaly; do not force a carrier conclusion.
- Both NEW or both OLD: first verify selected clone, file hash, and coordinates before interpretation.

F.1 remains a full-suffix result. This probe does not generalize tag100 semantics, prove BSP semantics, or establish tag1400 meaning.
