# Demo Debug message catalog

This catalog distinguishes the user's observed live examples from exact templates found in demo EXEs. A complete session log has not yet been captured; frequencies and resource path distributions are **UNKNOWN**. The classifier `tools/runtime/demo_debug_classify.py` accepts only these literal templates and leaves other lines unclassified.

| Template or example | Source/evidence | Likely subsystem | Frequency | Resource path |
|---|---|---|---|---|
| `Loaded cached DX texture: [%s]` | User saw a matching line in demo 8.4.1; literal in both EXEs. **CONFIRMED_BY_RUNTIME** message occurrence and **CONFIRMED_BY_EXECUTABLE** template. | Texture cache/load branch, high confidence. | Not measured. | `%s` value may contain a texture path; exact live value not supplied. |
| `Shader [shader/particle_blend], entry 0 selected` | User observed this example in the 8.4.1 Debug window. **CONFIRMED_BY_RUNTIME** example. | Shader selection, high confidence for the line; exact rendering effect unproved. | Not measured. | None in the example. |
| `Reading GXI: [%s]` | Exact literal in both EXEs. **CONFIRMED_BY_EXECUTABLE**; no live occurrence supplied. | GXI source read branch, high confidence. | Not measured. | `%s` GXI path expected from format string. |
| `Saved cached texture: [%s]` | Exact literal in both EXEs. **CONFIRMED_BY_EXECUTABLE**; no live occurrence supplied. | Texture cache save branch, high confidence. | Not measured. | `%s` path not yet observed. |
| `Cached texture out of date or missing.` | Exact literal in both EXEs. **CONFIRMED_BY_EXECUTABLE**; no live occurrence supplied. | Cache status branch, high confidence. | Not measured. | No path in literal. |
| `Caching disabled.` | Exact literal in demo 8.4.1 EXE. **CONFIRMED_BY_EXECUTABLE**; no live occurrence supplied. | Cache setting branch, high confidence. | Not measured. | No path in literal. |
| `Can't load GXI [%s]` | Exact literal in both EXEs. **CONFIRMED_BY_EXECUTABLE**; no live occurrence supplied. | GXI load failure, high confidence. | Not measured. | `%s` GXI path if emitted. |
| `Cannot load cached texture: [%s]` | Exact literal in both EXEs. **CONFIRMED_BY_EXECUTABLE**; no live occurrence supplied. | Cached texture load failure, high confidence. | Not measured. | `%s` cache path if emitted. |

A clean Trooper selection/race session is needed to count each template and attach the actual resource paths. Other possible categories such as model loading, timing, frontend and race are intentionally unclassified until lines are observed.

## Later R-DEMO2 human stage fragments

The user reported these 8.4.1 live Debug-window fragments during GXM cooking: `Caching disabled. Reading GXM`, `Making dx model for model named`, `Inserting mCSortPlane nodes`, `Vertex welder`, `Building convex hull`, `Building BSP tree`, `Building cylinder`, `Parsing 2d geometry`, `Building land database`, `Inserting object nodes`, and `Optimising model`. The complete line syntax, ordering, frequencies and paths remain unknown until DebugView capture. `demo_debug_classify.py` now recognizes these as **fragments**, leaving unmatched lines unclassified. See `research/r-demo2/cooker-stages.md`.
