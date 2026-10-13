# Original PS2 HUD contract and exact proof limits

Canonical ELF: `SLES_509.06`,3739852bytes, SHA256
`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`.
All four canonical inputs were hashed in this pass. PackFS addressing/decode
reuses `tngtool.py`; no decompressor or general image-bank parser was added.

## Resource ownership

| Original logical path | Decoded SHA256 | Supported fact |
|---|---|---|
| `\TNG\DATASCENE\HUD\HUD0.XML` |`faa90792c53b9fd29d122a94ff6212deb8bbe5c13b9555b4c6659589dd720ae9`|Authored owner names, banks, keys, positions/configuration; not proof of current runtime bank selection|
| `\TNG\DATAPSM\HUD\HUD-TEMPLATE.PSB` |`c36f89c2978a98a4e3e3e4ce64204ff9cd52c3f9a81c5891cb9268859e172f9b`|11images/34triangles; dial, needle, GPS and progress parts|
| `\TNG\DATAPSM\HUD\NEWHUD.PSB` |`131a5be359ea620182c244b99fe97e47279ef33d425f9a9791c86663dd0d648d`|38images/148triangles; complete rank numerals and small digits|
| `\TNG\DATAPSM\HUD\HUD-DAMAGE.PSB` |`84adc1ad91f5970a83b9a0367ed7ee2bc5a2022c2af4446efd929d0211c72d68`|Siximages/12triangles, icon/overlay lookup|
| `\TNG\DATAPSM\HUD\PACENOTES.PSB` |`35fb0d8121634775be768366dfb61f9f453479fe86181684eba77a076d1807e7`|24images/48triangles; gameplay enum mapping unknown|

The first dial is not one64x64picture. Source image0 uses
`HUD-TEMPLATE_001`, `_002`, `_003`, `_004`: four64x64quadrants, two triangles
each. Their respective decoded GXI SHA256 values are:

```text
001 7c13b266f093d34e120ed8f968089991fdf8bcfa1ed20219baa115c7c2866174
002 4e4098e5b0c61aa0438138c1fa0592d302dc61485f203d89805690ed4b0e0f6b
003 be80406032fd64bfa0ee57ad6afd2b9126a0cb850c2e6ec99c8fa37454b82831
004 44234b829d1850f9a440d04632d10eff3ef7eabf4cdb01012c41935236d2923b
```

Supported GXI is magic0x00013039,u16dimensions, exact8+W*H*4bytes.
UI1's RGBA/channel and V-to-row interpretation is visually corroborated by
whole glyphs and atlas reconstruction; the stored alpha statistics do not
prove the GS upload, texture combine or final alpha equation. Unsupported
variants fail closed. Full source images/geometry stay private.

PSB is F001/version125, bank key->image lookup, per-image triangles, UV/XY and
texture references. It does not encode a full live HUD layout, independent
anchors, glyph advances or material render state. `HUD-NUMS` alone is unsuitable
for rank replacement: its0..9keys alias only four drawn glyphs; NEWHUD has the
complete0..9mapping (0->37,1->28,...,9->36).

## Original execution chains

These working function names come from UI1/UI2, not original C++ symbols.
Addresses were originally tied to bytes/directJAL/vtable evidence, but that
historical pass used genericMIPS scalar surrogates and did not model COP2.
This phase rechecks only the explicitly listed R5900 words; it does not upgrade
every prior pseudocode result into fresh exact-EE proof.

```text
HUD0.XML bank/key/matrix + named AI
 -> 0x00295D58 version4 Egg reader
 -> 0x00292A48 entity/optional en2d creation
 -> 0x001FC4C0 owner lookup/clone -> 0x0021E620 initialize
 -> owner changes commands of the same en2d
 -> 0x00337A98 bank-key lookup / PSB triangle producer
 -> 0x003387C8 / 0x00338AB8 orthographic UI camera
 -> matrix/packet helpers -> 0x003376C0 submission
 -> UNKNOWN LINK: complete ordinary-sprite video/display composition
```

Bank loader: `0x00380A08 -> 0x00380998 -> 0x00386D28`; mapping reader
`0x00387188`, image reader `0x00387258`, triangle reader `0x00387478`.
In-memory image vector12bytes/triangle72bytes differs from packed PSB disk.

Dial config `0x0014B290 -> 0x0014B388` publishes needle/gear/speed positions.
Needle init `0x0014B6C8` obtains that state and writes translation; needle
update `0x0014B8B0` is an established vtable target whose full RPM rotation
is outside this report. Rank constructor `0x0014DE38` defaults to HUD/newhud;
`0x0014E250/0x0014E360 -> 0x0014E028` rebuilds the same command stream on rank
change, including a localized ordinal suffix. FontNo alone does not resolve
every glyph bank/locale or advancement rule.

## Procedural minimap: different owner and rendering mechanism

```text
Named RaceLine markers (document order; worldXYZ)
 -> gaHudAiMap init0x001461F8/update0x00147038
 -> route window + CarN output + stored heading
 ->0x001469F0 clipping ->0x00146D80 endpoint pair batches
 ->32EE40/32F498/32F710 primitive queues
 ->32FCE0 ->318E10 stroke expansion/GS coordinates
 ->318BD8 untextured alpha-blended triangle strip packet
```

For playerP and worldW in XZ, stored unit headingH and S=0.4f:

```text
dx=Wx-Px; dz=Wz-Pz
localX=S*(Hz*dx-Hx*dz)
localY=S*(Hx*dx+Hz*dz)
```

Clip half-extents45/43 and add center(74,392) for authored HUD0. Source route
records are80bytes with position+0x40/+0x44/+0x48. Player/opponents use PS2
output wrapper+8, position+0xF0/+0xF8. These are **PS2 offsets**, not PC aliases.
Window selection depends on LastMarker and FinishArea/BestMarker. Heading
consumes output vectors at+E0 and+18, with unusual0.045component evolution;
the initial heading seed and complete producer meanings remain unknown.

Route strokes have shadow width6/front3, opponent/player strokes width4;
packet alpha shifts right1 (250->125). The tag is PRIM0x14c: triangle strip,
TME0,ABE1. The traced course minimap does not bind MAP128STRIPED. This is an
actual different renderer, not an inference from the map-shaped screenshot.
Exact degenerate joins, selected full GS inherited state and per-pixel parity
remain unvalidated. See existing `ps2-research/ui2/minimap.md` for boundaries.

## R5900 matrix kernel: newly decoded, final composition still open

Fresh original-byte Rabbitizer R5900 decoding at0x003CB2D0..0x003CB308 gives:

```text
lqc2 vf4..vf7, four16byte vectors at a1
lqc2 vf8, current16byte vector at a2
vmulax.xyzw ACC,vf4,vf8x
vmadday.xyzw ACC,vf5,vf8y
vmaddaz.xyzw ACC,vf6,vf8z
vmaddw.xyzw vf9,vf7,vf8w
sqc2 vf9, current16byte destination at a0
repeat4rows with a0/a2 advancing16bytes
```

Hence each result vector is A0*Bx+A1*By+A2*Bz+A3*Bw, in that operation order.
With contiguous row-vector arrays, destination is B*A. This is
`EXACT_ELF_OPERATION` for the instruction identity, not host bit-exact EE/VU
emulation. Caller argument roles and selected projection/video/display factors
still need validation before asserting a universal final PS2 sprite equation.

Code-defined logical dimensions640x480 and localY inversion/half-pixel cursor
bias remain useful. The UI2 estimate
`x=tx+localX-0.5; y=480-ty+localY-0.5` applies only under its stated identity
global-UI/unit vertical-factor assumptions. RasterW/H, vertical factor0.5/1,
PS2/ScreenPosX/Y and field/interlace selection are not recovered as one live
frame here. Screenshot stretching must not fill this gap.

