# Bounded future backlog

| Feature | Evidence now | Planning categories | Missing interface / readiness |
|---|---|---|---|
| Hay authored model/shape | byte-identical PS2 aliases; compatible standalone PC convex A/B | REUSE_EXISTING_PC_MESH; COLLISION_RESEARCH_REQUIRED | visual shape equality and PC contact ownership still separate |
| ItalyS1/Italy2 static hay candidates | compiled hay-texture draws and TXT leads | COURSE_INSTANCE_MAPPING_REQUIRED; REPLACE_BAKED_STATIC_OBJECT | exact per-instance triangle/collision subset unknown |
| Tumbleweed model | original visual/convex payload and same controller | NEW_SCENE_OBJECT; PS2_ASSET_PORT; PC_RUNTIME_CONTROLLER | named PC counterpart not found; assets would need later conversion |
| Mass/MOI and momentum derivative | actual original consumer equations | PC_RUNTIME_CONTROLLER | host float32 is not bit-exact PS2 numerical parity |
| View/contact activation | fixed view gate + successful-contact wake | PC_RUNTIME_HOOK; PC_RUNTIME_CONTROLLER | live observer identity and cadence not captured |
| Visual pose publication | physical matrix -> Broker ->same entity en3d | PC_RUNTIME_HOOK | PC matrix owner/lifecycle interface not supplied by a draw proxy |
| Contact magnitude/material mix | selected impulse application proved | REQUIRES_DEEPER_PS2_RE | exact lambda, coefficients and general solver branches unresolved |
| First material visual pilot | earlier shared water-surface +material research | MATERIAL_ONLY_PORT; RENDERER_ONLY_PORT | separate authorization and constrained runtime validation required |

These are research readiness labels. None creates new PC objects, removes existing scenery, ports collision, or authorizes a contact implementation.
