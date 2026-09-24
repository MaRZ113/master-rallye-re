# R4G human runtime results

The project owner tested four isolated Astero candidates in the original Master Rallye runtime. These observations were reported after the automated R4G candidate package was generated. The original validation files describe pre-runtime state and remain unchanged.

| Probe | Result | Original-game observation |
|---|---|---|
| B1, expanded car bounds | PASS | Triangle beyond donor bounds visible; accepted bounds; visual damage/deformation; primary collision unchanged; normal physics. |
| C1, tag101 per-axis scale | PASS | Widened wall-contact boundary with stock visual mesh; collision, damage and physics work. |
| P1, complete.dx topology | PASS | Added hood triangle visible in menu/presentation; model otherwise normal. |
| W1, wheel.dx topology | PASS | Added triangle on all four instanced race wheels; steering, suspension and wheel physics unaffected. |

The B1, C1, P1 and W1 candidate SHA-256 values are recorded in runtime-results.json and the original runtime-test-plan.md. R4F F1 separately confirmed new car.dx vertices and triangle, original collision, external/internal procedural damage, breakable glass and normal wheels; see ../r4f/runtime-results.md.

**MASTER RALLYE VEHICLE SDK v1 — RUNTIME-CONFIRMED BASELINE.** The baseline covers the tested existing-donor draw/material authoring workflow. It does not add arbitrary draw/material/string creation, a collision-hull-from-scratch generator or extra EXE vehicle slots. Rare and unknown auxiliary semantics remain optional future work.
