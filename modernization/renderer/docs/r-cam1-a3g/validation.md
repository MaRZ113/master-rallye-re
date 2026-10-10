# R-CAM1-A3g validation

## Automated

- Win32 x86 Release build: passed.
- Native CTest: 13/13 passed, including synchronized FOV projection and Freecam FOV/roll controller contracts.
- `python -m unittest discover -s modernization/renderer/tests -v`: 155 tests passed.
- `python -m unittest discover -s tests/synthetic -v`: 630 tests passed with `TEMP`/`TMP` set to `D:\Temp\MasterRallyeA3g`, outside the repository parent as required by the extraction-boundary test.
- `python -m compileall -q modernization`: passed.
- `verify_proxy.py`: passed; PE32/I386, required exports present, no recursive `d3d8.dll` import.
- `git diff --check`: passed.

## Build artifact

Generated ignored candidate: `modernization/renderer/.build-msvc/Release/d3d8.dll`; size **1,752,576 bytes**, SHA256 `549857b1a187b420fb21894d0709bfa3d78084686583287d44be0d5d6a875300`. It is not committed.

## Runtime

Not run by Codex. Human pause/race tests remain required for the cinematic lens and manual roll. Review [runtime handoff](runtime-handoff.md); no visual or gameplay PASS is inferred from code tests.
