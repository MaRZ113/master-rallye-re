# Depth, backbuffer and offscreen coverage

**CONFIRMED_BY_EXE:** device creation/reset uses automatic depth-stencil with
selected matching format. Candidate list: D16, D15S1, D24X8, D24S8, D24X4S4,
D32 (selection depends on caps/mode). Present parameters Flags=0; no lockable
backbuffer flag. BeginFrame Clear uses TARGET|ZBUFFER=3, depth1, stencil0.
No separate stencil clear is made in that reviewed lifecycle.

Runtime defaults include ZENABLE1, ZWRITE1, ZFUNC4 (LESSEQUAL). Material families
and instance bytes+0xA8/+0xA9 alter enable/write. Base alpha disables writes;
environment alpha setup retains writes until instance override. Alpha-test uses
writes in the base family. Particle blend and stock textured shadows use write0.
UI depth is packet controlled; late debug screen geometry explicitly uses Z0 then
restores Z1. A depth snapshot at frame end can therefore contain different subsets.

GetBackBuffer VA `0x0055AD3C`/`0x0055AE6D` obtains a surface for GetDesc and releases
it after create/reset. This is not CPU capture or sampled depth. Mapped ordinary
scene/UI/particle paths contain no render-target switch: direct backbuffer rendering
is a **STATIC_INFERENCE limited to those paths**.

**CONFIRMED_BY_EXE:** linked D3DX surface/environment helpers `0x005E060E`,
`0x005E0AB7` create render/depth surfaces, save/restore targets and state blocks,
and CopyRects on some branches. Their game reachability is unresolved.
It would be incorrect to claim whole-program absence of intermediate targets.
See [library coverage](library-capture-debug.md).

**STATIC_INFERENCE:** native forwarding preserves depth behavior but does not by
itself supply a sampleable depth texture. SSAO/modern depth fog/DOF need a backend
that retains compatible depth or carefully replays depth-writing geometry, including
cutouts, damage and transparent writes. Projection/camera/viewport must accompany
each depth image, particularly split-screen. No depth-copy logic was implemented.
