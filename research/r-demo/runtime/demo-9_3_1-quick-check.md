# Demo 9.3.1 quick check (historical protocol; superseded by R-DEMO2.1)

This was the original loader-check protocol. The 9.3.1 model/cache and GXI→DXT paths have since been tested with real ProcMon exports; the defined R-DEMO2.1 trace scope is closed. Current results are in `research/r-demo2/findings.md`, `model-cache-state-machine.md`, and `runtime/procmon-findings.md`.

The earlier human tests confirmed GXM→persistent DX generation and DX-only fallback for the observed complete/wheel cases. Controlled ProcMon traces later classified source/cache miss/build, source-missing compiled fallback, stale-cache rebuild, fresh-cache hit, and GXI→DXT miss. The tested source-newer/DX-newer timestamp orderings select rebuild/direct load. Both missing and equal timestamps remain **UNKNOWN**. DebugView produced **NO_OUTPUT_OBSERVED** in the tested 9.3.1 session; logger removal remains unknown.

The static EXE contains the GXI/DXT cache message family and a symmetric caller branch (**CONFIRMED_BY_EXE**). The historical scratch steps are retained only as provenance for the test plan; do not treat them as unrun work or as an instruction to repeat the completed tests.
