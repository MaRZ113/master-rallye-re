# Model cooker stage order — DebugView-derived

The real 8.4.1 DebugView export is tab-delimited `sequence / relative time / PID / message`. Its source and stage records parse automatically. For Trooper `car.gxm`, the observed sequence is `Caching disabled` → `Reading GXM` → `Making dx model` → sort-plane insertion → vertex welding → convex hull → BSP decision → cylinder decision → 2D geometry → land database → object nodes → optimization. Stage completions are reported as `done` or `not necessary`; the land-database line is a single action message without a paired completion line.

The complete normal run confirms convex hull `done`, BSP and cylinder `not necessary`, and later stages complete. For the isolated `$chull` candidate, output ends at `Building convex hull -` after sort-plane and welder completion. No later stage appears. This localizes the runtime crash inside hull building; see `chull-crash.md` and `runtime/debugview-findings.md`.

This ordering is **CONFIRMED_BY_RUNTIME_TRACE** for the captured 8.4.1 Trooper path. It is not a claim that every resource takes identical branches.

## Demo 9.3.1 static stage xrefs (R-DEMO2.2)

A separate headless Ghidra project analyzed the demo 9.3.1 EXE (SHA256 `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680`); retail Ghidra exports were excluded. `FUN_005430c0` configures the vertex-welder tolerance field to float32 `0.01`, logs the convex-hull stage, then calls `FUN_005de630`. That function resolves a `$chull` node, recursively collects child triangle positions through `FUN_005df370`, then dispatches to hull-processing functions. This is targeted static control/dataflow evidence, not a 9.3.1 runtime trace and not a complete raw-GXM field mapping.

The prior 8.4.1 captured control and crash traces remain the runtime-stage evidence. No new runtime test was run in R-DEMO2.2.
