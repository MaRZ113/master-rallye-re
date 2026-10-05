# R-GFX2 handoff: observations and explicit PASS/FAIL

No runtime instrument was built in R-GFX1. This is a specification for the next
phase, not a runtime result. Use a separate game copy and preserve the pristine
EXE/assets. Record EXE SHA, runtime/wrapper chain, OS/GPU, mode/options, track/car,
camera and whether race/frontend/replay/video/debug is active for every capture.

Smallest useful next instrument: native forwarding of IDirect3D8/Device8 with
bounded logs; unchanged arguments/results/state and raw resource pointers.
Log module load paths, requested exports/SDK, CreateDevice/Reset full parameters,
caps/format-check results, cooperative HRESULTs, BeginScene/EndScene/Present/Clear,
VIEW/PROJECTION/WORLD/viewport, relevant render/TSS states, shader creation/FVF,
resource creation and draws. A draw record needs return PC normalized to MRallye
module RVA, frame/camera sequence, primitive parameters, bound VB/IB/stride/FVF,
texture pointers, effective cached states and current matrices. Do not log only
setter deltas: cache suppression means draws need reconstructed effective state.
Match the return PC to callmap `return_rva`; `rva` names the CALL instruction and
can differ by2,3 or6 bytes. Preserve the module identity for helper/overlay callers.

| Observation | PASS for static claim | FAIL / required correction |
|---|---|---|
| loader/creation | native runtime path is explicit; SDK120; PP/flags correspond to mapped source branches | different root/export/flags or unresolved loader chain |
| ordinary frame | Clear3 before BeginScene; paired EndScene/Present; per-camera owner sequence matches | additional scene/target lifecycle or different ordering |
| transforms | width/height-derived aspect and stock linear angle rule; near0.2 and expected far branch | different producer/matrix/clip branch |
| fixed function | FVF bindings, no actual shader creation on sampled scenarios | real vertex/pixel shader or unclassified handle |
| lighting | mapped families unlit; no unexplained native light/material use | SetLight/LightEnable/SetMaterial or other lighting owner |
| fog | linear vertex fog, preset start/end/color and per-instance enable | table/exponential/range fog or unexpected source |
| sky | cloud resource identity/world-centering matches known entity; actual depth/order captured | classifier based on state alone conflicts with another owner |
| target/depth | ordinary scenes stay on implicit backbuffer/depth | SetRenderTarget/RT texture/Cube/CopyRects active in game |
| loss/reset | Alt-Tab/mode change returns correctly, resources valid, HRESULT sequence preserved | stale DEFAULT resources, lost drawing, reset loop/crash |
| stock parity | same track/car/camera/options visually match baseline with no forwarding changes | alpha/env/fog/UI/texture/filter differences |

Scenario matrix: frontend navigation and vehicle preview; intro/video if available;
race on at least contrasting cloud selections; vehicle body/windows/wheels,
vegetation/fences, road/terrain, dust/skid/water/sparks and stock shadows; replay;
one/two/four camera modes if available; fullscreen/windowed and resolution changes;
loss/restore; optional existing debug mode. Human observation establishes appearance;
API logs establish call behavior. Neither a unit test nor a frame count proves both.

Semantic classification must retain UNKNOWN until caller/resource/state signatures
are corroborated. Highest common DrawIndexedPrimitive PCs cannot distinguish
terrain/road/body/wheel/glass. Proxy-only logging may need a later read-only
provenance supplement to connect raw textures/compiled slices to resource names;
that supplement is not authorized implementation in this phase.

Remaining static priorities: semantic sky ordering/depth; terrain/road/foliage entity producers;
all realized compiled vertex layouts; source lighting/colors; loss invalidation and
slice recreation; screenshot source-to-file chain; optional D3DX reachability.
Runtime discovery of a new method extends the forwarding audit before new effects.
R-GFX2 success is stock-transparent forwarding plus evidence, with no lighting,
FOV, sky, rain, shadow or postFX changes. R-GFX1 stops before that implementation.
