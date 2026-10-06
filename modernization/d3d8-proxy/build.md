# Win32 build and verification

Build tested on2026-10-05 with Visual Studio18 BuildTools (18.5.11709.299), MSVC
19.50.35729 / toolset14.50.35717, Windows SDK10.0.26100.0, CMake4.4.3 and Python3.14.
MSVC x86, SDK headers/libs and CMake are prerequisites; no download is performed.
The project uses /MT, C++17, /EHsc and /fp:strict, with research PDB/MAP and /Brepro
linking. Required DLL imports are bcrypt/USER32/KERNEL32 only; no MSYS2, CRT DLL,
D3D8/D3D9/D3D11 dependency. No bit-for-bit reproducibility promise is made across
toolchain versions/absolute build paths or repeated debug-information rebuilds;
the actual artifact is hashed after each build.

From `D:\Game\Master Rallye\master-rallye-re`:

```powershell
python modernization/d3d8-proxy/tools/build.py
python modernization/d3d8-proxy/tools/verify_proxy.py modernization/d3d8-proxy/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/d3d8-proxy/tests -p 'test_*.py' -v
python -m compileall modernization/d3d8-proxy
git diff --check
```

`build.py` configures Visual Studio18 2026 with `-A Win32`, builds Release, runs
the native CTest target and propagates failure. `--generator 'Visual Studio 17 2022'`
allows another installed MSVC generator; that configuration is untested. The
normalizer removes PATH/Path environment duplicates observed in the app-launched
shell that otherwise caused MSBuild MSB6001. It changes only the child build
environment, not permanent system settings. Build output paths must be ignored
`.build*` directories inside this folder.

Direct equivalent commands in a normal developer shell:

```powershell
cmake -S modernization/d3d8-proxy -B modernization/d3d8-proxy/.build-msvc -G 'Visual Studio 18 2026' -A Win32 -DBUILD_TESTING=ON
cmake --build modernization/d3d8-proxy/.build-msvc --config Release
ctest --test-dir modernization/d3d8-proxy/.build-msvc -C Release --output-on-failure
```

The vendored header's anonymous D3DMATRIX union emits MSVC C4201; mock QI's
unused parameters can emit C4100. These are understood declaration/mock warnings,
not errors. They do not alter calling convention or structure size.

`generate_interfaces.py` deterministically regenerates full declarations,
ordinary forwarders, mock ABI invocations and the manifest from the pinned
header. Run it only after an intentional declaration change; its outputs are
checked in. Native tests are GPU-free synthetic mocks. They write ignored
synthetic frames under `.build-msvc/Release/MRRGFX2/logs`, which are not game data.
Python tests inspect their valid/completed/truncated output after the native run.

Deliverable is `.build-msvc/Release/d3d8.dll`; PDB/MAP remain alongside it for
research. [proxy-build.json](data/proxy-build.json) identifies the verified local
binary, but is not a proprietary binary or runtime log. Reverify the SHA after
any rebuild; source-only commit intentionally omits every compiled product.
