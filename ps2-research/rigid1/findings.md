# PS2-RIGID1 findings

**PS2-RIGID1 STATUS: COMPLETE — bounded static/executable contract.**
**RUNTIME_VALIDATION: NOT_PERFORMED.**

The two authored prop families use the same `gaAiRigidBody` wrapper, a separate registered physical body, convex model geometry, a 13-value momentum/quaternion state and a Broker-driven visual transform. This establishes actual physics and the visual pose consumer; it does not establish a live collision replay or a complete general contact solver.

The largest semantic correction is activation: authored `Trigger Distance` is parsed into owner+0x18, but `1a0258` does not read it. That function uses the first two view registry entries, shared visibility predicate `200550` with radius 4, and squared 3D distance <=10000. Initial bodies are paused. Nearness alone does not wake an initially settled body. A successful vehicle/paused-prop contact can wake it; proximity resumes a body previously paused because it became far away.

Mass becomes actual body mass and inverse mass. MOI becomes the diagonal local inertia matrix, then a world inverse inertia. Gravity is the proved force callback `(0,-g*m,0)`. No wind/RNG operation occurs in that callback or owner update; other force accumulator writers were not exhaustively excluded.

The PC standalone haybale already contains compatible two-representation convex geometry. Both hull vertex sets match under 0.0001 model-local source units and their triangle indices are identical. Baked Italian course hay-texture draws also exist, but individual Egg-to-static-mesh identity remains unknown. Restoring dynamics therefore requires an instance-mapping decision before hiding static content.

Start with [final-report.md](final-report.md), then [rigid-physics-contract.json](rigid-physics-contract.json), [elf-functions.json](elf-functions.json) and [instruction-probes.json](instruction-probes.json). All original proprietary geometry remains ignored.
