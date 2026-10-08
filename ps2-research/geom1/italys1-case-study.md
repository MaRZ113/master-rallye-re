# ITALY_S1 course case

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

Shared water1329/1329 is PS2 puddle versus PC water, not extra geometry. Ordinary
ground node3758051 matches336 faces to draw530. Selected pinus2 node3706566 has
64 unmatched faces at every profile. PC hay-related draws dominate some unmatched
candidates (draw235:707 faces); this is not a haybale instance count or an automatic
absence from PS2, which has separate authored haybale references. No rigid-body
reverse or static-hay replacement was undertaken.
