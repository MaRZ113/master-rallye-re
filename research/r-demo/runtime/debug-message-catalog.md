# Demo Debug message catalog (historical template inventory)

This catalog preserves exact EXE strings and earlier live examples. It is not a complete frequency or path census. R-DEMO2.1 DebugView captures establish the 8.4.1 live cooker stage sequence; 9.3.1 had **NO_OUTPUT_OBSERVED** in the tested session. See `research/r-demo2/runtime/debugview-findings.md` and `cooker-stages.md` for parsed runtime evidence.

| Template or example | Source/evidence | Bounded interpretation |
|---|---|---|
| `Loaded cached DX texture: [%s]` | User observed a matching 8.4.1 line; literal in both EXEs (**CONFIRMED_BY_RUNTIME**, **CONFIRMED_BY_EXE**) | Cached texture load diagnostic; complete path/frequency census unavailable |
| `Shader [shader/particle_blend], entry 0 selected` | User observed this 8.4.1 example (**CONFIRMED_BY_RUNTIME**) | Shader-selection line; rendering effect is not established by the line alone |
| `Reading GXI: [%s]`; `Saved cached texture: [%s]`; `Cached texture out of date or missing.` | Exact strings in both EXEs (**CONFIRMED_BY_EXE**) | Static source/cache diagnostics; do not claim each was emitted in a captured run unless the parser report says so |
| `Caching disabled.` | Exact string in 8.4.1 EXE (**CONFIRMED_BY_EXE**); live cooker status appears in the 8.4.1 stage capture | Tested 8.4.1 model-cooker path reports caching disabled |
| `Can't load GXI [%s]`; `Cannot load cached DX texture: [%s]` | Exact strings in both EXEs (**CONFIRMED_BY_EXE**) | Failure-branch templates; emission/frequency unmeasured |

The 8.4.1 stage trace includes observed fragments for reading GXM, making the DX model, inserting sort planes, vertex welding, building the convex hull/BSP/cylinder, parsing 2D geometry, building the land database, inserting object nodes, and optimizing. Full runtime classification and the crash endpoint are in `research/r-demo2/cooker-stages.md`; this old catalog does not replace that report.
