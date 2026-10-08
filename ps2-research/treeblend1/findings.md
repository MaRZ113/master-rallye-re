# TREEBLEND1 findings

**PS2-TREEBLEND1 STATUS: COMPLETE — bounded static/executable contract.**
**RUNTIME_VALIDATION: NOT_PERFORMED.** Live texture descriptors, inherited GS state and VU residency remain separate questions.

1. `treeblend` and `tree` have distinct registered material callbacks. They select renderer modes **2** and **6**, respectively. Both use authored visual strips and the common cached-mesh/VU path. Neither callback creates plants, a billboard basis, wind displacement or an LOD crossfade.
2. Mode 2 enables source-alpha blending, disables alpha testing and masks depth writes. Mode 6 disables blending, enables **alpha > 64 / KEEP** and permits depth writes. Both write ZTST=GEQUAL but preserve ZTE. This is a proved material-state difference, not a conclusion from the word “blend”.
3. `$alphatest()` occurs in the selected treeblend materials but does **not** describe their final GS state. Shader callback and renderer mode take precedence at the traced state producer.
4. Mesh+44 values 0.15/0.20 are **mip/strip-scale inputs**, not opacity. Mesh+3c also differs; its negation enters the texture-cache creation option. The exact downstream format/alpha consequence of that option is not closed.
5. Source color is `0xRRGGBBAA`. Loading clamps all channels to 2..254; caching multiplies by 0.5; selector 0 uses FTOI0. Authored A=255 therefore enters RGBAQ as 127 before texture combination. Normals are cached but not used by selector 0's coordinate/color computation.
6. France1 bush01 provides **24/24 strictly matched unsigned source triangles**, PS2 treeblend versus PC-sidecar tree. Its PC draw has 48 triangles: 24 unique unsigned triangles, each in both windings. Pinetree draw 283 has 320 triangle records but only 80 unique unsigned triangles. These counts are source representations, not plant populations or live polygon budgets.
7. Italy pinus2 and France pinetree image pixels match PC exactly under the explicit `flip-vertical` DXT row policy. France bush01 differs: PS2 64×64 / 89 stored alpha values; PC 128×128 / 15. Geometry, texture and material differences must be kept separate.

## Evidence-backed chains

Grades on these arrows are static evidence, never an emulator capture.

### A — Tree material

```text
ItalyS1 PSM tag2 at3706566, material at3706622 [BYTES]
 ->391d38/391690 material owner [BOTH]
 ->390d98 '$shader(tree)' extraction, interning,3a6c58 registry [EXE]
 ->3a75b8 registration /487d08 vtable /3ae710 callback [EXE]
 ->mesh+28=6,+2c=0,+44=0.2 [EXE]
```

### B — Treeblend material

```text
Turkey3 tag2 at3620664, material at3620723 [BYTES]
 ->same verified material owner/extractor/registry [BOTH]
 ->3a7468 registration /487d68 vtable /3ae618 callback [EXE]
 ->mesh+28=2,+2c=1,+44=0.15 [EXE]
```

### C — Geometry and textures

```text
original tag2 strips +52-byte vertices [BYTES]
 ->3900f0 runtime48 ->361a58/31f2f8/31f4e0 cache64 [BOTH]
 ->original mesh texture+34 ->3714e0 ->2fd7d0 ->2f84f0/2f9c80 [BOTH]
 ->mesh handle+dc /descriptor+e0 ->311c50 texture-state producer [EXE]
 ->UNKNOWN LINK: selected live descriptor, sampled alpha/CLUT representation
```

### D — Submission

```text
3bca80 mesh draw ->31d1b8 bucket /31d230 mode /31d1f8 texture key [EXE]
 ->31d250 enqueue ->31cd98 drain ->312610 GS templates /31c438 commit [EXE]
 ->31d7c8 four-qword REF/UNPACK,MSCAL0xf ->31e010 cached CALL [EXE]
 ->embedded selector0 transform/STQ/RGBAQ/XYZF2; XGKICK atmicro0xfa [EXE bytes/contract]
 ->316b88 chain flush ->30ea80 VIF1 hardware submission [EXE]
 ->UNKNOWN LINK: independently captured live micro-RAM and visible foliage frame
```

### E — PC control

```text
France1 PS2 bush01 tag2 3509209 /24 faces [BYTES]
 ->GEOM1 strict unsigned triangle correspondence /PC draw54 [BYTES]
 ->PC material tree, flags1/1/1/1 versus PS2 treeblend [BYTES]
 ->R4D_1 generic PC selector predicts _alphatest [STATIC_PC_INFERENCE]
 ->UNKNOWN LINK: captured PC course handler/state for this exact draw
```

See [shader registration](shader-registration.md), [render contract](tree-vs-treeblend.md), [case studies](course-case-studies.md) and [validation](validation.md). Machine-readable evidence preserves original addresses, masks, hashes and unknowns.
