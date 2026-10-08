# Conditional selection and LOD limits

The four source paths all use tag1/tag6/tag5/tag2. No alternate-child LOD wrapper,
per-leaf distance threshold or named variant is present in those paths. Tag6 is
proven to select/cache child indices using model region data and camera inputs.
Bounding wrappers apply view/range tests. These are selection/culling mechanisms;
calling them a multi-resolution LOD system would require another proof.

The reproduced200550 test uses r>0 and d=center-view.position. If the graphics
virtual+6c range descriptor exists, require
dot(d,d)<=(descriptor.range+r)^2 and -dot(view.direction,d)>=-r.
For each of four side normal triples at view+8, require dot(d,n)<r. Equality is
accepted for range/direction and rejected at the side boundary. If the range
descriptor is absent, its distance and direction tests are skipped; side tests
still apply. Relevant original instructions are2005dc..200690.

This is a group sphere test, not a grass/tree-specific fade, nor an instance
creation/destruction rule. Radius/center are in the wrapper+28/+1c; the range is
read from a shared descriptor+28. No fixed course distance is inferred.
dressing_runtime.sphere_eligibility preserves finite float32 arithmetic order
and marks FLOAT32_RECONSTRUCTION. Actual bound values/view fields are not captured.

3c15d8/26bc78 interior predicates remain partially decoded. Selected live groups,
mask state, generation initialization/rollover and simultaneous visibility are
UNKNOWN. Source faces across all branches are retained without a live polygon
budget or alternate-object count. No GRASS2/WATER2/REFL2 capture was attempted.
