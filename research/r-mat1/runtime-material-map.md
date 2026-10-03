# Runtime material map and evidence provenance

Target: retail MRallye.exe SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Addresses are virtual addresses in this executable, not portable signatures.
The existing analyzed `_ghidra_project/MasterRallye.gpr` was opened read-only
through ghidra-bridge's PyGhidra runtime. Installed Ghidra 12.1.4 PUBLIC was
the newest version on D:. Missing virtual method disassembly was performed in
an unsaved transaction and rolled back. No analyzed project was saved.

`tools/scanner/r_mat1_exe.py` exports assembly, decompilation, normalized
high-pcode/CFG, callers, callees, and data references using
`ghidra_ai_bridge.exporters.runner.export_single_function`. Full exports are
ignored in `.research-output/r-mat1/ghidra/`. The tracked
[evidence index](evidence-index.json) records export hashes for reproducibility;
focused assembly and call chains are retained in these notes. Ghidra databases,
game bytes, screenshots, and full raw dumps are not committed.

## Serialized -> runtime -> compiled

R4D.1's paired tag2 serializer `005520E0` / deserializer `005528B0` is retained
as the loader evidence; this closeout traces the subsequent consumers.

| Serialized field | Runtime material | Consumer/result | Confidence |
|---|---|---|---|
| flag byte0 | +22 | 00580360 alpha suffix, shader class alpha flag | CONFIRMED_BY_EXE |
| flag byte1 | +23 | alpha-test suffix only when byte0 enabled | CONFIRMED_BY_EXE |
| flag byte2 | +20 | 005781B0 pass diffuse descriptor -> 00575E70 FVF40 | CONFIRMED_BY_EXE |
| flag byte3 | +21 | 005781B0 source UV count/dimensions -> 00577DD0 copying | CONFIRMED_BY_EXE |
| unknown_0x24 | +34 | 00580360 family selector and 00577620 binding gates | CONFIRMED_BY_EXE |
| slot0/1/2 | +38/+3C/+40 | 00577620 fixed compiled texture vector | CONFIRMED_BY_EXE |

Mask &3 selects base; mask04 with Reflections>0 selects env. Byte0 selects
the alpha suffix and byte1 selects alpha versus alphatest. `00565DA0` registers
the six base/env variants and sets shader+14 flag1 on the two alpha-blend
families; opaque and alpha-test variants get zero. No filename is consulted
by this selector. Typed tokens match the registered shader family names.

## Explicit shader writes (not a complete device snapshot)

Wrapper `0053F8B0` corresponds to device vtable+F8 SetRenderState; texture-stage
wrapper `0053F930` uses +FC. Binding wrapper `00564EE0` uses +F4 SetTexture.
The COM shape, numeric state IDs, and paired state operations corroborate
the earlier R4D.1 mapping.

| Setup write | base | base_alpha | base_alphatest | base_env | base_env_alpha | base_env_alphatest |
|---|---|---|---|---|---|---|
| LIGHTING (137) | 0 | 0 | 0 | 0 | 0 | 0 |
| ZENABLE (7) | 1 | 1 | 1 | 1 | 1 | 1 |
| ZWRITEENABLE (14) | 1 | 0 | 1 | 1 | 1 | 1 |
| ALPHABLENDENABLE (27) | 0 | 1 | 0 | 0 | 1 | 0 |
| SRCBLEND (19), DESTBLEND (20) | 5,6 | 5,6 | 5,6 | 5,6 | 5,6 | 5,6 |
| ALPHATESTENABLE (15) | unwritten | 0 | 1 | unwritten | unwritten | 1 |
| ALPHAFUNC (25), ALPHAREF (24) | unwritten | unwritten | 5,128 | unwritten | unwritten | 5,128 |

5/6 are SRCALPHA/INVSRCALPHA blend factors; compare function5 is GREATER.
Base method `005867A0` and env method `00586150` explicitly produce the table.
An unwritten value is represented by None, with scope metadata; it is not an
unresolved family or a claim that the shader resets inherited state.
`00576970` calls the shader method and then writes ZENABLE/ZWRITEENABLE again
from instance+0xA8/+0xA9. Therefore base_alpha's proven setup ZWRITE=0 is
retained, while the model does not claim every final vehicle draw disables Z.

The source-alpha/test distinction is exact shader semantics. The image's
HasAlpha and pixel alpha do not select this family. Existing human in-game
claims stay scoped to their tested candidates, not all shaders or materials.
Older public alpha/environment confidence fields retain the existing
`CONFIRMED_BY_EXECUTABLE` label; it denotes the same evidence category as
`CONFIRMED_BY_EXE` in the new stage/flag records, not a downgraded inference.

## Shallow damage lead

`00589110` registers DirectX/Damage/RemoveEnvMap and EnvMapFadeStrength with
the other vertex-damage controls, in a 0x58-byte configuration object.
`0056B680` allocates it and stores the pointer at renderer+0x8C. This short
trace does not prove whether a later damage path edits vertex colors, compiled
material state, or individual material fields. Following those mutations would
expand into the damage system, so the trace stops here: **OUTSIDE STATIC
MATERIAL PREVIEW**. No per-material damage-fade parameter was invented.

State constant references:
[render-state enum](https://learn.microsoft.com/en-us/previous-versions/windows/embedded/ms886344(v=msdn.10)),
[texture-stage enum](https://learn.microsoft.com/en-us/previous-versions/windows/embedded/ms886612(v=msdn.10)).
