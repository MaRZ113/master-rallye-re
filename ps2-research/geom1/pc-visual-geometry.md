# PC visual baseline

Use the unmodified Course SDK4244fa0c4d878523c9947f54816bf377cdfb2589.
parse_course_dx supplies complete-disjoint validated render draws, vertex banks,
and draw_global_indices (including its established local-to-global winding rule).
Selected retail DX/TXT hashes must match frozen WATER1 identities. All physical
draws participate; no material filter limits the geometry search.

Source identities retain file hash, draw index/path/offset, local index span,
vertex base, textures in original slots, control words and source face indices.
Sidecar material candidates come from ordered texture tuples, not material-name
guessing. Multiple candidates are retained and classified unresolved.
course_source retains brace-backed TXT parentage and literal mesh names.
TXT Index/Size is not silently repurposed as DX face indexing. No source GXM is
required or substituted; optional historical GXM conclusions remain separate.
Normals/colors/UV are available from the SDK, but this position-based geometry
matcher does not certify UV/color equality or runtime appearance.
