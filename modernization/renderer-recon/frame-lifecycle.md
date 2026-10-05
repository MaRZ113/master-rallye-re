# Application and renderer frame lifecycle

**CONFIRMED_BY_EXE:** `UpdateAndRender_005AFE30` performs fixed-step update work,
computes/clamps interpolation to 0..1 and calls `RenderFrame_00653080` at VA
`0x005B0166` (RVA `0x001B0166`). Frame owner checks Fullscreen changes, reads
client size, and schedules each active camera. Renderer constructor `0x0056B680`
installs vtable VA `0x006922C8`; `0x004D3920` returns holder global `0x006F93D0`.

| Order | Frame-owner call site VA / RVA | Operation |
|---|---|---|
| 1 | 0x00653280 / 0x00253280 | vtable+0: BeginFrame_0056B900 |
| 2, each camera | 0x0065328C / 0x0025328C | +0x0C: BeginCamera_0056E1B0 |
| 3, each camera | 0x0065329C / 0x0025329C | +0x24: SetCurrentCamera_0056BAF0 |
| 4, each camera | 0x006532C9 / 0x002532C9 | +8: viewport via 0056BB90 -> 005613E0 |
| 5, each camera | 0x006532DD / 0x002532DD | SubmitVisibleEntities_00509680 |
| 6, each camera | 0x006532E6 / 0x002532E6 | +0x20: FinalizeCamera_0056E250 |
| 7, all cameras finished | 0x0065331B, 0x00653322 | restore first camera/full-client viewport |
| 8 | 0x00653329 / 0x00253329 | +0x18: EndFrame_0056CD80 |

`0x004F6310` is the scene-manager accessor; its +0x20 object owns per-camera
entity lists consumed by `0x00509680`. The submitter skips entity flag bit2 and
invokes renderer+0x10 (`0x0056BA70`). It is not a separate terrain/vehicle API.

BeginFrame checks cooperative status through `0x0055AF50`; renderer byte+0xB0
gates rendering. It resets queues/context, calls Clear at `0x0056BA1A` with
TARGET|ZBUFFER=3, black, depth1/stencil0/no rectangles, then BeginScene at
`0x0056BA23`. Camera rectangles support one view, two horizontal halves and four
quadrants with divider gaps; the first camera is restored to full client before end.

Entity submission flushes `0x00562810` when grouping byte+0x48 changes. Entity
+0x50 enters `0x0056BBC0` (bounds, hierarchy, compiled geometry, damage,
shadow/trail collection); +0x4C enters `0x0056D110`. Each geometry flush emits
opaque before alpha using R-MAT1 state groups/composite depth keys. Sky/terrain/car
ordering inside lists is not a global semantic pass order. Immediate 2D packets
can occur during submission.

FinalizeCamera has this confirmed structural sequence:

1. Final geometry flush (`0x00562810`).
2. Shadow vector renderer+0x34..+0x38 -> `0x00587C20` -> `0x00587DB0`.
3. Trail vector +0x48..+0x4C -> `0x00571B30` -> `0x00571EC0`.
4. If DirectX/Particles/Enable is absent or true: apply camera then
   `0x00563CB0` -> billboards `0x005641C0`.
5. If video singleton `0x005833B0` has active byte+0x248 (getter `0x005813E0`):
   video texture quads `0x0056C0D0`. This is video, not the debug HUD.

EndFrame emits deferred +0x94..+0x98 2D packets, optionally calls late debug
`0x00589880` (world then screen primitives), unbinds textures `0x0058C4C0`, calls
EndScene at `0x0056CE60`, then Present through `0x0055B0D0`. Actual Present VA
`0x0055B0DE` passes all four parameters null. Queue maintenance/FPS accounting follow.

[Passes JSON](data/render-passes.json) separates scheduler order from unresolved
semantic object order inside shared queues. Present alone is insufficient as a
future HUD boundary: immediate packets, video, deferred UI and late debug all matter.
Runtime counts and split-screen behavior remain unobserved.
