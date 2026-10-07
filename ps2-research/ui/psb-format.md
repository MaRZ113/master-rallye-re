# PS2 PSB F001 / 125 packed stream

All offsets below refer to the **decoded resource**, not TNG.000. Endian is
little. No disk pointers, aligned string pool, padding or color/alpha/order
fields were found in this supported stream. Signature/version are explicit
loader gates, not inferred by extension. Confidence: `CONFIRMED_BY_BOTH`.

| Offset | Width | Type | Meaning / evidence |
| --- | ---: | --- | --- |
| 0x00 | 4 | u32 | Signature 0x0000F001; loader `0x00386D28` checks equality |
| 0x04 | 4 | u32 | Serialized version 125 (0x7D); same loader checks equality |
| 0x08 | 4 | u32 | Mapping count N; reader `0x00387188` |
| 0x0C + 8i | 4 | u32 | Mapping key; runtime retains low u16 |
| 0x10 + 8i | 4 | u32 | Image index; runtime retains low u16 |
| 0x0C + 8N | 4 | u32 | Image count M; reader `0x00387258` |
| Sequential, per image | 4 | u32 | Triangle count; reader `0x00387328` |
| Then each triangle | 68+L | packed record | Fixed fields plus L ASCII bytes |

Mappings can be printable character keys (HUD-NUMS/NEWHUD) or numeric selection
keys (HUD-TEMPLATE/PACENOTES). They are not inherently font characters. Zero
counts are structurally representable. Offline bounds cap counts and reject
duplicate keys, high mapping bits, missing image indices and truncation.

For a triangle beginning at **T**:

| Offset from T | Width | Type | Meaning |
| --- | ---: | --- | --- |
| +0x00, +0x04 | 4 each | f32 | U0, V0 |
| +0x08, +0x0C | 4 each | f32 | U1, V1 |
| +0x10, +0x14 | 4 each | f32 | U2, V2 |
| +0x18, +0x1C | 4 each | s32 | Local X0, Y0 |
| +0x20, +0x24 | 4 each | s32 | Local X1, Y1 |
| +0x28, +0x2C | 4 each | s32 | Local X2, Y2 |
| +0x30, +0x34 | 4 each | s32 | Allocated atlas-cell Xmin, Ymin |
| +0x38, +0x3C | 4 each | s32 | Allocated atlas-cell Xmax, Ymax |
| +0x40 | 4 | u32 | Resource-name length L, excludes NUL |
| +0x44 | L | ASCII bytes | Texture stem, or exact sentinel `Null` |

Next record starts at **T+68+L**, with no rounding. For example,
MASTER_TEMPLATE's 19-byte names yield 87-byte records and unaligned subsequent
integers. Names are not NUL-terminated on disk. The loader reads L bytes into
a bounded local buffer and appends a temporary NUL. Supported offline names
are nonempty, at most 1023 ASCII basename bytes; unsafe names fail closed.

The six UV floats, six local-coordinate integers, four further integers and
length/string layout are confirmed by bytes and scalar ELF reads. Naming the
four further integers an **allocated cell** is `STATIC_INFERENCE`, supported
by all 418 textured records: UV bounds fit inside these padded regions. No
writer or GS upload path was used to claim the original authoring terminology.

Texture resolution uses the PSB's logical parent directory and texture stem
plus `.GXI`, normalizing case. `0x00387478` handles `Null` without a texture
lookup; non-Null names reach `0x002FD7D0`, which appends `.gxi`. The current
79 distinct stems across the ten banks resolve to 79 exact manifest entries.

Runtime storage differs from disk: a triangle occupies **0x48 bytes**, including
two leading resource handles; UV begins at runtime +8, vertices at +0x20,
cell bounds at +0x38. The image vector stores 12-byte objects. Width/height
helpers `0x003853D8` / `0x00385458` compute coordinate max-minus-min across the
three vertices of each 0x48-byte triangle. They corroborate local geometry;
they do not prove font advance, baseline or bearing semantics.

Two adjacent records are recognized as an offline quad only when they have
the same texture/cell, four rectangular position and UV corners, a shared
diagonal, complete coverage, and consistent X→U / Y→reversed-V mapping.
Other triangle geometry remains in the dump but cannot silently become a
rectangular diagnostic sprite. All 418 textured canonical triangles form 209
such quads; Null records are skipped for texture assembly.

The allocated cell is in PSB atlas coordinates: UV sample bounds multiplied
by GXI width/height must lie inside it. The cell includes padding and is not
necessarily the actual sampled rectangle. To select **raw GXI rows** use
`1-V`, as corroborated by complete glyph reconstruction. Integer local XY
positions describe image geometry around implicit (0,0); no separate named
pivot/anchor fields occur in the file.

Unknown handling:

- Non-Null UV must be finite and normalized; cell/texture bounds are checked.
- Null UV and cell fields retain exact byte ranges and u32 float bits. Their
  values are not assigned texture semantics. Canonical NUMS includes NaN/Inf.
- Any trailing bytes are retained in `unknown_ranges` by `dump`; `verify`
  refuses unrecognized trailing data.
- Unknown signature/version and malformed counts, names or ranges fail closed.
- Tint, alpha blending, draw order, final transforms, baseline/advance, dynamic
  image selection and screen anchors remain runtime questions. None is guessed
  from a zero integer or NaN payload.

`psb-manifest.json` records each section/record/string offset, exact UV bits,
signed geometry, resolved logical textures, aliases, provenance and unknown
ranges. It contains metadata only. There is no PSB writer or repacker.
