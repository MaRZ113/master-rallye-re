# Geometry editing results

Changed: explicit vertex/UV/normal edits, new/deleted vertices/faces, new meshes, face sections, independent duplicates, transformations, visibility and backing quads are supported by the new journal. Original source streams remain immutable. Stable face IDs prevent stale lamp/material ordinals after topology edits. Duplicate selects an explicit instance if one mesh is shared by several wheels.

Windows acceptance uses actual Qt Widgets and D3D9 on Dakar2 Pajero and an opt-in GT-derived Clio native snapshot. It moves/adds vertices, duplicates a wheel, adds backing geometry, assigns native material/environment references and brake Glow, saves/reopens, Undo/Redo, and compares two native builds byte-for-byte. Captures are private; native OFF/ON errors must fail the acceptance tool. A first Clio run exposed an insufficient32-artifact preview limit; it was raised to a bounded512 consistent with UVS textures and the final run was repeated. The earlier partial report is superseded.

This is an editable geometry/material fixture, not a new accepted vehicle. Backing/spare positioning remains a deliberate user modification; the three authentic internal Pajero spares remain in the source. No physics/collision edits are implied. Normal-based winding orientation is explicit and reversible, not a source-fidelity claim or global no-cull repair.

Remaining: transform gizmos, direct viewport face picking synchronization, arbitrary sculpting, full normal editing ergonomics, topology compaction, texture painting and Blender round-trip. Backend split/merge exists; GUI merge and scale/rotation ergonomics still need a later panel. Empty whole scenes cannot compile. The current UI is a pilot, not a complete replacement for every established Studio.
