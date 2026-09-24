# Limited tag101 collision authoring

Tag101 rigid translation was confirmed by original-game testing in R4C. R4G adds positive source-space per-axis scale around a selected center:

    P' = C + (sx, sy, sz) * (P - C)

The writer transforms detailed Representation B vertices, rebuilds Representation A as the axis-aligned bounding box of transformed B, recomputes the A and B vertex-mean helper points, updates the base point and AABB-corner bounding radius, and recomputes each face scalar from its polygon's transformed primary-index loop. Triangle indices, edges, adjacency, face descriptors and face loops remain unchanged. The full DX and tag101 are reparsed and all changed bytes must lie in proven positional, radius, face-area, or marker-1339 bounds fields.

Scale is allowed only for finite validated existing tag101 hulls and factors in (0, 10]. The 27 finite corpus hulls passed non-uniform in-memory scale; the non-finite forklift/car.dx is preserved at zero edit and rejected for scaling. C1 uses a 20% lateral scale of Astero source X, with original visual geometry, and passed human wall-contact testing: the widened physical boundary registered while the visual mesh stayed unchanged, with damage and physics functioning normally. See ../research/r4g/runtime-results.md. Arbitrary hull creation, rotation, tag100 BSP, tag102 editing, and direct collision vertex sculpting remain unsupported.

In Blender, the imported car.dx object exposes source-space translation and per-axis scale values. Validate / Preview checks the transform without writing the original DX and refreshes read-only collision helpers; Reset restores source values. The project builder serializes approved transform values into a staged candidate. The panel shows center, radius, AABB, source hash and validation status.
