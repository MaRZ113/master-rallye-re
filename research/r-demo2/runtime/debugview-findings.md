# DebugView findings — demo 8.4.1 and 9.3.1

The supplied raw DebugView logs use tab-delimited sequence number, relative time, PID, and message columns. `tools/runtime/demo_debug_classify.py` parses process IDs dynamically, preserves ordered messages, extracts GXM source paths and `moModel` names, pairs cooker-stage starts with `done` / `not necessary`, and marks an unclosed final stage as incomplete. Raw logs stay ignored under `.research-output/r-demo2/debugview/`; parsed full-message JSON there is also ignored.

## Demo 8.4.1 normal capture

The normal capture uses PID 24172; the separate `$chull` crash capture uses PID 16440. No PID is hardcoded. For the observed Trooper `car.gxm` compilation, the ordered stages are:

1. `Inserting moSortPlane nodes` — done
2. `Vertex welder` — done
3. `Building convex hull` — done
4. `Building BSP tree` — not necessary
5. `Building cylinder` — not necessary
6. `Parsing 2d geometry` — done
7. `Building land database for model: [vehicles\trooper\car]` — emitted as a single non-paired action line
8. `Inserting object nodes` — done
9. `Optimising model` — done

The trace also directly records `Caching disabled.`, the source path, and `Making dx model for moModel named : [vehicles\trooper\car]`. This captures the original runtime stage order for the tested source path (**CONFIRMED_BY_RUNTIME_TRACE**). The 8.4.1 OutputDebugString channel is **CONFIRMED_BY_RUNTIME**.

## Demo 8.4.1 `$chull` crash capture

For the Trooper `car.gxm` candidate, `Inserting moSortPlane nodes` and `Vertex welder` complete. `Building convex hull -` is the final message; its completion message is absent, and no later BSP, cylinder, 2D, land database, node insertion, optimization, or cache-save stage appears. The parser reports `CRASH_DURING_CONVEX_HULL_BUILD`: last completed stage `Vertex welder`; last started stage `Building convex hull`; final message `Building convex hull -`. This is **CRASHED_IN_RUNTIME**, localized inside the convex-hull stage by **CONFIRMED_BY_RUNTIME_TRACE**. No second hull mutation was attempted.

## Demo 9.3.1 channel

The user observed no DebugView output for the tested 9.3.1 run: **NO_OUTPUT_OBSERVED**. This does not establish logger removal; sink, build flag, configuration, call path, or logger implementation remain **UNKNOWN**.
