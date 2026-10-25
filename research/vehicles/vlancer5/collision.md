# Collision adjustment — current SDK and re-blend evidence

Read-only comparison against `master-rallye-re-blend` on 2026-10-23.
No current Lancer hull or donor physics was modified.

## Already available

`src/master_rallye/collision_writer.py` and `collision_scale.py` are byte-identical
in the vehicles and blend checkouts. The Vehicle SDK project loader already
supports `collision_translation`, `collision_scale` and `collision_center` for
`car.dx`. These are bounded operations on an existing validated finite tag101
convex hull, not a general collision mesh generator.

| Operation | Preserved / recalculated |
| --- | --- |
| Translation | Existing topology; translated proven geometry/centroids; refreshed marker-1339 bounds in project build |
| Positive per-axis scale around explicit/default centre | Detailed B geometry transformed; AABB A rebuilt in original corner order; vertex means, radius, face areas and marker-1339 bounds recalculated |
| Structural safety | Same serialized hull size; original triangle indices, edges, adjacency, face descriptors and loops unchanged; bounded binary diff audit |

Scale requires three finite factors in `(0,10]`. Unknown schemas and non-finite
hulls fail closed. Rotation, new topology, automatic convex decomposition,
arbitrary vertex fitting and new damage envelopes are not qualified features.

## Evidence and current check

Primary branch findings:

- `../master-rallye-re-blend/research/r4c/findings.md`: original translation
  qualification, including human runtime evidence within that experiment.
- `../master-rallye-re-blend/research/r4g/collision-scale.md` and
  `runtime-results.md`: 28/28 zero-edit hull identities, 27 finite hulls scaled
  non-uniformly, non-finite Forklift rejection; human-confirmed Astero +20% X
  wall contact with normal damage/physics. This evidence is vehicle/build scoped.

Current offline check: `collision-investigation.json` under the V5 private
output tests identity, hypothetical `(1.1,1,.95)` scale and `.01m` translation
in memory only, verifies bounded diff/topology validation, rejects zero,
negative, NaN and excessive factors, and verifies the real Lancer asset hash
did not change. Existing R4G synthetic tests pass in the full suite. This does
not qualify a particular fitted Lancer hull in-game.

## Integration boundary for a future fitment phase

Imported `scene_candidate` and `native_brake_scene_candidate` deliberately
reject collision transforms in the same project resource operation. Their
validators promise donor collision preservation. Therefore existing low-level
writers can investigate fitment today, while applying it to a converted scene
needs an explicit separate validated authoring stage and a recorded source
hash/transform. No bypass or schema weakening was added here.

A future adjustment should use the intended body envelope/contact points and
source coordinate frame, retain the original hull provenance, show overlays,
and then test contacts/damage in-game. Blind fitting to render bounds would
include antennas, mirrors, wings or presentation wheels and is unjustified.
Changing contact geometry can affect behavior despite unchanged physics tables;
it belongs with the planned physics/contact qualification phase.
