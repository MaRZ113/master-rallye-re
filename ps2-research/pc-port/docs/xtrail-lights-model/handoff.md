# X-Trail lights/model handoff

Headlight pilot implemented; user runtime pending. Decal user-confirmed closed.
Brake/glow and full frontend/race model replacement blocked on exact contracts in
blockers.md. Start with runtime-ab.md and merge PS2Port.ini; all new defaults off.
No automatic installation or push.

ZIP contains clean committed tools/tests/source, exact overlay patches/lock,
compact source evidence, both DLLs, build report and SHA256 manifest. No original
PS2/PC textures/meshes, private PS2glass asset, screenshots or raw runtime dumps.
Prepare that local file with tools/prepare_xtrail_glass.py using canonical PS2
corpus, protected retail DX and read-only Course SDK, or use the already prepared
local ignored asset named in runtime-ab.md. Assets remain unchanged.

Build: python ps2-research/pc-port/overlay/build_overlay.py, original pinned Git
objects0bddf7c7bc5e95831f98714ff6231da05ab073ea, MSVC Win32/CMake/SDK required.
Reuse .build/baseline and .build/ps2-enabled plus .staging; --parallel1.
Corpus-independent native mocks need Windows native build dependencies; extracted
Python tests require no game corpus/SDK. Native asset decode integration accepts
MRR_XTRAIL_GLASS_ASSET; its absence is reported explicitly, not runtime proof.
No Blender required. See validation.md for actually executed checks; all user A/B
steps remain pending. No PS2 visual parity or brake/model implementation claim.
