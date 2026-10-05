# Fixed function versus actual shader programs

**CONFIRMED_BY_EXE:** base/env/noise/water methods VA `0x005867A0`, `0x00586150`,
`0x00585AC0`, `0x005854D0` and particle `0x00584EA0` configure render states and
texture-stage combiners. Names `shader/base*` identify engine pass objects, not
Direct3D vertex/pixel shader bytecode. UI and stock shadow paths also configure
fixed-function state. FVF builder `0x00575E70`, binding `0x00564FB0`, and concrete
0x142 use establish SetVertexShader as the D3D8 FVF API in those paths.

| Family | Classification | Evidence scope |
|---|---|---|
| base / alpha / alpha-test | FIXED_FUNCTION | traced setup, compiled layouts, indexed emission |
| base_env variants | FIXED_FUNCTION | camera-space normal texcoord generation and texture matrix |
| base_noise variants | FIXED_FUNCTION | stage1 MODULATE2X, including alpha-test branch |
| base_water variants | FIXED_FUNCTION | stage1 ADD and fixed-function alpha operations |
| particle five modes | FIXED_FUNCTION | fixed blend pairs and texture/diffuse modulation |
| text/2D, debug, projected shadows | FIXED_FUNCTION | FVF binding and direct state setup |
| unreviewed/linked helpers | UNKNOWN | no claim of whole-program exclusion |

**STATIC_INFERENCE:** the ordinary inspected game renderer is fixed-function;
no proven real vertex/pixel shader creation or binding was recovered. The Ghidra
memory-call inventory (5,027 calls) contains no +0x12C CreateVertexShader,
+0x15C CreatePixelShader or +0x160 SetPixelShader match. This is coverage-limited:
register-dispatched calls and unanalysed code are not covered by that statement.

Linked D3DX shader assembler code exists, including bytecode assembly and dynamic
Validate* exports (see entry document). Its existence does not upgrade the game
to PROGRAMMABLE or MIXED. Future runtime logging must distinguish FVF values from
actual handles returned by CreateVertexShader and record every shader creation.
Any such game call makes the global fixed-function-only inference FAIL and
extends the compatibility map; it does not invalidate the observed family setups.
