# Linked graphics helpers, screenshot and developer coverage

**CONFIRMED_BY_EXE:** linked D3DX paths are marked
`linked_helper_unproven_game_reachability` in callmap, separate from game paths:

| Body VA / RVA | Confirmed API behavior | Game reachability |
|---|---|---|
| 0x005DFD97 / 0x001DFD97 | sprite setup, FVF0x144, render/TSS states, Begin/EndStateBlock | unresolved |
| 0x005E01F1 / 0x001E01F1 | textured RHW quad, DrawPrimitiveUP at005E0490, stride28 | unresolved |
| 0x005E060E / 0x001E060E | CreateRenderTarget/DepthStencilSurface, GetRenderTarget/DepthStencilSurface, SetRenderTarget, BeginScene | unresolved |
| 0x005E07DA / 0x001E07DA | EndScene, CopyRects, restore targets/ApplyStateBlock | unresolved |
| 0x005E0AB7 / 0x001E0AB7 | render-to-environment helper, RT texture fallback, offscreen surfaces | unresolved |
| 0x005D9794 / 0x001D9794 | image-to-2D texture; DEFAULT branch uses SYSTEMMEM staging/UpdateTexture | unresolved |
| 0x005D9BA5 / 0x001D9BA5 | six-face CreateCubeTexture/upload/UpdateTexture | unresolved |
| 0x005EC5C0 / 0x001EC5C0 | D3DX font bitmap/texture/state-block setup | unresolved |

Library function identities are **STATIC_INFERENCE** from behavior/caller chains,
not recovered symbol names. Public font wrapper `0x005DAAA3` has no direct callers
in the current Ghidra index. Dynamic ValidateVertexShader/ValidatePixelShader
belongs to linked assembler code; real shader creation remains unobserved.
These facts prevent declaring all optional graphics methods absent, but do not
prove stock postFX, reflection captures or cube textures are active.

Screenshot: no stock backbuffer-to-file chain established. Reviewed GetBackBuffer
calls only obtain dimensions/format. DirectDraw primary-surface ownership after
startup is confirmed; capture purpose is unknown. No GetFrontBuffer path is
receiver-confirmed in this map. File-output and format-conversion pieces without a
connected render source cannot establish screenshot functionality.

Developer rendering: `0x00589880` uses debug-system accessor `0x004E5CE0`, emits
world primitives via `0x00589B70`, switches to orthographic/identity matrices, sets
ZENABLE0, emits screen primitives `0x0058A4F0`, restores ZENABLE1. They use dynamic
buffers and DrawPrimitive, with scene attachment/identity choice in `0x0058AD40`.
Primitive collections are confirmed; complete bindings to wireframe, bounds,
normals, collision labels or statistics commands remain unresolved. Their presence
is not proof of an enabled end-user debug mode or existing freecam.

**CONFIRMED_BY_EXISTING_RESEARCH:** external R-DEV1 editor inventory at
`../master-rallye-re-general/_re-evidence/master-rallye-re-r-dev1/research/r-dev1/editor-inventory.md`
lists FlowBuilder/Broker/Egg/Particle/Marker editors and particle-editor leads.
It is read-only input. No developer controls were activated or expanded.
