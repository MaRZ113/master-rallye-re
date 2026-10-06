# R-GFX2 — transparent native D3D8 proxy

**READY FOR HUMAN RUNTIME.** Source, Win32 build, mock COM forwarding and offline
trace checks are complete. Stock rendering parity has **not** been tested in the
game. Follow [runtime-handoff.md](runtime-handoff.md); R-GFX3 remains unopened.

The load chain is `MRallye.exe → local d3d8.dll → Windows system d3d8.dll`.
The proxy forwards the complete 16-slot IDirect3D8 and 97-slot IDirect3DDevice8
interfaces. All graphics arguments, HRESULTs and resource pointers go through
unchanged; root/device identity uses documented COM plumbing. No new draws,
overlays, shaders, backend translation, assets or executable patches are added.

Build from the repository root:

```powershell
python modernization/d3d8-proxy/tools/build.py
python modernization/d3d8-proxy/tools/verify_proxy.py modernization/d3d8-proxy/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/d3d8-proxy/tests -p 'test_*.py' -v
python -m compileall modernization/d3d8-proxy
```

Output: `.build-msvc/Release/d3d8.dll`. Build products and captures are ignored.
The DLL has **not** been copied beside the installed game by this task.

Default tracing records startup/create/reset/resource metadata and periodic
counts. F10 arms the next complete Present-to-Present interval, writes one JSONL
frame and stops. Releasing F10 allows another capture. All logs are relative to
the proxy, under `MRRGFX2/logs/`. Optional `MRRGFX2.ini` can disable instrumentation.

| Evidence / use | Document |
|---|---|
| Final scope and limitations | [findings](findings.md), [validation](validation.md) |
| Build prerequisites, artifact verification | [build](build.md), [build manifest](data/proxy-build.json) |
| Loader, threading, failure isolation | [architecture](architecture.md) |
| Complete COM ABI, parent lifetime | [COM identity](com-identity.md), [interface map](data/interface-map.json) |
| Exports and signatures | [exports](exports.md) |
| Why resources currently stay raw | [child-resource audit](child-resource-audit.md) |
| Observational state and engine cache constraint | [state-cache safety](state-cache-safety.md) |
| Capture schema, tools, bounds | [trace format](trace-format.md) |
| Human observations and static comparisons | [runtime handoff](runtime-handoff.md), [comparison](static-runtime-comparison.md) |

All R-GFX1 and earlier research is read-only input. Corrections and later runtime
observations belong in this folder. The target is pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
An unknown executable still receives generic forwarding, but the offline tools
disable every game-specific address interpretation.
