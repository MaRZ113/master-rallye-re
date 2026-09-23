# Alpha path

**CONFIRMED_BY_EXECUTABLE:** DX flag byte 0 -> runtime material +0x22; byte 1 -> +0x23. The shader selector at 0x580360 chooses no suffix when +0x22=0, `_alpha` when +0x22!=0 and +0x23=0, `_alphatest` when both are nonzero. `FUN_00565DA0` registers those variants. The base shader virtual method 0x5867A0 calls the D3D8 render-state wrapper.

| Shader variant | D3D8 states established by method |
|---|---|
| base_alpha | ZWRITEENABLE=0; ZENABLE=1; ALPHABLENDENABLE=1; SRCBLEND=SRCALPHA (5); DESTBLEND=INVSRCALPHA (6); ALPHATESTENABLE=0 |
| base_alphatest | ZWRITEENABLE=1; ALPHABLENDENABLE=0; ALPHATESTENABLE=1; ALPHAFUNC=GREATER (5); ALPHAREF=128 |

**CONFIRMED_BY_CORPUS:** all 1,478 vehicle draw flag byte 1 values are zero; 237 flag byte 0 values are one. Thus the observed static vehicle draws can request _alpha but not _alphatest. Byte 2 separates many glass-like from brake/glow-like names, yet does not select alpha test. Byte 0 matches sidecar slot-0 UsesAlpha in 1,364/1,365 unique bindings, with one Kamaz sidecar exception.

Game-observed transparency, sorting, glass response, and brake dynamic pass remain **UNKNOWN** pending M2/M4.
