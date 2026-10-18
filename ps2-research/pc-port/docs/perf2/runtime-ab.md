# PERF2 — runtime A/B

Kit: `dist/perf3.1` (superset: SPLIT-SCREEN1 + HUD-PORT4.1 + GROUND-PERF1 + PERF2/2.1 + PERF3 + PERF3.1 hotfix). Replace `d3d8.dll`, keep assets and INI, then add:

```
PS2PerfTiming=1
PS2PerfWindow=300
```

A = this DLL, B = the `dist/perf2.1` DLL (same INI; B ignores the timing keys).

## Runs (about one minute each, note the fps)

1. Split screen, `PS2SplitScreen=0`.
2. Split screen, `PS2SplitScreen=1`.
3. Quick Race with 8 cars, start grid and a pack of cars in view.
4. Single-car race (control).

## What to send back

fps A vs B for each run, and from the A runs the `session-*.jsonl` lines `ps2_perf_timing` (they name where the
time goes). Afterwards set `PS2PerfTiming=0`.
