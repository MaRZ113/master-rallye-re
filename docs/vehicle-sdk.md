# MASTER RALLYE VEHICLE SDK v1 — RUNTIME-CONFIRMED BASELINE

R4F F1 and R4G B1, C1, P1 and W1 passed original-game testing. The full existing-donor vehicle authoring baseline is frozen at v1. See the separate human evidence in ../research/r4f/runtime-results.md and ../research/r4g/runtime-results.md.

## Runtime-confirmed capabilities

- Topology-changing render writing for car.dx, complete.dx and wheel.dx; the wheel edit appears on all four runtime-instanced wheels.
- Position, source-space normal, UV and vertex-color writing.
- Same-dimension DXT content replacement.
- Alpha and environment material-state writing on established material fields.
- Expanded render bounds through marker-1339 recomputation.
- Tag101 rigid collision translation and finite existing-hull per-axis scale.
- Preserved procedural vehicle damage and breakable glass in the tested car edits.
- Dependency resolution, vehicle staging/bundling and Python full-tree Data.sma packing with controlled overrides.

## Authoring workflow

Import a vehicle folder in Blender; car.dx, complete.dx and wheel.dx show distinct roles. Edit geometry only within existing donor draw/material identities, or use the same-topology attribute path. The topology exporter rebuilds render arrays and indices and recomputes marker-1339 when needed. Finite tag101 hulls support translation and positive per-axis scale. Save a VehicleProject, validate it, then build a separate staging tree. Same-dimension DXT replacements and optional full-tree SMA output use explicit destinations. The project validator checks donor hashes, roles, draw/material identity, bounds, collision and dependencies. See vehicle-project.md, vehicle-bounds.md, collision-authoring.md and ../research/r4g/custom-vehicle-readiness.md.

CLI: py -3 tools/mrtool.py validate-vehicle project.json; py -3 tools/mrtool.py build-vehicle-mod project.json --output output.

## SDK v1 limits

- Existing donor draw/material identities and texture strings only; no arbitrary new draw, material or string creation.
- No collision-hull-from-scratch generator, tag100 BSP rebuild or arbitrary collision topology.
- No extra vehicle slot EXE patch and no track support in this vehicle baseline.
- Rare or unknown auxiliary semantics remain optional future research.
- The known non-finite Forklift tag101 hull remains rejected for scaling; it is preserved at zero edit.

## Future addon qualification boundary

The existing-donor SDK v1 baseline does not close the generic addon vehicle
roadmap. The agreed phases are R5V-G.1 unlock architecture, R5V-G.2 vehicle
audio identity/sound family, R5V-H AI pools, R5V-I multi-slot registry
expansion with a real added T2 vehicle as a required qualification, then R5V-J
the generic addon tool/SDK. Before that SDK can be called complete, an addon
must select/configure its sound family independently of model/physics identity
and pass a T2 addon vehicle qualification. F.2f does not implement these
features.
