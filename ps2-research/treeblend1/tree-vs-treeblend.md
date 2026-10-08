# Tree/treeblend render paths, alpha, depth and ordering

All state statements below describe the proved mode producer in `312610`, not a selected live GS dump. The original jump table is at `4850c0`: mode2 reaches `313270`; mode6 reaches `3138ec` then the shared tail `31679c`; mode15 reaches `313e64`.

| Property | tree, mode6 | treeblend, mode2 | object, mode15 |
|---|---|---|---|
| Geometry | Authored visual strips, common cache | Same representation/path | Same representation/path |
| Effective primitive stream | 1 | 1 | 1 |
| Primary GIF reglist | 0x412: ST,RGBAQ,XYZF2 | Same | Same |
| Secondary reglist | 0xfff:NOP,NOP,NOP | Same | Same |
| PRIM low controlled bits | 0x3c: TRIANGLESTRIP,IIP,TME,FGE | 0x7c: same plus ABE | 0x3c |
| Texture TCC /TFX | 1 /0 MODULATE | Same | Same |
| Alpha test | Enabled; GREATER64; KEEP on failure | Disabled | Disabled |
| Alpha blend | ABE=0 | ABE=1 | ABE=0 |
| ZTST | 2 GEQUAL | 2 GEQUAL | 2 GEQUAL |
| ZTE | Inherited | Inherited | Inherited |
| Depth writing | ZMSK=0: permitted | ZMSK=1: masked | ZMSK=0: permitted |
| FBA_1 | 0 | 0 | 0 |
| Queue bucket | 0 | 1 | 0 |
| Handler mip coefficient | 0.20 | 0.15 | 0.50 |

No extra effective reflection/foliage overlay pass is selected. The common renderer still commits primary and secondary state structures, but the second geometry reglist contains NOPs. “One effective stream” does not mean only one DMA packet or no shared clipping packets.

## Original integer operations

The compact JSON retains keep masks and set bits separately. Unknown inherited bits are not evaluated as zero.

```text
GIF_TAG: (old & ffc07fffffffffff) |003e000000000000 treeblend
                                      |001e000000000000 tree/object
TEST:    (old & fffffffffff9c000) |0000000000041000 treeblend
                                      |000000000004040d tree
                                      |000000000004040c object
ZBUF:    (old & fffffffeffffffff) |0000000100000000 treeblend
                                      |0000000000000000 tree/object
ALPHA:   (old & ffffff00ffffff00) |0000000000000044
TEX0:    (old & ffffffe3ffffffff) |0000000400000000
TEX1:    (old & fffff000ffe7fe1e) |0000000000000160
FBA_1:   old & fffffffffffffffe
```

Full-entry PRIM prefix and interior mode block must be composed. The isolated interior-block decompilation shows a smaller `ffc3...` mask/+3c or+1c; treating that in isolation loses the common prefix and yields the wrong PRIM contract. `instruction-evidence.json` includes both the prefix and selected block stores.

`ALPHA=...44` sets A=Cs,B=Cd,C=As,D=Cd,FIX=0:

```text
output RGB = (Cs − Cd) × As /128 + Cd
```

That equation is active for treeblend's ABE=1. It is inactive for tree/object ABE=0. Texture alpha, vertex alpha, TCC/TFX, alpha testing and blending are separate operations. The actual As must be established after texture sampling/combination; stored GXI alpha is not automatically a captured GS blend coefficient.

TEX1 sets MMAG=1 and MMIN=5, corresponding to linear magnification and linear/trilinear mip filtering. MXL and dynamic K require the selected runtime descriptor/strip calculation; they are not filled with invented values. Authored clamp directives are preserved; final selected CLAMP addressing/format must be read with the actual descriptor/key and inherited state.

`3411d0` maps the global at `42df10` to GS register **0x4a,FBA_1**. It is not PABE. Global words at `42dea0/42deb0` are modified by the mode path, but their remaining shared AD identities and consequences are not completely mapped here. PABE, TEXA, FRAME and DATE/DATM remain inherited/UNKNOWN. TEST ZTE also remains inherited, so “GEQUAL selected” is not an unconditional assertion that depth testing is enabled in every live draw.

## Ordering

`3bca80` sends mesh+2c through `31d1b8` to renderer+160. `31d250` indexes the bucket vectors and material/texture key. Original R5900 MULT at `31d70c` has an explicit destination register; it supplies bucket×12 and must not be interpreted as generic MIPS LO-only multiplication.

The existing `31cd98` drain walks bucket0 before bucket1 **within one invocation**, grouping draws by the recovered material/texture key. Tree/object therefore precede treeblend in that drain. No camera-distance or back-to-front sort was proved. This does not establish that every treeblend draw is globally after every terrain/opaque draw across the whole frame.

Mode changes replace the controlled shared state bits; dirty-template commit happens through `31c438`. There is no proved per-foliage state-stack save/restore. Live frame order and inherited render context remain capture questions.
