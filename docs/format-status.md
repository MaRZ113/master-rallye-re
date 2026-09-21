# Format status (Phase R0)

| Family | Current interpretation | Confidence | Evidence / limit |
|---|---|---|---|
| `.dx` | Compiled 3D model data. Common header, vertex positions, normals, per-vertex colors, UV set(s), local `uint16` triangle indices, then unresolved draw/material records containing texture stems. | **HIGH** | All 160 share the first 12 bytes; five vehicle samples parse consistently. Draw-record addressing and hierarchy binding remain unresolved. |
| `.dxt` | Custom 20-byte wrapper around one uncompressed 32-bit BGRA pixel plane. It is not DDS and not DXT1/3/5 block compression. | **CONFIRMED** | All 6,960 files use magic `0x0000FEED`, word `1`, explicit dimensions, and exact size `20 + W*H*4`. |
| `.dxb` | Compiled 2D/font/sprite-batch-like resource. | **LOW** | All 113 begin `0x0000F001, 125`; strings such as `dummy_000_000` occur. The third word varies like an entry count, but record layout is not mapped. |
| `.hnt` | Plain-text dependency manifest for scene/frontend resources. | **CONFIRMED** | 54 readable files; 36 begin with `Model[...]`, 18 with `FSTexture[...]`; entries name models/textures used by adjacent scene XML. |
| `.sfl` | 20-byte header plus a single `W*H` byte raster plane. Semantic meaning is unresolved. | **HIGH** structural / **UNKNOWN** semantic | All 36 start with float32 `3.0`; offsets `0x04/0x08` are dimensions and file size is exactly `20 + W*H`. |
| `.txt` adjacent to `.dx` | Export/diagnostic sidecar carrying material, texture, hierarchy, and mesh-span metadata. | **HIGH** | 136 exact stem pairs; 147 of 149 TXT files start with `moModel(`. |
| `.xml` | Human-readable scene/config broker data and direct/indirect asset identifiers. | **CONFIRMED** | All 122 XML files parse successfully. |

## What R0 does not claim

- The unknown `.dx` draw/material record schema is not complete.
- TXT mesh `Index/Size` is not blindly equated with the binary global index
  buffer. It matches triangle count in `Astero/complete`, `Astero/wheel`, and
  `Ufo/complete`, but differs for sampled `car.dx` files.
- Binary indices are not yet safe to emit as global OBJ faces because draw
  records appear to apply local vertex bases.
- Texture word `0x08` is not labeled a checksum/hash without a proof.
- `.sfl` raster semantics, `.dxb` record semantics, and runtime loader behavior
  remain unresolved.
- No executable analysis was performed.
