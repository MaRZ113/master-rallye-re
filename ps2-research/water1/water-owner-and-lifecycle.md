# Owner, cache and lifetime

This is the general landscape mesh renderer with material mode switches and
small per-mesh auxiliary objects. There is no evidence requiring a separate
WaterRenderer class, procedural puddle manager or surface-spawn subsystem.

The mesh constructor `3ba868` initializes a0xf4-byte owner with vtable488328.
The shader handlers allocate16-byte auxiliaries and copy mesh center XYZ.
`38fac0` calls their virtual+14 during model post-load processing. Puddle
vtable4853c8 uses `320938`; water4853a0 uses `320f90 ->321098`; waterfall485378
has an empty load callback at327f20. `391d38` also builds the initial render
wrapper through renderer virtual+84=`31f2f8`.

`3bca80` obtains the scene instance's cache entry using mesh+d8 and calls
`361a58`. A cache entry tracks revision+0c, frame counter+10 and referenced
render-wrapper pointers+14/+18/+1c. Missing/invalid geometry is built through
renderer+64=`31f1c8` or rebuilt through+7c=`31f4e0`.

| Mode | Auxiliary frame flag virtual+1c | Callback virtual+c | Consequence |
|---|---|---|---|
| puddle |327e98 returns1|320c78|UV update once per changed renderer counter when cache is visited|
| water |327ee0 returns0|327ed8 empty|No per-frame water auxiliary UV update in this path|
| waterfall/waterall |327f28 returns1|321838|Two vertical UV layers update on changed counter|

`316808` stores the caller's unsigned counter at renderer+140 and derives the
water phase unless PauseMenuEnabled prevents that update. Counter identity is
not a measured seconds clock. Cache visitation and generic scene visibility
affect when work occurs; no independent water distance cutoff or spawn range
was found in the traced producer.

Mesh destruction `3bbeb0` releases auxiliary+24 and owned vectors/secondary
objects. Render wrappers and queued packets use shared reference counts;
`31cd98` empties queue groups after submission. The full generic cache eviction
policy and scene reload scheduler were not expanded into a new investigation.
Source puddle XYZ/topology are authored once in PSM; callbacks alter their
appearance rather than replacing the surface population.
