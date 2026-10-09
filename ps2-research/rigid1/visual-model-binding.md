# Physics and model drawing share an entity

Authored `en3d Model Name` selects the prop PSM resource, while `en3d Matrix` initializes the scene entity. Owner init receives that entity, passes it to physical body registration, and attaches the physics transform AI to the same entity. Collision attach resolves its en3d model resource. Transform consumption writes its en3d world matrix. These are distinct objects joined by the actual entity pointer and Broker key, not a hypothetical copied scenery instance.

Hay visual material is `Hay Bale $shader(dull)` with source texture slots commontextures\hay-tga and commontextures\hay_env-tga. Tumble visual material is `bigshrub $shader(treeblend)` with the original shrubtrig2 texture reference. Source references prove material bytes, not a new live texture-state capture.

The existing shared entity draw path **21ea20 ->3301c8 ->3302b8 ->330780**, verified in TREEBLEND1/earlier graphics phases, consumes model/world state. RIGID1 extends its ownership backward to a physical pose. It does not reopen GS/VU residency or claim final live packet confirmation.

The two families share physical controller/integrator but differ in authored mass/inertia, convex geometry and visual material. `treeblend` is visual classification; no wind or billboard physics follows from its name. AMBIENT1 publishes a spline pose and AMBIENT2 publishes bird procedural poses through related entity infrastructure; neither supplies this rigid-body integration algorithm.
