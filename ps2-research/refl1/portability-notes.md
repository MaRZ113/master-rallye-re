# Future portability, research only

No implementation, D3D8 proxy change, asset conversion/deployment or SDK update
is authorized or performed in this phase.

| Recovered feature | Future classification | Required interface |
|---|---|---|
|ENV64/static windscreen source images|ASSET_REUSE / PS2_TEXTURE_CONVERSION|Validated GXI conversion and source pixel interpretation|
|carshiny/carglass/flat and rubber exception|VEHICLE_MATERIAL_PORT / MATERIAL_METADATA_EXTENSION|Actual material identity, primary/secondary ownership and mesh subset|
|Normal-coordinate mapping|D3D8_PROXY_RENDER_FEATURE|Original object/view orientation and normals; explicit PS2 basis/state semantics|
|Additive body layer and glassFIX96|D3D8_PROXY_RENDER_FEATURE|Draw-local material/pass state; do not apply indiscriminately to every FVF0x152 draw|
|Static+framebuffer64x64 feedback|D3D8_PROXY_RENDER_FEATURE / PC_RUNTIME_HOOK|Correct capture point, source frame, target generation and consumer timing|
|Scene/conditional material identification|MATERIAL_METADATA_EXTENSION / PC_RUNTIME_HOOK|Stable native mesh/material association, not only texture color or flatness|
|Live target parity and inheritance|REQUIRES_DEEPER_RE|Selected frame packet/VRAM/GS capture|

The screen-feedback producer is a dynamic texture update, but its known content
is not a separately rendered environment camera. Calling a future feature
DYNAMIC_ENVIRONMENT_CAPTURE must not imply a cube map or mirrored scene absent
from the original. A faithful option may need to reproduce the screen mixture;
choosing a modern reflection method would be a later product/design decision.

Existing PC normal-coordinate infrastructure is related to the PS2 equation.
The existing experimental REFLECTIONVECTOR mode is not automatically the faithful
implementation. Original source colors, target mixture and additive coefficient
may matter more than changing the coordinate generator.

The current PC draw wrappers do not universally expose full PS2 shader/material
identity. A texture named chrome or a NORMAL FVF is insufficient to distinguish
paint, glass, rubber and unrelated env materials. A future vehicle material
metadata bridge or runtime owner hook may be necessary. That interface has not
been implemented here; Course SDK does not need changes for this vehicle study.

Lighting broader than the local grayscale auxiliary, opponents/LOD, model reload,
GS conversion and presentation cadence remain separate constraints. No portable
bit-exact claim is made from host float32 tests.
