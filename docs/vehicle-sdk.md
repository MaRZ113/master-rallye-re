# Vehicle SDK v1 development baseline

R4G is the last planned vehicle-core hardening phase. The F1 Astero race car.dx topology edit is confirmed in the original game. B1 expanded bounds, C1 collision scale, P1 presentation topology, and W1 wheel topology are WAITING FOR HUMAN. Do not call the full Vehicle SDK v1 runtime-confirmed until all four pass.

## Supported authoring path

- Import a vehicle folder in Blender. Imported objects show RACE BODY (car.dx), PRESENTATION (complete.dx), and WHEEL TEMPLATE (wheel.dx) roles.
- Edit existing-draw triangle geometry, source normals, UVs, vertex colors, and approved material alpha/environment controls. All faces must use an existing donor draw/material identity. The same-topology byte-patch path remains available.
- The topology exporter recompiles render vertices, local and global indices and draw spans. If geometry exceeds stored bounds or sphere coverage, it recomputes marker-1339 bounds.
- Tag101 collision translation is runtime-confirmed. Positive per-axis scale around a chosen source-space center is structurally validated on 27 finite corpus hulls and awaits C1 runtime confirmation. The known non-finite Forklift hull is rejected for scale.
- Export a VehicleProject JSON, validate it, then build a staging tree. Texture content replacement keeps original DXT dimensions/header. Optional full-tree Data.sma packaging uses an explicit destination and never overwrites an existing archive.

Commands: py -3 tools/mrtool.py validate-vehicle project.json and py -3 tools/mrtool.py build-vehicle-mod project.json --output output. See vehicle-project.md, vehicle-bounds.md, and collision-authoring.md.

## Deliberate v1 limits

No new draw/material records or texture strings, no empty draw, no new UV-set count, no collision topology/BSP reconstruction, no extra EXE vehicle slots, no track support. Wheel and presentation topology, expanded bounds and collision scale still need human runtime tests. The project file records donor source SHA-256 values and the validator refuses unsupported fields.
