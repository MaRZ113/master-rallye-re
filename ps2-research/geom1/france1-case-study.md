# FRANCE1 course case

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

Water3586/3586 reproduces all16 PC candidate draws. Ordinary ground node3613136
matches441 faces to draw519, checked with direct original-byte position samples.
Vegetation node3550808 has62 exact,10 coverage-equivalent and8 partial faces at
baseline; relaxed matches all80 exactly. This is a defensible spatial group,
not a plant count. Tyre node3564909 baseline unmatched47 becomes0 at relaxed;
those threshold-sensitive records are not evidence of additional tyre instances.
PC's larger source triangle inventory includes repeat/alternative coverage; the
two directional exact counts differ. PC dinghy geometry remains baked in draws
897/904; source-instance study is separate from the landscape count.
