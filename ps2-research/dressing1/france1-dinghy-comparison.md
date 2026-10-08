# France1 dynamic and baked dinghy control

Two original PS2 source references bind REDDINGHY/BLUEDINGHY.PSM to boat1/boat2,
gaEntitySpline, routes boatlist1/boatlist2, speeds2.5/2.7 and closed loops. Both
have authored identity matrices. Each model decodes60 source vertices, two
material meshes and24 faces; payload3420 ends at3416 withffffffff. Position-bank
hashes are identical. Local extents are2.603206/8.703737/8.204062 units.

The PC France1 landscape positively contains dinghy-textured compiled draws897
and904 with165/96 faces,31 whole-edge components, and11 hull/11 mast TXT names.
These representations do not count boats. TXT Index/Size are not validated DX
face ranges. No corresponding standalone spline Egg is found in the paired PC
scene. That bounded scene result does not imply absence of all PC boat geometry.

The fresh whole-model and four source-component unit rigid exact-face searches
find zero accepted anchor hypotheses against all261 PC dinghy-textured faces.
This excludes exact unit-rigid source topology in that search; alternative
tessellation, scale, partitions and the original potentially nonorthogonal
spline basis remain open. A selected PC component diameter13.5454 exceeds the
complete PS2 model diameter9.1370; GEOM1's unit-scale control is preserved.

```text
PS2 local model -> two independent authored spline-owned references
 -> route-published world matrix [AMBIENT1]
 -> UNKNOWN LINK: captured pose / exact static PC instance counterpart

PC TXT hull/mast names -> UNKNOWN LINK: direct TXT-to-DX face ownership
PC compiled draws897/904 -> positively present baked dinghy family
 -> UNKNOWN LINK: smallest safe static-instance partition
```

REPLACEMENT_STATUS: NOT_READY. Removing whole draws897/904 could remove multiple
unrelated source parts/placements. The smallest safe hide/replacement unit is
UNKNOWN. No route pose is fabricated for a France overlay map; authored Row3=0
is not substituted for an in-race pose. Dynamic capture and AMBIENT1 runtime
closeout remain deferred. No PC boat is hidden, replaced or animated.
