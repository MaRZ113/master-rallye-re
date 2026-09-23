# D3D8 wrappers and texture stages

The PE imports d3d8.dll and Direct3DCreate8. **CONFIRMED_BY_EXECUTABLE:** `FUN_0053F8B0` calls D3D8 device vtable +200 with (state,value), matching `SetRenderState`. `FUN_0053F930` calls +252 with (stage,state,value), matching `SetTextureStageState`. Direct +244 calls in `FUN_00586C60` pass (stage,texture), matching `SetTexture` and binding shader-pass entries by increasing stage index. Paired API method order, call shapes, and observed enum numbers support these identities.

Base shader method 0x5867A0 configures stage 0 COLOROP=MODULATE (4), COLORARG1=TEXTURE (2), COLORARG2=DIFFUSE (0), ALPHAOP=MODULATE (4), ALPHAARG1=TEXTURE (2), ALPHAARG2=DIFFUSE (0), TEXCOORDINDEX=0 in its main branch. The primary stage combines texture and vertex diffuse.

Environment shader method 0x586150 configures stage 1 COLOROP=MODULATEALPHA_ADDCOLOR (18), COLORARG1=CURRENT (1), COLORARG2=TEXTURE (2), ALPHAOP=MODULATE (4), ALPHAARG1=CURRENT (1), ALPHAARG2=TEXTURE (2), TEXCOORDINDEX=0x10000 (**camera-space normal**, not reflection vector), TEXTURETRANSFORMFLAGS=COUNT2 (2), plus a texture transform. Slot1 presence sets runtime mask bit 0x4 and enables this env family only when Reflections is enabled. Slot1 -> stage1 is **HIGH_CONFIDENCE_INFERENCE**; the complete material-handle-to-stage pass mapping and Null-slot behavior are not yet fully established. Whitepaint/chrome/glass/perspex appearance requires M1/M3.

The base alpha path uses source-alpha/inverse-source-alpha blending, not an additive equation. Additive particle shader registration is a separate path. No transparent sort pass was established.

Enum comparison: [D3D8 render states](https://learn.microsoft.com/en-sg/previous-versions/windows/embedded/ms886344%28v%3Dmsdn.10%29), [D3D8 texture-stage states](https://learn.microsoft.com/en-us/previous-versions/windows/embedded/ms886612%28v%3Dmsdn.10%29), [texture operations](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dtextureop), [camera-space coordinate flags](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dtss-tci).
