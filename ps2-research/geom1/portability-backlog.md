# Future content-pack planning

| Evidence | Planning classes | Missing prerequisite |
|---|---|---|
|France/Italy shared water, different mode|MATERIAL_ONLY_PORT + RENDERER_ONLY_PORT|Material identity and existing WATER contract integration|
|Turkey3 authored puddle source additions|COURSE_VISUAL_GEOMETRY_PORT + MATERIAL_ONLY_PORT + RENDERER_ONLY_PORT|Course delivery and live selected subset; collision separately researched|
|Robust Turkey shrub/hut/boat and Italy pinus candidates|COURSE_VISUAL_GEOMETRY_PORT + REQUIRES_DEEPER_PS2_RE|Grouping/alternatives and relocated PC counterpart search|
|Exact geometry/literal same source material|NO_PORT_NEEDED|Runtime presentation may still differ|
|Near/partial/threshold-sensitive source changes|REQUIRES_DEEPER_PS2_RE + UNKNOWN|Avoid duplicating an existing altered/LOD surface|
|Standalone spline dinghy versus PC baked candidates|NEW_SCENE_OBJECT + PC_RUNTIME_CONTROLLER + REQUIRES_DEEPER_PS2_RE|Exact instance/shape mapping before REPLACE_BAKED_STATIC_OBJECT|
|Vehicle common local source subsets|REUSE_EXISTING_PC_MESH + UNKNOWN|Dedicated part/LOD/damage classification if later needed|

All classes are future research/architecture hypotheses, not implementation-ready
ports. Course SDK material/visual identity delivery may require COURSE_SDK_EXTENSION;
the final D3D8 draw alone does not guarantee those identities. Visual geometry and
collision are separate. No new collision structures were generated, and no visual
puddle automatically receives collision. COLLISION_RESEARCH_REQUIRED applies only
when later object interaction demands a proved physical counterpart.
