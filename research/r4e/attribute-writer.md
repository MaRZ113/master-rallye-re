# R4E attribute writer evidence

`r4e_writer.py` uses parsed offsets as patch authority. Position edits call the unchanged R3 position patcher first, including AABB policy. Normal float32 records occupy 12 bytes per source vertex; UV records occupy 8 bytes per source vertex per set; color records occupy four raw bytes per source vertex. Every changed record emits field, source identity, offset, old hex, new hex. All other byte changes are forbidden by `audit_binary_diff`.

Blender maps loops to source IDs and uses strict 1e-6 corner agreement. It never averages a seam. Source-space normal vectors are exported from `mr_source_normal`; native Blender custom-normal APIs remain unused after prior crashes. Colors are preserved raw when unchanged, then quantized through the imported `MR Vertex Color` channels when edited. No BGR/RGB semantic assumption is needed for byte patching.

78/78 vehicle DX resources passed zero-edit identity with normals, UV sets and raw colors both in the library and through Blender 5.2.2. Synthetic isolated edits and Blender 5.2.2 source-indexed edits passed. E1/E2/E3 await game confirmation. Collision and render topology hashes are recorded per candidate.
