# R4D targeted renderer reconnaissance

## Direct3D version

**CONFIRMED_BY_EXECUTABLE:** the original MRallye.exe PE32 import table names d3d8.dll and Direct3DCreate8. This was checked directly from the import directory, not merely from embedded text.

## Narrow Ghidra chain

The existing analyzed project at E:/Game/Master Rallye/_ghidra_project was queried on demand. Function addresses refer to that original executable. Raw decompilation stays under ignored .research-output/r4d/ghidra.

| Address | Direct observation | Status |
|---|---|---|
| 00565DA0 | Registers shader/default, shader/base, base_alpha, base_alphatest, base_env, base_env_alpha, base_env_alphatest, corresponding noise/water variants, and separate particle variants. | CONFIRMED_BY_EXECUTABLE |
| 00580360 | Builds shader names from a material object: bits 0/1 of +0x34 select base text; bit 2 requests env when Reflections is enabled; bit 3 requests noise when DetailPasses is enabled; bit 4 requests water. Bytes +0x22 and +0x23 select _alpha versus _alphatest suffix. | CONFIRMED_BY_EXECUTABLE for this object; connection to DX offsets UNKNOWN |
| 00577FB0 | Calls 00580360 and looks up the constructed shader, with fallback behavior. | CONFIRMED_BY_EXECUTABLE |
| 0053F8B0 | Caches a state/value pair and calls D3D8 device vtable +200 with (state,value). Consistent with SetRenderState. | HIGH_CONFIDENCE_INFERENCE |
| 0053F930 | Caches a (stage,state,value) triple and calls device vtable +252 with those three arguments. Consistent with SetTextureStageState. | HIGH_CONFIDENCE_INFERENCE |
| 00584EA0 | A particle-family shader method calls both wrappers. It sets render states 14 and 27 and stage states 1, 4, 11, 13, 14. This is **not** evidence that vehicle draws use the same values. | CONFIRMED_BY_EXECUTABLE for particle path only |
| 00589110 | Registers DirectX/Damage/RemoveEnvMap and EnvMapFadeStrength. | CONFIRMED_BY_EXECUTABLE for config registration |

Microsoft's [Direct3D 8 device interface](https://learn.microsoft.com/en-us/previous-versions/windows/embedded/ms889277%28v%3Dmsdn.10%29) documents SetRenderState and SetTextureStageState. Its [texture-stage enum](https://learn.microsoft.com/en-us/previous-versions/windows/embedded/ms886612%28v%3Dmsdn.10%29) lists COLOROP=1, ALPHAOP=4, TEXCOORDINDEX=11, ADDRESSU=13, ADDRESSV=14. The [render-state enum](https://learn.microsoft.com/en-sg/previous-versions/windows/embedded/ms886344%28v%3Dmsdn.10%29) is the comparison source for ZWRITEENABLE=14 and ALPHABLENDENABLE=27. Numeric constants are reported only for the inspected particle method; vehicle-state application remains untraced.

## Explicit limits

No direct xref has yet been established from the parsed 40-byte DX draw core to the material object inspected at 00580360. DX unknown_0x24 values 1/2/3/5/6/7 look bit-like, but equating them to the +0x34 shader mask would be premature. No vehicle-specific SetTexture stage call, blend equation, alpha-test threshold, depth-write rule, render sort, or texture-coordinate generation has been established. Material names in TXT were not shown to be runtime input.
