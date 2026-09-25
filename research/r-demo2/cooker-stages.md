# Model cooker stage order — DebugView-derived

The real 8.4.1 DebugView export is tab-delimited `sequence / relative time / PID / message`. Its source and stage records parse automatically. For Trooper `car.gxm`, the observed sequence is `Caching disabled` → `Reading GXM` → `Making dx model` → sort-plane insertion → vertex welding → convex hull → BSP decision → cylinder decision → 2D geometry → land database → object nodes → optimization. Stage completions are reported as `done` or `not necessary`; the land-database line is a single action message without a paired completion line.

The complete normal run confirms convex hull `done`, BSP and cylinder `not necessary`, and later stages complete. For the isolated `$chull` candidate, output ends at `Building convex hull -` after sort-plane and welder completion. No later stage appears. This localizes the runtime crash inside hull building; see `chull-crash.md` and `runtime/debugview-findings.md`.

This ordering is **CONFIRMED_BY_RUNTIME_TRACE** for the captured 8.4.1 Trooper path. It is not a claim that every resource takes identical branches.
