# R-UI1 Validation Record

## Repository and scope

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`
- Branch: `master`
- Starting HEAD: `007138f` (`research: validate camera submission ownership for R-CAM1-A2`)
- Final HEAD: recorded with the R-UI1 commit.
- The pre-existing staged Observatory files were present before R-UI1 and were left untouched.
- All R-UI1 source, test, and documentation changes are under `modernization/renderer/`.
- No proprietary executable, game asset, runtime log, generated DLL, PDB, OBJ, LIB, or EXP file is part of the tracked change.

## Automated validation

- `python modernization/renderer/tools/build.py`: passed; Win32 Release DLL and test targets built, then all CTest targets ran.
- Native CTest: 10/10 passed, including the production UI wrapper and new R-UI1 packet/draw diagnostic contract.
- `python -m unittest discover -s modernization/renderer/tests -v`: 119/119 passed.
- `python -m compileall -q modernization/renderer`: passed.
- Proxy verification: valid PE32 / I386 DLL; required D3D8 exports present; no recursive `d3d8.dll` import; evidence grade `BUILD_VERIFIED_NOT_RUNTIME`.
- `git diff --check`: passed.

The verified build output is `modernization/renderer/.build-msvc/Release/d3d8.dll`, 1,556,480 bytes, SHA256 `655510f5c74bb1ffd82f2f9d41fc7ce5106d5008315d408b40f874b4966611fe`. It remains ignored build output and is not committed.

## Runtime boundary

No game session was run as part of this validation. The synthetic test establishes that the existing retained-anchor policy can produce the supplied paired-transform displacement shape; it does not prove carousel ownership or visual correction. Race Select and Vehicle Select testing remains pending. The required short test sequence and capture fields are in [runtime-handoff.md](runtime-handoff.md).

The current R-CAM1-A2 camera submission diagnostic, GameFov behavior, foliage upload provenance, and broader D3D8 frame capture passed their existing tests and were not redirected or removed. Exclusive Fullscreen behavior and the unrelated staged Observatory changes remain outside R-UI1.
