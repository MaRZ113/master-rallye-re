# Master Rallye renderer — R-GFX3-1

Status: **READY_FOR_SHORT_RETEST**. Native D3D8 forwarding with independently configurable, default-off Classic+ experiments. Pre-fix default-off, shadow and pristine Reset human results are recorded. Final MIN-only AF and preview-exclusion fixes require the short retest.

Work in `master-rallye-re-general`, branch `research/general-re`. Historical `modernization/renderer-recon` and `modernization/d3d8-proxy` are frozen. [Implementation](research/r-gfx3/implementation.md), [validation](research/r-gfx3/validation.md), [human handoff](research/r-gfx3/runtime-handoff.md).

`MRRRenderer.ini` is read beside the proxy DLL once per process. Copy `MRRRenderer.ini.example` and change individual features between game launches. Missing/unsupported-version config means Stock. Unknown EXE always means Stock forwarding with optional tracing. Supported EXE SHA256: bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.

Features: stage0 LINEAR MIN anisotropy (MAG stays stock) with device caps; vertical FOV30..110 on the observed source90 race projection family; dedicated stock shadow Stock/Off. Stage1 environment mapping, mip filtering and point filtering stay stock. No backend translation, lighting, freecam, texture replacement or EXE patches.

```powershell
python modernization/renderer/tools/build.py
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll
python -m unittest discover -s modernization/renderer/tests -v
python -m compileall modernization/renderer
```

Build products/captures are ignored. Logs are beside the DLL under `MRRRenderer/logs`. F10 retains one complete frame. [Trace/state conventions](research/r-gfx3/state-virtualization.md) explain logical state and effective overlays. Offline R-GFX2 readers remain available; `tools/summarize_visual_trace.py` reconstructs both versions.
