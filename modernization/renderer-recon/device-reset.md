# Cooperative status, reset and recreation

**CONFIRMED_BY_EXE:** `CheckDevice_0055AF50` calls TestCooperativeLevel at
VA `0x0055AFB3` (RVA `0x0015AFB3`). D3DERR_DEVICELOST `0x88760868` leaves rendering
unavailable. D3DERR_DEVICENOTRESET `0x88760869` refreshes windowed adapter display
format (GetAdapterDisplayMode at `0x0055B006`), then invokes `0x0055AE40`.
BeginFrame's +0xB0 gate prevents normal drawing while the manager is unavailable.

Reset owner `0x0055AE40` invokes manager virtual+0x14, device Reset at
`0x0055AE57`, refreshes backbuffer/GetDesc, cursor state, then manager virtual+0x18.
Manager vtable VA `0x0069228C` gives concrete callbacks:

| Callback | Owner VA / RVA | Effect |
|---|---|---|
| pre-reset +0x14 | 0x0055B410 / 0x0015B410 | 00567F60 destroys dynamic VB/IB ownership lists |
| post-reset +0x18 | 0x0055B450 / 0x0015B450 | 00570BB0 reapplies cache; 0053F590 restores baseline |
| full destroy +0x10 | 0x0055B3D0 / 0x0015B3D0 | 00567D40 includes dynamic plus static backing allocator cleanup |

`0x00567F60` calls resource destruction helpers `0x005849D0` and `0x00587970` and
clears owner lists. Dynamic buffers were created DEFAULT; static backing buffers
and ordinary uploaded textures were MANAGED. Post-reset state restoration includes
cached render/TSS/transform/texture/stream/index/FVF/viewport state plus boot
projection. State-cache duplicate suppression makes invalidation/restoration material.

Full device release `0x0055B0F0` invokes pre-reset/full-destroy callbacks before
Release at `0x0055B11A`; auxiliary DirectDraw objects are released later. Explicit
mode/fullscreen changes can release/recreate instead of only Reset. These must both
be exercised in the next phase.

Complete resource-pointer invalidation and eager/lazy recreation of every compiled
slice, video texture and optional D3DX DEFAULT surface is still unresolved. Do not
infer MANAGED pool behavior for all resources from the ordinary texture uploader.
Runtime PASS requires successful return to race/frontend after loss and mode change,
no stale DEFAULT handles, balanced ownership, and unchanged HRESULT sequences.
