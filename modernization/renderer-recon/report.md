# R-GFX1 report

**STATUS: MORE WORK NEEDED.** Exact-image mechanisms are mapped; several semantic
owners and runtime behaviors remain open. [Validation](validation.md) evaluates
all28 requested criteria individually. R-GFX2 was not started.

**BRANCH:** modernization/renderer-recon.
**STARTING HEAD:** bd27cc1c12099b7062d251fa476fe62586ac4444, research/r-ui1;
clean preflight after user cleanup.

**PRIMARY BUILD:** external MRallye.exe, size3,121,214, ImageBase0x00400000,
SHA256 bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
PE timestamp2001-11-26T16:10:05Z; entry VA0x005C4602/RVA0x001C4602.
Sections/imported DLLs: [build identity](data/build.json).

All code addresses below are VA; RVA=VA-0x00400000. CONFIRMED_BY_EXE facts are
instruction/header evidence. Inferences, corpus evidence and unknowns are marked
in their linked topic files and [master map](data/renderer-map.json).

| Requested area | Result and evidence |
|---|---|
| D3D8 entry | Static d3d8.dll import; Direct3DCreate8(120) at0055905B, IAT0068F414. Linked assembler can dynamically resolve ValidateVertexShader/ValidatePixelShader; reachability open. DDRAW primary surface after D3D creation, GDI glyph rasterization, USER32 window/cursor dependencies. [entry](d3d8-entry.md) |
| Device creation | Owner0055AB90/API0055ACD7; selected adapter/type/focus HWND. Flags24/44/54 include MULTITHREADED. One DISCARD backbuffer, selected dimensions/format, auto-depth, flags0, refresh0, interval DEFAULT0. Fullscreen mode or windowed client/desktop sources; MSAA initialized NONE. [creation](device-creation.md) |
| Frame |005AFE30 ->00653080; clear0056BA1A before BeginScene0056BA23. Per camera: entity submission/group geometry flushes, opaque before alpha within each flush, shadows, trails, billboards, optional video. Immediate UI may interleave; deferred UI and late debug follow all cameras. EndScene0056CE60 ->Present0055B0DE. Semantic sky/terrain ordering open. [frame](frame-lifecycle.md) |
| Used APIs |224 reviewed sites:145 game/79 linked-helper; root11 identities, device23 game plus14 linked-only. Per-call VA/RVA, return VA/RVA, bytes, owner and receiver evidence. Full lists [vtable](device-vtable.md), [JSON](data/d3d8-callmap.json). Register dispatch/unanalysed code limits completeness. |
| Pipeline | Mapped major material/UI/particle paths are fixed function, with FVF passed to SetVertexShader. Real CreateVertexShader/CreatePixelShader/SetPixelShader not recovered; shader assembler code presence alone proves no programmable draws. [pipeline](pipeline-model.md) |
| Geometry | Concrete142/24-byte particle/UI/video; debug42/16 and62/20; linked RHW144/28. Derived base102/142, env112/152, noise202/242, water212/252. VB584960/IB5878F0, shared slices587070; static MANAGED and dynamic DEFAULT, ring NOOVERWRITE/DISCARD. Exhaustive active layouts open. [geometry](geometry.md) |
| Textures |005587E0 ->CreateTexture005589CD: MANAGED, Usage0, Levels0; alpha/depth/caps format preferences, A8R8G8B8 upload and mip filtering. Ordered handles/cache54ACD0 ->577620 ->SetTexture. Loose-first/Data.sma fallback reused from read-only research. Full decoding/eviction coverage open. [textures](textures.md) |
| Materials/cache |580360 family selector; setups5867A0/base,586150/env,585AC0/noise,5854D0/water,584EA0/particles. Alpha-test REF128/GREATER; base alpha SRCALPHA/INVSRCALPHA/write0; env alpha initially write1. Instance overrides can alter depth/fog. Env stage uses camera-space normals and two-coordinate transform. Cache570900 suppresses redundant setters. Old SetRenderState+F8 claim corrected to+C8 only here. [materials](material-state-map.md), [cache](state-cache.md) |
| Camera/world | Final view/projection5614A0; FOV helper4F2350 applies original linear angle*h/w rule, aspectcamera80/84; near0.2, far600/800/1000 or100000 branch. Packet interpolation583B90 ->WORLD561A40. Body/wheel matrices4F5440 read Physics/<entity>/Transform. Future freecam needs CPU culling/sky agreement and pause-input seam. [camera](camera-pipeline.md) |
| Lighting | Reviewed families LIGHTING0; packed model diffuse copied, generally texture/vertex-color driven. Default LIGHTING1 differs from effective family state. No receiver-confirmed native light/material calls; baked-light/source sun/ambient ownership open. blight lookup4CA110 is a material/controller lead. [lighting](lighting.md) |
| Fog | Common emission576970: linear vertex fog, sky palette color, start=end*(1-span), end300/400/500; span0.9 from sky initialization. Global parameter block plus per-instance enable; table/range defaults0. [fog](fog.md) |
| Sky |4B1180 selects Misc/Sky/cloudN/cloudsN and layerN; CloudNumber/Replay/Used and quality gates. Fifteen protected resources inspected; base/base_alpha derived, camera X/Z centering. Network0x00433EC0/0x004343C0 is not the complete local selection policy. Actual depth/order/live swap ownership open. [sky](sky.md) |
| Terrain/road | Shared indexed owner576970; bounds/hierarchy54C9D0 and frustum4F2380, option-driven visibility scalar. Terrain/road split, chunks/LOD/repetition and physical surface-to-material ownership open. Physical tag100 BSP is not assumed render batching. [terrain/road](terrain-road.md) |
| Vehicles | Entity/resource builder4B6A00 binds body/car and four wheel entities. Ordinary4F5440 and ghost/replay4C00D0 matrices converge on shared draws. Glass needs material provenance; damage mutation5892E0 and interior details still partial. Env stage is2D reflection. [vehicles](vehicle-renderer.md) |
| Vegetation | Generic alpha-test/blend/queue semantics mapped; foliage-specific caller/material binding open. A cutout state alone does not identify vegetation. [vegetation](vegetation.md) |
| Particles | Billboards5641C0, trails571EC0, stock projected shadows587DB0, dynamic142 and camera basis. Rain/spray rendering plausible; spawning/timing/contact triggers open. Surface.xml names tarmac/harddirt/grass/gravel/mud/water etc.;4DB5B0 registers properties, without GPU identity proof. [particles](particles.md) |
| UI |56D110 packet path, logical640x480 ortho, SRCALPHA blend, glyph/sprite textures. Immediate and deferred branches; shared HUD/frontend owner not fully split. Video56C0D0 and debug589880 distinct. Present-only postFX would include UI. [UI](ui-renderer.md) |
| Depth/targets | Auto-depth selected by format matches, ClearTARGET/Z, default LESSEQUAL; per-family/instance writes. Ordinary mapped path implies direct backbuffer. Linked D3DX RT/depth/Cube/CopyRects methods exist with unproved game reachability; whole-program offscreen absence unproved. [depth](depth.md) |
| Loss/reset |55AF50 TestCooperativeLevel: DEVICELOST skip; DEVICENOTRESET refresh/reset55AE40/55AE57. Pre55B410 ->567F60 clears dynamic resources; post55B450 reapplies cache/baseline. All compiled-slice/video recreation not yet closed. [reset](device-reset.md) |
| Capture/developer | No connected backbuffer-to-file screenshot path or working existing freecam established. Debug world/screen primitives mapped; semantic controls incomplete. [capture/debug](library-capture-debug.md) |
| Classification | Caller PCs identify billboards/trails/shadows/packet UI/video/debug paths. Shared indexed PCs cannot distinguish road/terrain/body/wheel/glass. Return-PC fields, resource and VB/IB slice identity, effective states/FVF/matrices are needed; retain UNKNOWN. [classification](draw-classification.md) |
| Proxy | CONDITIONAL local loading; minimum complete16/97-slot root/device ABI and native forwarding. Audit three export names, identity/refcounts/GetDevice escapes, raw children, loaded runtime, existing d3d8 wrappers, overlays/Wine. No proxy created. [feasibility](proxy-feasibility.md) |
| Backend | Native forwarding first for stock parity; D3D9 is a nearer translation candidate; D3D11 later if fixed-function/resource ownership emulation is justified. Backend not final. [options](backend-options.md) |

**FUTURE SEAMS:** per-pixel sun/specular/ambient MODERATE with normals and source
diffuse policy; shadow maps and SSAO HARD with reliable provenance/depth; modern fog
MODERATE; sky/time-of-day MODERATE but sun/ambient/exposure open; rain/spray MODERATE
with emitter/contact prerequisites; wet materials/headlights/night HARD; HD textures
MODERATE; freecam MODERATE, FOV EASY, photo mode HARD. Gamma/postFX need actual
scene/UI boundaries. [All26 ratings](modernization-seams.md) include addresses/why.

**RUNTIME VALIDATION STILL NEEDED:** full creation values, scene/target counts,
matrices, effective lighting/fog/depth/TSS, semantic draw identities, realized FVF,
optional helper reachability, UI boundary and reset recovery/visual stock parity.
[Handoff](runtime-handoff.md) provides scenarios and explicit PASS/FAIL.

**TOOLS:** exact-build read-only scan_d3d8.py; read-only ghidra_readonly.py using
installed exporter. **TESTS:** compileall and11 synthetic tests pass; reproducible
scanner JSON/TSV; JSON/link/fingerprint/scope checks pass. No runtime pass implied.

**GIT:** one local research commit; final SHA/status reported in the task response.
All tracked changes confined to this new directory; no push or game/database edit.
**NEXT RECOMMENDED PHASE:** R-GFX2 — Transparent D3D8 Proxy / Stock Rendering
Validation, after reviewing the remaining static gaps. STOP at this handoff.
