# Terrano released / held-brake native control

Two current same-session F10 captures were examined: session2080/frame1288
(released brake) and frame1569 (held brake), as labeled by the user. Both certify
Turkey2, race lifecycle generation6 and owner lifetime1. Original EXE SHA is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
proxy SHA is `d0059a788bb270fa54f2091e00052149b74565452b677cd9a19c84760b37efe6`.
File hashes and exact captured matrices are in `runtime-join.json`.

| Control | Observed DIP arguments (type,min,vertices,start,faces) | FVF/stride | Texture0 generation | Blend | Zwrite |
|---|---|---|---|---|---|
| released rear lamp | 4,5218,10,14262,6 | 0x152/36 | 638 | OFF | ON |
| held lamp | 4,5840,10,14184,6 | 0x112/32 | 772 | OFF | ON |
| held glow | 4,5850,20,14202,20 | 0x112/32 | 773 | ON, SRCALPHA / INVSRCALPHA | ON |

All three calls return S_OK. Alpha test is OFF, Z-test enabled, ZFUNC LESS_EQUAL,
cull CCW and fog ON. Stage1 remains the native MODULATEALPHA_ADDCOLOR with
camera-space normal generation/COUNT2 and texture generation631. The on and glow
calls reuse their frame's vehicle world transform; released versus held world
and view differ, so these frames are a control-state comparison, not a pixel A/B.

The released frame contains the six-face off candidate; the held frame instead
contains a different-format six-face on candidate plus a twenty-face glow
candidate. This positively establishes an existing PC renderer brake-dependent
submission change under the user's control labels. It does not identify a
controller memory slot or prove the exact threshold. No new glow is needed to
invent basic PC braking behavior.

Original Terrano source record30 (on) and record32 (off) share the exact geometry
SHA `2afd75bd071f0cb1bee35be8f99f0209511a5332b0e8880bb3b889fa52aaf847`.
Source record31 is20-face glow, SHA
`3658c62c72e54bbe2fba9ad4b9503bd55ab38d5ec40336e89341dc79ff828517`.
The source-layout/count/material correlation is strong STATIC_INFERENCE;
the F10 files contain no uploaded vertex/index bytes, so full native geometry
source identity is not yet independently proved. Numeric ranges, ordinals and
generations in this table must never become a persistent admission predicate.

The off candidate has no PS2 Mode4 transaction around it. Immediately adjacent
body draws do show feature8 stage1 ADD/private-texture changes and restoration
to native COLOROP18. Thus this capture does not support claiming a PS2 override
was applied to the off brake branch. The native off material already has a
reflection-capable second stage. Whether another body mesh overlaps lamp area
requires exact source-face attribution, not a global lamp exclusion.

**Smallest safe implementation:** retain the original native conditional draw
selection; validate each selected current lamp's full mirrored geometry plus
original normals/UVs and resource generations, then apply only proved source
material changes. Never use the shared six-face position hash alone to choose
off versus on. Preserve original on/glow timing. The original PS2 mode14 GS
contract remains a separate prerequisite for claiming PS2 glow equivalence.

Executed: `python .../runtime-pair/audit.py`. No renderer edit, memory mutation,
game-file copy, new build directory, screenshot copy or DLL installation.
