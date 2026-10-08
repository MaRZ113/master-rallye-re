# France1 standalone and baked dinghies

Two exact PackFS models, BLUEDINGHY/REDDINGHY.PSM, decode60 source vertices,
two material meshes and24 nonsuppressed source faces each. Their position-bank
SHA is identical. Both use commontextures/dinghy-tga; payload hashes differ.
Model-local width/height/length are2.603206/8.703737/8.204062 source units.

PS2 France1 declares red boat1 and blue boat2, owned by gaEntitySpline, routes
boatlist1/boatlist2, speeds2.5/2.7, closed loops. Authored translations are zero;
AMBIENT1 proves route-derived world-matrix publication, so Row3 is not a placement
oracle. Original scene-reference parameters are in object-evidence.json.

PC compiled draws897/904 contain165/96 dinghy-textured faces and31 diagnostic
shared-edge components. TXT has11 hull and11 mast name leads; these are mesh
records, not a proved boat population or direct compiled face mapping. PC actual
positions are course-source coordinates. No standalone PC spline Egg was found
in the paired scene. The static compiled geometry is positively present.

A selected PC component has point separation13.5454 units, greater than the
entire PS2 model's maximum9.1370. It cannot be the same unscaled rigid geometry.
Hull dimensions remain broadly compatible with a dinghy family, but topology,
scale, partition and instance mapping are unresolved; no transform was fitted.
Labels: PS2_STANDALONE_DYNAMIC_MODEL, PC_BAKED_STATIC_GEOMETRY,
GEOMETRY_DIFFERENT (bounded unit-scale proof), PLACEMENT_CORRESPONDENCE_UNKNOWN.
Future duplication is a real risk, but REPLACE_OR_HIDE_PC_STATIC_CANDIDATE is
conditional on an exact instance relation. Hiding whole draws897/904 could remove
unrelated static boats. No object was moved, hidden, replaced or animated.
