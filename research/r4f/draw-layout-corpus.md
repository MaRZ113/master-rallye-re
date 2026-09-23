# R4F vehicle draw layout corpus

Source: protected original unpacked vehicle tree. Detailed per-draw evidence is in `draw-layout-corpus.json`.

78 resources, 1478 physical draws. Contiguous vertex ranges: 78/78; contiguous local-index ranges: 78/78; monotonic vertex bases: 78/78; nonoverlapping vertex ranges: 78/78; all declared vertices referenced: 1478/1478 draws. A 44-byte marker-1339 footer follows collision data in 78/78; its min/max matches the render-and-collision vertex union in 78/78, and its center matches that min/max midpoint in 78/78. Its other scalar is preserved raw.

Every physical draw has an inclusive `local_vertex_max` relative to `vertex_base`, an `index_start` and `index_count`, and an existing texture tuple. Every source vertex belongs to one declared draw range; every local-index entry belongs to one draw. The stored global table is exactly reconstructed by the parser for all 78 resources. Consequently adding vertices to a draw shifts later bases; adding triangles shifts later starts. These are corpus invariants for vehicle resources, not a claim about course DX or arbitrary synthetic layouts.

## Required layout answers

1. Draw vertex ranges are contiguous in 78/78.
2. No declared draw vertex ranges overlap in 78/78.
3. A source render vertex belongs to one declared draw range in this corpus.
4. `vertex_base` is monotonic in 78/78.
5. Draw record order follows vertex range order in 78/78.
6. Each draw stores inclusive `local_vertex_max`, so its span is `vertex_base..vertex_base+local_vertex_max`.
7. A draw gaining vertices updates total vertex count, each vertex array, its local maximum, later bases and the global table.
8. Yes: all later `vertex_base` values shift when an earlier draw gains vertices; later `index_start` values shift when it gains triangles.
9. The parsed tag-101/tag-102 collision structures use internal counted references, not render vertex IDs. The footer contains geometric bounds, not render indices. No other observed suffix field is a proven render-vertex index; unknown footer scalar stays raw.
