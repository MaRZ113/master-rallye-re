# Compact geometry delta map

geometry-delta-map.json contains90 selected relation records, versioned schema1.
Source IDs use full file hash plus node offset or draw index; face IDs use strip/
newest-vertex or draw/triangle references. They survive tolerance changes. Relation
IDs include source/material/geometry relation; source identity remains separate.
Every record retains course, sources, coordinate frame, group owner, material axis,
counts/bounds/area, tolerance, coverage/residual, visibility qualification, evidence,
portability hypothesis and exact open questions. Full group/per-face relations
remain in ignored data/geom1, with no complete positions committed or packaged.

| Course | PS2 source triples | PC compiled triangles | PS2 exact | PS2 equivalent coverage | PS2 unmatched candidates | PC unmatched candidates |
|---|---:|---:|---:|---:|---:|---:|
|TURKEY3|40832|42237|36001|1|4478|971|
|FRANCE1|41817|64577|41620|18|117|1922|
|ITALY_S1|40479|46367|39682|13|690|1694|

Counts are representation-specific and directional. Repeated/alternative source
faces may map to the same opposite surface. These are not runtime draw, instance,
tree or live polygon counts. Full coverage is not a one-to-one group bijection.
Unmatched labels are candidates within the examined compiled landscapes, declared
tolerances and bounded matcher; they do not prove universal platform absence.
