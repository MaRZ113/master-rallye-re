# Race cycle plan (COURSE-RENDER-FIX1)

One car for the whole run. In every entry: start the race, wait for the countdown, drive straight for ten seconds,
steer left and right once, then Esc -> Quit to the menu and pick the next course. Do not restart the game between
entries. If a screenshot is wanted (ReflectionDebug=2 shows the env target at the top of the screen) take it at
second 5 of the entry.

| # | course | kind | what it shows |
|---|---|---|---|
| 1 | SpainS2 | converted | black reflection candidate; PS2 water (12 triangles); boats (spline objects); grass |
| 2 | Italy3 | stock | control: stock PC course on the same car; spline gate must say stock course, grass/shrubs |
| 3 | Turkey3 | converted | PS2 water (26 triangles), grass and shrubs, converted course |
| 4 | France1 | converted | converted course with boats; waterfall |
| 5 | SpainS2 | converted | second entry of the candidate: every effect must come back |
| 6 | Italy3 | stock | second control entry |
| 7 | Turkey3 | converted | second entry: water, grass, shrubs |
| 8 | Spain2 | stock | stock course with water (PS2 water on retail geometry) |
| 9 | SpainS2 | converted | third entry |
| 10 | Turkey2 | converted | converted course, puddles |
| 11 | ItalyM1 | stock | stock control |
| 12 | Turkey3 | converted | third entry |
| 13 | SpainS2 | converted | fourth entry |
| 14 | France1 | converted | second entry |

Each entry must last at least 600 frames to be judged.

After the run:

    python tools/analyze_race_lifecycle.py --diag logs/ps2diag-*.jsonl --session logs/session-*.jsonl --md report.md --min-races 12
    python tools/race_cycle_plan.py check --plan plan.json --diag logs/ps2diag-*.jsonl
