# R-CAM1-A3f.2 validation

## Automated

- Win32 x86 Release build: passed.
- Native CTest: 13/13 passed, including the expanded Freecam clock contract suite.
- `python -m unittest discover -s modernization/renderer/tests -v`: 155 tests passed.
- `python -m unittest discover -s tests/synthetic -v`: passed.
- `python -m compileall -q modernization`: passed.
- `verify_proxy.py`: passed; PE32/I386 DLL, expected exports, no recursive `d3d8.dll` import.
- `git diff --check`: passed.

## Build artifact

Generated ignored candidate: `modernization/renderer/.build-msvc/Release/d3d8.dll`; size **1,743,872 bytes**, SHA256 `a9c222218e5cc4ef323addb6898cd23aa78fe476420f6502f68c940a45c7049c`. It is not committed.

## Runtime status

Not run by Codex. R-CAM1-A3f.2 is ready for the short user comparison described in [runtime handoff](runtime-handoff.md). Native clock tests establish arithmetic and lifecycle safety, not visual smoothness in Master Rallye.
