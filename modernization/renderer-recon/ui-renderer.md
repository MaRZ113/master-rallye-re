# Text, 2D packets, frontend, HUD and video

**CONFIRMED_BY_EXE:** `DrawTextPacket_0056D110` receives entity+0x4C packet.
Packet+0x68 modes1/2 select logical 640x480 ortho; other modes select perspective.
Packet+0x7C bit2 controls depth enable. Mode2 can defer through renderer+0x94..+0x98;
other calls are emitted during scene entity traversal. Final UI ordering is therefore
partly immediate and partly EndFrame, not a single universally isolated HUD pass.

DrawPrimitive VA `0x0056D7BE` (RVA `0x0016D7BE`), stream bind `0x0056D7A8`.
Dynamic glyph/quad vertices use FVF0x142/24 bytes. State: unlit,
SRCALPHA/INVSRCALPHA, clamp U/V, stage0 texture*diffuse, stage1 disabled.
Ortho filtering is linear min/point mag/no mip; perspective packet branches change
mag/mip. Font/glyph cache lead `0x0054B430`; GDI rasterization `0x0064EC50` and
font worker `0x00652DC0`. Rasterization is not a GDI replacement for D3D presentation.

HUD versus frontend callers/resources are not exhaustively connected to packet
owners. Ortho/FVF/blend alone cannot distinguish both, or world labels. A future
proxy will need resource/caller provenance and active scene context for that split.

Video path `0x0056C0D0` is gated by video singleton+0x248 (`0x005813E0`), with
textures from `0x005833B0` and an optional tiled layout. It uses triangle fans,
orthographic state and FVF0x142. Its DrawPrimitive sites are separately marked in
[call map](data/d3d8-callmap.json); they must not be labeled ordinary HUD or debug.
Linked D3DX sprite/font code also exists, including FVF0x144/28-byte RHW quads;
its game reachability remains unresolved.

After all cameras, EndFrame emits deferred UI, then optional late debug world/screen
geometry, EndScene and Present. Future postFX/HUD suppression must locate actual
packet boundaries: processing everything before Present would include UI/video/debug.
