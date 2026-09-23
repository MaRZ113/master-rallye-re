# Normal writer audit

The parser reads 12-byte little-endian float32 XYZ normals at `VertexData.normal_offset`, immediately after positions. R4E patches `normal_offset + source_vertex_id * 12`. An unchanged entry retains its exact bytes; changed entries must be finite float32 and pass a full authorized-range diff.

The Blender importer keeps `mr_source_normal` in original source XYZ. Its display copy is rotated to Blender axes, but export reads the source attribute directly without a second transform. The full 78-resource Blender zero-edit export was byte-identical. A focused Blender 5.2.2 audit exported all 192 edited Astero draw-11 normals at their source IDs without native custom-normal APIs.

The active installed Astero file contained E2, so N1 uses the protected original backup, SHA-256 `b97949651ae1c0089a614beaa24f6b07bbea84735c70faf1570760a9aaa16d90`, matching R4E provenance. Draw 11 is tag 2, chromebar/chrome/Null, vertices 1820–2011, with no shared draw vertices. Source +Y is vertical. All 192 normals use `(x,y,z)->(z,y,-x)`, a right-handed +90-degree rotation around +Y. Every input/output length is approximately one. Float32 outputs match the rotation within 1e-7 and lengths within 2e-6.

N1 changed 1504 bytes in 192 authorized normal records; unexpected ranges: 0. Positions, UVs, colors, material fields, texture names, collision, topology and trailing bytes are unchanged. Full reparse passed. Runtime normal consumption remains unconfirmed.
