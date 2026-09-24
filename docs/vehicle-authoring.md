# Vehicle authoring (R4E)

R4E edits an existing vehicle DX against its original byte template. Import a vehicle folder in Blender, edit mesh vertices, MR UV layers, the source-space `mr_source_normal` attribute, or `MR Vertex Color`, then use **Export DX - Safe Attributes**. Save replacements outside the source vehicle directory. The old positions-only exporter remains available and unchanged.

Source IDs, triangle IDs, draw membership, vertex/face counts, and the source SHA-256 must match. The R3 safe AABB position check remains active. Per-corner UV, normal, and color values for one source vertex must agree; divergence is rejected as `REQUIRES_R4F_TOPOLOGY_WRITER`. No vertex split or topology rebuild occurs.

The writer patches parsed XYZ, normal, UV, raw four-channel color, and selected fixed material-state bytes. It preserves unchanged float bytes, local/global indices, collision, trailing data, texture names, and unknown material bytes. A complete binary diff is checked against field ranges and the result is reparsed. Source normals are an editable source-space attribute; Blender-calculated display normals are not exported. Existing non-finite source normal values remain untouched.

The classifier reports `NO_CHANGE`, `TEXTURE_CONTENT_ONLY`, `POSITION_ONLY`, `SAME_TOPOLOGY_GEOMETRY_ATTRIBUTES`, `SAFE_MATERIAL_STATE_CHANGE`, `COLLISION_TRANSLATION`, `MULTIPLE_SAFE_CHANGES`, `TOPOLOGY_CHANGED`, or `UNSUPPORTED`. A topology failure carries `REQUIRES_R4F_TOPOLOGY_WRITER`. Material alpha edits are staged by draw ID in the panel. The environment bit is available only when slot 1 already holds a helper; its writer effect is confirmed by the focused R4E.1 M1 runtime test.

CLI: `mrtool validate-edit source.dx edit.json --output replacement.dx`. The JSON contains `source_sha256` and optional source-indexed `positions`, `normals`, `uv_sets`, raw `colors`, `material_alpha` and `material_env` maps. Omit output for validation only. The CLI never installs into the game.

## Same-topology vehicle SDK v1 baseline

**FROZEN after R4E.1 human tests.** Positions (R3), normals (N1), UVs (E1), vertex colors (E3), same-size DXT content replacement (R4D.1), alpha-family flag writing (E4), environment feature writing (M1), tag-101 translation (R4C), and the full-tree Python `Data.sma` packaging workflow (E5) are runtime-confirmed. Exact vehicle dependency resolution and staging/bundling are implemented as part of that workflow. The earlier weak E2 normal test remains historically inconclusive; N1 resolved its runtime question. Unknown material fields stay raw. This paragraph records the R4E.1 same-topology baseline; R4F/R4G subsequently extended the full Vehicle SDK v1 to runtime-confirmed existing-draw topology writing. See research/r4e_1/runtime-results.md.

## R4F topology-changing experimental path

Blender now exposes a separate **Export DX - Topology Changing (Experimental)** action and an existing-draw face-assignment tool. It can add/remove vertices and triangles and split corners for UV, normal or color discontinuities within the original draw/material set. The old **Export DX - Safe Attributes** path is unchanged for same-topology files. A protected corpus zero-edit rebuild was 78/78 byte-identical; the F1 Astero +3-vertex/+1-triangle output is confirmed by human game testing. See docs/topology-authoring.md and docs/dx-render-rebuilder.md.

## R4G project workflow

Import Vehicle Folder labels car, complete and wheel roles. Export changed DX resources, stage same-size DXT replacements, preview limited tag101 translation/scale, then Save Vehicle Project, Validate Vehicle and Build Vehicle Mod. The existing same-topology exporter remains available. The topology exporter now recalculates marker-1339 bounds when new geometry exceeds donor coverage. B1/C1/P1/W1 later passed human runtime tests; see docs/vehicle-sdk.md, docs/vehicle-project.md and research/r4g/runtime-test-plan.md.
