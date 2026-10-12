# R-CAM1-A3h.1 validation

Static and synthetic validation is complete; live game observation is pending.

| Check | Result |
|---|---|
| Renderer Python unittest suite | 160 tests passed |
| Root synthetic suite (`PYTHONPATH=src`) | 630 tests passed |
| Win32 Release native CTest | 13/13 passed |
| `python -m compileall -q modernization` | passed |
| PE/export/import verifier | valid PE32/I386 DLL; required exports found; no recursive `d3d8.dll` import |
| `git diff --check` | passed |
| Human normal + paused F10 runtime pair | pending |
| HUD/PauseMenu Egg-to-draw owner proof | unresolved; not claimed |

The CTest quality suite includes the bounded UI ownership scope nesting, identity mutation, unknown packet mode, capture-local rearm, overflow and pass-through draw contracts. The race epoch suite additionally tests typed optional bool reads for valid values, missing keys and wrong types without a write path. Analyzer tests cover shared/paused-only tuple reporting, same-session validation, overflow/truncation, owner-name mapping, and optional typed pause-state signal handling.

The generated DLL is intentionally not committed. See [build-manifest.json](build-manifest.json) for its local path, hash, size, PE identity and exports.
