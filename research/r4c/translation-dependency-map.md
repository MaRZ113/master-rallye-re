# R4C translation dependency map

The confirmed tag-101 schema exhaustively enumerates every serialized float
and index field. This map is the safety gate for the first rigid translation.

| Field path | Classification | Evidence |
|---|---|---|
| `base_geometry.vertices[*]` | `TRANSLATES_BY_D` | One point equals representation-A vertex mean/AABB centre in 27/27; maximum mean error `5.927727639168478e-8`. |
| `base_scalar` | `TRANSLATION_INVARIANT` | Bounding radius in 27/27; lengths do not change under translation. Serialized float bytes remain unchanged. |
| `representation_a.geometry_a.vertices[*]` | `TRANSLATES_BY_D` | Eight AABB corner positions in 27/27. AABB min/max shift by D while extents remain fixed. |
| `representation_a.geometry_a.triangles[*]` | `TRANSLATION_INVARIANT` | Indices/topology; reader/writer schema and translation reparse. |
| `representation_a.geometry_b.vertices[0]` | `TRANSLATES_BY_D` | Equals A geometry-A arithmetic mean in 27/27; maximum error `5.927727639168478e-8`. |
| `representation_a.geometry_b.triangles` | `TRANSLATION_INVARIANT` | Empty in all validated hulls. |
| `representation_b.geometry_a.vertices[*]` | `TRANSLATES_BY_D` | Detailed convex-polyhedron model-space positions; pairwise distances and face areas remain invariant after D. |
| `representation_b.geometry_a.triangles[*]` | `TRANSLATION_INVARIANT` | Closed-hull topology indices. |
| `representation_b.geometry_b.vertices[0]` | `TRANSLATES_BY_D` | Equals B geometry-A arithmetic mean in 27/27; maximum error `5.8445629948292557e-8`. This resolves the former R4B unknown point sufficiently for translation. |
| `representation_b.geometry_b.triangles` | `TRANSLATION_INVARIANT` | Empty in all validated hulls. |
| `referenced_vertex_indices` | `TRANSLATION_INVARIANT` | Integer references into geometry A. |
| `edges` | `TRANSLATION_INVARIANT` | Integer vertex-index pairs. |
| face descriptor primary/secondary lists | `TRANSLATION_INVARIANT` | Integer vertex indices; secondary semantics remain unknown but cannot encode absolute coordinates. |
| `edge_face_adjacency` | `TRANSLATION_INVARIANT` | Integer face-index pairs. |
| `face_loop_indices` | `TRANSLATION_INVARIANT` | Integer edge indices. |
| `face_scalars` | `TRANSLATION_INVARIANT` | Polygon areas in 27/27; area is translation invariant and bytes remain unchanged. |

## Derived values

No serialized derived field requires recomputation for translation. AABB
minimum/maximum, centroids, pairwise distances, and hashes are recomputed only
as validation diagnostics. The bounding radius and face areas remain stored
unchanged.

## Unknown-position gate

**UNKNOWN position-dependent serialized fields: none in the confirmed tag-101
schema.** The unresolved secondary face-list semantics are integer references,
not coordinates. Runtime use of A versus B and the collision algorithm remain
unknown, but both positional representations are translated consistently.

This classification supports translation only. Rotation and scale remain out
of scope because their orientation/metric dependencies require separate work.
