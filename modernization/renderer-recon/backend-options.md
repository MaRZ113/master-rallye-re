# Backend choice for the mapped Master Rallye workload

Preliminary recommendation (**STATIC_INFERENCE**): native D3D8 forwarding first
for stock parity and trace collection; keep D3D9 translation as the nearer migration
candidate, and D3D11 as a later candidate for renderer ownership. Backend is not final.
Master Rallye's mapped requirements are fixed-function texture combiners, FVF,
normal-generated 2D environment UVs, vertex fog, alpha cutouts/sorting, dynamic rings,
automatic depth and loss/reset; these must survive every choice.

| Choice | MR-specific burden | Future features / limits |
|---|---|---|
| Native D3D8 forwarding | lowest; preserve old caps/state/resource/reset behavior | good parity oracle/logging; sampleable depth/modern postFX not supplied automatically |
| D3D8 -> D3D9 | moderate adapter/resource/state translation; fixed function has a closer counterpart | practical shader/postFX route; depth sampling and parity still require deliberate design |
| D3D8 -> D3D11 | high; emulate FVF, lighting/material sources, fog/combiners/alpha test, D3D8 state blocks, pools/reset, legacy raster conventions | greatest direct control over shader, target/depth, shadow/postFX policy; high stock-parity cost |
| Vulkan | high unless adopting a separately validated compatibility backend | no MR evidence makes it preferable here; backend integration and debugging still substantial |

D3D11 uses a programmable graphics pipeline; reproducing this game's legacy stages
would require shaders and compatibility state translation. [Microsoft pipeline](https://learn.microsoft.com/en-us/windows/win32/direct3d11/overviews-direct3d-11-graphics-pipeline).
The existing d3d8to9 project translates D3D8 API/bytecode to D3D9, while its author
warns native-versus-translated behavior may differ by Windows/driver/settings,
including vsync. Its existence reduces exploration cost; it is not a Master Rallye
compatibility PASS. [Project source/README](https://github.com/crosire/d3d8to9).

For Windows compatibility, test the actual supported OS/GPU/runtime matrix rather
than infer support from API age. All options retain the same local d3d8 name/chain
coexistence problem. D3D11/Vulkan additionally need a clear child-resource ownership
model, loss emulation and caps policy. Shadows need draw replay/provenance; SSAO
needs depth; postFX needs scene/UI composition regardless of backend. No implementation
or dependency was added, and no generic API benchmark is claimed.
