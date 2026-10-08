# GEOM1 findings

PS2-GEOM1 STATUS: COMPLETE as a bounded static geometry bridge.
RUNTIME_VALIDATION: NOT_PERFORMED. No game/SDK/renderer writing occurred.

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

The known WATER1 answers reproduce exactly: Turkey3 0/745; France1 3586/3586;
Italy_S1 1329/1329. Three independently probed ordinary ground groups add247,
441 and336 exact source-face matches. The bridge is not water-specialized.

Strong new bounded candidates are Turkey3 node3429766 rustic Hut (139 faces),
3583641 boat1 (113),3620664 TURshrub2 (256), and Italy_S1 node3706566 pinus2 (64).
They remain unmatched at strict/baseline/relaxed profiles. This proves source
surface differences in the examined coordinates, not extra building/tree counts
or absence of the same object relocated elsewhere. France1 tyre node3564909
changes from128 unmatched at strict to47 at baseline to0 at relaxed: it must not
be advertised as extra PS2 tyres. A tree region also demonstrates coverage-based
matching, with classification sensitivity recorded explicitly.

France1 has actual PC dinghy geometry, while PS2 declares two spline-owned
standalone models. Blue/red standalone position banks are identical; material
payload hashes differ. PC hull/mast partitions and geometry differ at unit scale
for the measured component. A route-controlled instance correspondence remains
UNKNOWN. Optional Tata/Kia car-only feasibility finds1442/2016 and1739/2289
PS2 exact face matches to PC source car.dx, without equating all alternatives.

Recommend one next phase: PS2-DRESSING1, bounded ownership/alternative-group study
of the robust Turkey3/Italy foliage, hut and boat candidates. Do not begin it here.
