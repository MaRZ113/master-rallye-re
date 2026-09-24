# Experimental vehicle topology authoring (R4F)

The **SAME-TOPOLOGY VEHICLE SDK V1 BASELINE** is frozen and runtime-confirmed. Its **Export DX - Safe Attributes** command still uses the original byte-patch writer. **Export DX - Topology Changing (Experimental)** is a separate render-core rebuild path. The F1 Astero `car.dx` +3-vertex/+1-triangle candidate is **CONFIRMED_BY_RUNTIME**; see `research/r4f/runtime-results.md`.

## Blender workflow

1. Import an original vehicle DX or vehicle folder. Keep the source template available and unchanged. Work on one imported mesh object with identity object transforms.
2. Edit mesh topology in Blender. Triangulate all faces explicitly. Quads and n-gons are rejected. The exporter does not triangulate or auto-recalculate normals.
3. Use existing `MR UV <n>` layers, `MR Vertex Color`, and source-space `mr_source_normal`. New vertices need a finite nonzero source-space normal, four color bytes, and every existing UV set. Duplicating a nearby face copies these attributes and is a safe starting point.
4. For a new or duplicated face, select it in Edit Mode, choose an **Existing draw ID** from the panel list, then press **Assign Selected Faces to MR Draw**. The command stores valid draw membership, marks duplicate faces as generated, and records parent-source IDs for newly duplicated points. New faces without an explicit draw are inferred from their Blender material only if that material belongs to exactly one existing MR draw. Ambiguous or missing assignments fail export. No new draw/material/string can be created.
5. Choose **Export DX - Topology Changing (Experimental)** and a fresh output path outside the source tree. The file selector shows source/compiled vertex and triangle counts, generated/split counts, changed draws and collision preservation. The output must be tested separately from the original.

The exporter compiles triangle corners in draw-ID order, then Blender polygon and loop order. Within each draw, retained source IDs are ordered by original ID; generated point IDs follow in stable Blender point order and first corner occurrence. The key includes Blender point identity plus position, source normal, raw color and every UV set. Different corner values split into separate serialized vertices. It does not weld independent points, reorder triangles, optimize caches, repack UVs or simplify geometry.

`mr_source_vertex` remains source provenance for unchanged imported points. `mr_generated_vertex` and `mr_parent_source_vertex` are tooling-only point metadata for duplicated/generated geometry. The compiler also distinguishes a corner split from an original source vertex. None of these provenance IDs is serialized into DX.

## Safety and limits

Existing draw records, material/texture names, group labels, collision bytes and the marker-1339 bounds footer are copied. The writer updates only render arrays, indices, global table and the four proven draw range fields. All new positions must stay inside the original combined render/collision AABB. Existing draw sets and UV-set count are fixed; deleting every triangle from a draw, adding a material/draw, editing collision, or moving outside original bounds requires later research. Every compiled vertex must be referenced by a triangle. Local indices are uint16 (at most 65,536 vertices per draw). Unknown material controls remain raw.

The writer reparses its output and verifies all indices, draw identities, material fields, prefix, collision and suffix. A full protected vehicle-corpus zero-edit dry run was byte-identical for **78/78** resources; an Astero Blender +3-vertex/+1-triangle export matched the direct F1 writer SHA-256. Human testing then confirmed the new triangle in-game with normal collision, damage, glass and wheels. See `docs/dx-render-rebuilder.md` and `research/r4f/runtime-test-plan.md`.

## R4G expanded bounds

The topology rebuilder offers an explicit recompute-bounds mode. It permits finite sane-size new vertices beyond the donor AABB, computes marker-1339 extrema/center/covering radius, reparses the output and preserves collision topology. Blender chooses this mode when geometry exceeds the donor box or sphere; the published R4F in-bounds path remains byte-compatible. Astero B1/P1/W1 candidates passed original-game human tests; see research/r4g/runtime-results.md. See docs/vehicle-bounds.md.
