# Primitive input and embedded VU expansion

`3597e0` emits **one 64-byte record per accepted point**, not four CPU quad
vertices. Its caller supplies a category pool, which fixes resource and size.
The record is passed to VU1 pc `0x449` by `31da60`. The canonical ELF contains
a matching MPG program, decoded below; the CPU upload of that exact stream
remains **UNKNOWN LINK**.

| Record offset | Original stored representation |
|---|---|
| `+00/+04` | Two float size inputs |
| `+08` | Float zero |
| `+0c` | Initially zero; first accepted record in a group overwritten with **integer group count** |
| `+10/+14/+18` | RGB floats `128,128,128` |
| `+1c` | Float radial-fade alpha from owner LUT |
| `+20..+2c` | Four zeros; not read by embedded detail program449 |
| `+30/+34/+38/+3c` | World X/Y/Z and homogeneous 1 |

Size inputs preserve the original order:
`sizeX=(64/renderer[+11c])*(3*lift)`;
`sizeY=((global42d2c4*64)/renderer[+11c])*(3*lift)`.
Lift is `.4` shrubs or `.33` grass. Physical meaning of renderer `+11c` and
global `42d2c4` beyond their use in these equations is **UNKNOWN**; they are
not silently named FOV/aspect. The diagnostic requires them explicitly.

The mode-11 GIF template sets the lower seven PRIM bits to **0x56**, selecting
GS **SPRITE** with texturing and alpha blending. Higher AA1/FST/CTXT/FIX bits
are inherited; the first template initializes to ST/Q and context0, but this
mode does not independently force those bits. Register format template `0x412` names
ST/RGBAQ/XYZF2 ordering. Hardware interpretation follows the primary
[PS2SDK GS definitions](https://ps2dev.github.io/ps2sdk/gs__gp_8h_source.html);
game-specific values and selection come from the canonical ELF. This is a
sprite-oriented contract, not evidence of crossed world quads or small meshes.

## Embedded program, conditional execution contract

MPG chunk at ELF VA `44419c` (`4ac90400`) uploads201 instruction pairs to
pc400..4c8. Thus pc449 is ELF VA **4443e8**, and single-record tail pc4ae..4c4
is **444710..4447c0**. See [VU provenance](vu-contract.json). Instruction encoding
and MR32/FCAND/FTOI semantics were checked against primary
[PCSX2 opcode tables](https://raw.githubusercontent.com/PCSX2/pcsx2/master/pcsx2/DebugTools/DisVUmicro.h)
and [VU interpreter](https://raw.githubusercontent.com/PCSX2/pcsx2/master/pcsx2/VUops.cpp).
Original instruction pairs supply all game-specific constants.

Two column-matrix transforms use original X,Y,Z,W multiply-add order:
`c=M(vf1..4)*point`; `h=P(vf5..8)*c`. Shared entries pc2cf/30e load those
registers; CPU317770/317470 transfer matrices through VIF. No guessed camera
matrix is substituted for live values.

For ordinary finite values and positive projected W, the single-record contract is:

```text
Q = 1 / h.w
center = h.xyz * Q
halfSize = (min(sizeX*Q,56), min(sizeY*Q,56), 0)
corner0 = center + halfSize; corner1 = center - halfSize
STQ0 = (0,0,Q); STQ1 = (Q,Q,Q)
RGBA0 = RGBA1 = FTOI0(record.RGBA)
XYZ0 = FTOI4(corner0); XYZ1 = FTOI4(corner1)
clip = (.8*c.x, .8*c.y, c.z-1), compared with +/-abs(c.w)
second XYZF2 W mask = 0xc000 if any current clip bit in 0x3f, else 0
```

These are **two GS SPRITE corners**, a screen-aligned rectangle with shared
depth and a full0..1 texture rectangle expressed through ST/Q. The clip tests
the transformed center, not expanded corners. Half-size is capped at56 per
axis in projected coordinate space; no world-space size is inferred. No terrain
normal basis, yaw, crossed quads, mesh, random tint/scale, time, wind parameter
or UV animation occurs in this program.

Multi-record path pc468..4ad pipelines the same six output quadwords per point.
Upper/lower instructions execute in parallel: pc4bb stores previous STQ while
converting a corner. A sequential instruction replay would produce wrong output.
No cycle-accurate VU implementation is supplied. `vu_sprite` reconstructs the
ordinary single-record contract from **explicit transformed inputs**, with
FLOAT32_RECONSTRUCTION precision. VU FMAC/FDIV exceptional precision is UNKNOWN.

pc4c0..4c2 writes the cached GIF prototype and **NLOOP=2*count**. Each point
contributes ST/RGBAQ/XYZF2 twice, six quadwords, plus one batch tag. A CPU group
of30 gives181 quadwords before inherited state tags. CPU pool positions remain
fixed until retirement. Live inherited PRIM flags, exact VU residency and visual
parity require capture; they are separate from this embedded-code contract.
