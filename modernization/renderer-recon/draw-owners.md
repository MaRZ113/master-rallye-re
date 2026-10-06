# Draw owners and shared semantic paths

All code-path rows below are CONFIRMED_BY_EXE; semantic category exclusions
and runtime activity are not implied. Addresses are VA; full RVA/call lists are
in [master map](data/renderer-map.json) and [callmap](data/d3d8-callmap.json).

| Owner VA / RVA | Path | Draw API / first call | VB/IB and layout | Material / transform / state |
|---|---|---|---|---|
| 0x00576970 / 0x00176970 | SHARED_COMPILED_WORLD | DrawIndexedPrimitive / 0x00577078 | compiled instance/material descriptors -> shared static suballocator00587070; VB+IB slices | compiled ordered material passes, selector00580360, family setup; instance+44 via00583B90; final world00561A40; 005867A0/base,00586150/env,00585AC0/noise,005854D0/water; final instance overrides |
| 0x0057F9A0 / 0x0017F9A0 | ALTERNATE_FIXED_FUNCTION_MESH | DrawIndexedPrimitive / 0x00580242 | compiled instance/material descriptors -> shared static suballocator00587070; VB+IB slices | compiled ordered material passes, selector00580360, family setup; instance+44 via00583B90; final world00561A40; 005867A0/base,00586150/env,00585AC0/noise,005854D0/water; final instance overrides |
| 0x005641C0 / 0x001641C0 | PARTICLE_BILLBOARDS | DrawPrimitive / 0x00564ECA | dynamic ring VB; FVF0x142 stride24, no index buffer in draw | particle texture/shader mode; camera basis plus particle world records; particle00584EA0 |
| 0x00571EC0 / 0x00171EC0 | TRAILS | DrawPrimitive / 0x005722E8 | dynamic ring VB; FVF0x142 stride24, no index buffer in draw | trail shader/texture; trail triangle positions; particle00584EA0 |
| 0x00587DB0 / 0x00187DB0 | STOCK_SHADOWS | DrawPrimitive / 0x005881E5 | dynamic ring VB; FVF0x142 stride24, no index buffer in draw | misc/shadow/shadow; projected stock shadow positions; particle00584EA0 |
| 0x0056D110 / 0x0016D110 | TEXT_2D_PACKET | DrawPrimitive / 0x0056D7BE | dynamic ring VB; FVF0x142 stride24, no index buffer in draw | text/sprite glyph texture handle; packet ortho/perspective mode; inline owner state + shared cache |
| 0x0056C0D0 / 0x0016C0D0 | VIDEO_QUADS | DrawPrimitive / 0x0056C31D | dynamic ring VB; FVF0x142 stride24, no index buffer in draw | video singleton texture slots; ortho video quads; inline owner state + shared cache |
| 0x00589B70 / 0x00189B70 | DEBUG_WORLD | DrawPrimitive / 0x00589FB4 | dynamic ring VB; FVF0x42/stride16 or point-size0x62/stride20, no index buffer | debug color/primitive collections; scene attachment0058AD40/current camera; inline owner state + shared cache |
| 0x0058A4F0 / 0x0018A4F0 | DEBUG_SCREEN | DrawPrimitive / 0x0058A766 | dynamic ring VB; FVF0x42/stride16 or point-size0x62/stride20, no index buffer | debug color/primitive collections; ortho identity world/view; inline owner state + shared cache |
| 0x005E01F1 / 0x001E01F1 | LINKED_D3DX_SPRITE | DrawPrimitiveUP / 0x005E0490 | UP stack vertices, no VB/IB; FVF0x144 stride28 | sprite texture and tint argument; RHW vertices / optional matrix argument; 005DFD97 sprite state blocks |

Scene list00509680 -> SubmitEntity0056BA70 -> packet0056BBC0 -> bounds0054C9D0
-> compiled submission00576910/00562560 -> common indexed emission. Terrain,
static world, body, wheels, glass and alpha-tested objects can share this entire
tail. Road details/vegetation/driver-interior distinct renderer owners remain UNKNOWN.
Sky initialization/resource provenance is separate from the final D3D caller.

Caller PCs identify billboards, trails, textured stock shadows, packet UI, video
and debug paths much more strongly than they identify a specific world object.
A shared static VB can hold slices of unrelated objects. The alpha queue identifies
blend ordering, not exclusively vehicle glass. No shader/layout alone proves road.

No DrawIndexedPrimitiveUP was recovered. DrawPrimitiveUP is present in linked
sprite code005E01F1, whose game use is unproved. Do not count it as stock HUD
until that chain is observed.
