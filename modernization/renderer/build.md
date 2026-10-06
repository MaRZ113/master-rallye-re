# Win32 build

MSVC x8619.50.35729, VS18 BuildTools, Windows SDK10.0.26100.0, CMake4.4.3. Run `python modernization/renderer/tools/build.py` from the repository root; it configures Win32 Release and runs CTest. Native contracts are GPU-free typed mocks; no game executes. Source-defined exports: Direct3DCreate8@5, ValidateVertexShader@3, ValidatePixelShader@2. Explicit Windows system loader; no d3d8 import recursion.

DLL is `.build-msvc/Release/d3d8.dll`; identity is in `data/build.json`. No byte-identical relationship to historical R-GFX2 is claimed. Generated files, native logs and binaries remain ignored. Header notices/licenses and exact pinned header hashes are retained. Compiler warnings C4201 are the unchanged SDK anonymous struct; C4100 occurs in generated mock QI parameters.
