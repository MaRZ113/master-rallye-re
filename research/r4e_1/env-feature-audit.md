# Environment feature writer audit

The R4D.1 paired tag-2 loader copies serialized DX core +0x24 directly into runtime material +0x34. The shader selector tests bit 0x4 for its environment family when Reflections is enabled. Its stage 1 uses camera-space normals. Human M1/M3 results prove whitepaint/chrome helper content is gated by Reflections, but do not alone prove fixed-mask writing.

Astero body draw 7 is tag 2: slot 0 `acamo64b-tga`, slot 1 `whitepaint-tga`, slot 2 Null; parsed mask 7 and flags `00000101`. The writer requires an existing slot-1 helper, recognizes only known mask bits, and patches the dword at `core_offset+0x24`. M1 changes bit 0x4 only, yielding mask 3.

M1 uses protected original source SHA-256 `b97949651ae1c0089a614beaa24f6b07bbea84735c70faf1570760a9aaa16d90`. Changed bytes: 1; unexpected ranges: 0. Texture references/content, positions, normals, UVs, colors, other masks, material flags, unknown controls, collision, topology and trailing bytes remain unchanged. Full reparse and Blender draw-7 toggle audit passed. Runtime effect remains unconfirmed.
