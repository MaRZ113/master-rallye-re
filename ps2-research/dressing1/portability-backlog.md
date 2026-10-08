# Evidence-qualified portability backlog

| Feature | Possible future work | Readiness / missing proof |
|---|---|---|
| Turkey hut subparts | REUSE_EXISTING_PC_MESH; material/placement metadata | NOT_READY: full object grouping and instance map |
| Turkey boat whole group | REUSE_EXISTING_PC_MESH; different placement of congruent source geometry | NOT_READY: exact PC source subset and independent authored boat owner |
| Turkey shrub | REQUIRES_DEEPER_PS2_RE; possible COURSE_VISUAL_GEOMETRY_PORT | NOT_READY: treeblend vertex/visibility interpretation and PC counterpart |
| Italy pinus | REQUIRES_DEEPER_PS2_RE; material-only or geometry work UNKNOWN | NOT_READY: shader/tree representation and component ownership |
| France dinghy | Conditional REPLACE_BAKED_STATIC_OBJECT + PC_RUNTIME_CONTROLLER | NOT_READY: exact PC partition and captured/derived pose relationship |
| Italy haybales | REUSE_EXISTING_PC_MESH / PC_RUNTIME_CONTROLLER candidates | NOT_READY: standalone/TXT/compiled relation; physics not reversed |

No feature is declared implementation-ready. GEOM1 Turkey3 puddle additions and
France/Italy shared water controls are unchanged; this phase does not redo their
renderer or conversion backlog. Source culling infrastructure can guide future
diagnostics, but it is not a universal instancing or LOD API.
