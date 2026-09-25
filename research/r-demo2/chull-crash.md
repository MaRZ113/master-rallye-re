# Isolated `$chull` candidate: crash localized to convex-hull build

The user-provided 8.4.1 DebugView crash capture names Trooper `car.gxm`. Runtime messages show `Inserting moSortPlane nodes -` → `done`, then `Vertex welder -` → `done`, then `Building convex hull -`. The log ends there. No completion line follows and no later BSP, cylinder, 2D geometry, land database, object node, optimization, or cache serialization stage appears.

Classification: **CRASHED_IN_RUNTIME**. Last completed stage: vertex welder. Last started stage: convex-hull build. Crash localization: inside the convex-hull build stage (**CONFIRMED_BY_RUNTIME_TRACE**). The normal control trace runs the same stage to `done`, so the trace parser distinguishes the crash from an intentionally skipped stage.

The tested position-only `$chull` candidate hash for the 8.4.1 scratch asset was `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699`. The same-build 9.3.1 source-to-generated tag101 correspondence is documented in `gxm-to-tag101.md`, but does not identify the invariant that the edit violated. Vector A/B/C, indexed records, winding, plane offsets, bounds, hierarchy, and other dependent data remain candidates for static dependency analysis; no cause is promoted without evidence.

Do not produce a second blind `$chull` mutation. The 9.3.1 DebugView test yielded **NO_OUTPUT_OBSERVED**, not proof of logger removal.
