# Vehicle authoring (R4E)

R4E edits an existing vehicle DX against its original byte template. Import a vehicle folder in Blender, edit mesh vertices, MR UV layers, the source-space `mr_source_normal` attribute, or `MR Vertex Color`, then use **Export DX - Safe Attributes**. Save replacements outside the source vehicle directory. The old positions-only exporter remains available and unchanged.

Source IDs, triangle IDs, draw membership, vertex/face counts, and the source SHA-256 must match. The R3 safe AABB position check remains active. Per-corner UV, normal, and color values for one source vertex must agree; divergence is rejected as `REQUIRES_R4F_TOPOLOGY_WRITER`. No vertex split or topology rebuild occurs.

The writer patches parsed XYZ, normal, UV, raw four-channel color, and selected fixed material-state bytes. It preserves unchanged float bytes, local/global indices, collision, trailing data, texture names, and unknown material bytes. A complete binary diff is checked against field ranges and the result is reparsed. Source normals are an editable source-space attribute; Blender-calculated display normals are not exported. Existing non-finite source normal values remain untouched.

The classifier reports `NO_CHANGE`, `TEXTURE_CONTENT_ONLY`, `POSITION_ONLY`, `SAME_TOPOLOGY_GEOMETRY_ATTRIBUTES`, `SAFE_MATERIAL_STATE_CHANGE`, `COLLISION_TRANSLATION`, `MULTIPLE_SAFE_CHANGES`, `TOPOLOGY_CHANGED`, or `UNSUPPORTED`. A topology failure carries `REQUIRES_R4F_TOPOLOGY_WRITER`. Material alpha edits are staged by draw ID in the panel. The environment bit is available only when slot 1 already holds a helper; its writer effect awaits the focused R4E.1 test.

CLI: `mrtool validate-edit source.dx edit.json --output replacement.dx`. The JSON contains `source_sha256` and optional source-indexed `positions`, `normals`, `uv_sets`, raw `colors`, `material_alpha` and `material_env` maps. Omit output for validation only. The CLI never installs into the game.

## Human runtime status entering R4E.1

Positions (R3), UV editing (E1), vertex-color diffuse modulation (E3), same-size DXT content replacement (M1-M4), and alpha-family flag writing (E4) are confirmed by runtime. The original E2 normal edit changed only eight normals by about 15 degrees and was visually inconclusive. A stronger full-draw normal test is prepared. The environment feature writer is structurally and executable supported but awaits its own material-bit runtime test. Tag-101 translation is runtime-confirmed from R4C. Topology changes remain unsupported. See research/r4e/runtime-results.md.
