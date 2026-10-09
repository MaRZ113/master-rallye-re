# PC hay geometry, collision and baked-content correspondence

Read-only SDK at commit **4244fa0c4d878523c9947f54816bf377cdfb2589** decodes retail standalone **DataGx/Misc/Haybale/haybaletest.dx**. It has34 visual vertices, one draw,84 indices/28 visual triangles with hay-tga. PS2's selected visual mesh has60 source triangles; visual equivalence is not asserted merely from the shared family.

Standalone PC tag101 collision is1843..4415, with compatible base scalar1.5405999422, A8vertices/12triangles and B16/28. Independent PC-versus-PS2 collision comparison in **MODEL_LOCAL_IDENTITY** yields:

| Representation | Numeric/bitwise matching positions | Matches within0.0001 | Triangle index arrays |
|---|---:|---:|---|
| A | 1/8 | 8/8 | identical |
| B | 1/16 | 16/16 | identical |

No transform was fitted. This supports **REUSE_EXISTING_PC_MESH** for collision geometry compatibility, not equivalence of physics solvers or future exact behavior. Bounds, index hashes and source-file hashes are in pc-counterparts.json; full vertices are excluded.

Italy_S1 compiled landscape contains13 hay-texture draw candidates (867 totaldraws), while its TXT has175 hay-name leads (174moMesh/1moUnknown). Italy2 has16 candidate draws/223leads. Batches may contain multiple objects. A TXT name span is not a compiled triangle range.

**UNKNOWN LINK: selected PS2 Egg -> one removable PC baked instance.** Future work must recover per-instance grouping, triangle subset and associated collision before hiding or replacing static content. Deleting an entire hay-texture draw would be unsupported.
