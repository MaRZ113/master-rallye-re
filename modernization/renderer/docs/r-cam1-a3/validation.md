# R-CAM1-A3 validation and handoff boundary

Status: **`BLOCKED_ON_POST_TRAVERSAL_RESTORE`**. The DLL below contains automatic
R-UI1 carousel closeout and the existing read-only camera diagnostics. It is not
a functional Freecam candidate.

## Repository and scope

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`.
- Branch: `master`; starting HEAD: `23941fe108f8bd4c21338736145783a5fbc15e70`.
- Preflight: clean; status, branch, last 20 commits and diff-check inspected.
- UI closeout commit: `7e866d7` (`fix: enable validated carousel alignment by default`).
- All stage source/documentation/test changes are under `modernization/renderer/`.
- No branch/worktree created; retired worktrees untouched; no push or game deployment.
- Proprietary EXE/assets and existing Ghidra databases were read only.

## Automated results

| Check | Actual result | What it establishes |
|---|---|---|
| Isolated UI focused Python | 24/24 PASS | Automatic policy and previous quality evidence contracts |
| Isolated UI canonical native build/CTest | 10/10 PASS | UI closeout builds and preserves native regressions before camera research |
| Final canonical Win32 Release build/CTest | 10/10 PASS; 4.69 s CTest | Existing renderer/native regression contracts |
| Full renderer Python suite | 126/126 PASS; 112.424 s | Existing 121 contracts plus 5 new static-scope scanner tests |
| Scope tests after final particle anchors | 5/5 PASS | Final scanner anchors, malformed/unknown-build rejection and output boundary |
| Pristine scope inspector | PASS; 17 byte anchors | Exact traversal return, late camera-builder/particle pose dependencies and narrowed scene candidates |
| Fresh Ghidra queries | 19 curated function exports | Read-only instruction evidence; no saved analysis transaction |
| Compileall | PASS | `python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization/renderer` |
| PE verifier | PASS | PE32, I386, DLL; required export ordinals; no recursive D3D8 import |
| `git diff --check` | PASS | Whitespace validation |

Full Python execution used a writable ignored renderer `TEMP`/`TMP`. No old test
assertion was weakened. Final scanner changes were limited to the additional
particle dependency anchors and corresponding focused assertions.

The fresh query requested `0x00562420`, but that export returned the overlapping
function entry `0x00562810`. It was excluded from curated evidence. No claim is
made that the returned decompiler types describe `0x00562420`.

## Build identity

DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll` (ignored).

- SHA256: `7badff0e671a95395a8058ebe207ed0a65d73da955368dcc31aff422fe8b4ab2`.
- Size: **1,597,440 bytes**.
- PE32, I386 (`0x014C`), DLL.
- Exports: Direct3DCreate8 ordinal 5, ValidatePixelShader ordinal 2,
  ValidateVertexShader ordinal 3.
- Imports: bcrypt.dll, USER32.dll, KERNEL32.dll. No d3d8.dll import.

## Handoff

Findings: [camera scope and race ownership](findings.md).
Reproducible byte map: [camera-scope-map.json](../../research/r-cam1-a3/camera-scope-map.json).
Fresh exporter instruction digests: [ghidra-evidence.json](../../research/r-cam1-a3/ghidra-evidence.json).

Reproduce the static map:

```powershell
python modernization/renderer/tools/inspect_camera_scope.py `
  'D:\Game\Master Rallye Pristine\MRallye.exe' `
  --output modernization/renderer/research/r-cam1-a3/camera-scope-map.json
```

Clean changed-source archive (ignored):
`modernization/renderer/.analysis/archives/r-cam1-a3-source-20261010.zip`.
It includes both isolated UI closeout and this camera investigation, without
DLL/PDB/OBJ, game assets, raw logs or reverse databases.

No Freecam flight, controls, focus/mouse restoration, native replacement bridge,
pose restoration or Freecam/frustum coherence test is claimed. Those tests have
no implementation to exercise yet. Source45/Source90 observations and successful
UI runtime acceptance remain separate from those missing proofs.

Next narrow verification is the candidate complete-camera end at `0x006532E9`,
including late consumers and scoped restore. A persistent read-only offline
France1 race gate also remains required. Do not use the DLL for a first-flight
handoff, enable imaginary Freecam options, or begin teleport/HUD-hide/photo work.
