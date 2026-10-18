# SPLIT-GRASS1 — runtime A/B

Kit: `dist/split-grass1` (superset of PERF3.1 and HUD-PORT5). Replace `d3d8.dll`; the runtime kit also carries `PS2Hud/PS2HudTemplate.bin` and `PS2Hud/PS2HudTimeDiffs.bin` (grass/shrubs assets from earlier kits stay in `PS2Grass`).
`PS2Port.ini` keeps the PERF3.1 / HUD-PORT5 keys; needed:

```
PS2SplitScreen=1
Grass=1
Shrubs=1
Diagnostics=1
```

B = `PS2SplitScreen=0`: split screen stays PC (no PS2 grass there), everything else as PERF3.1.

## Runs

1. **Split-screen Quick Race, two players** on a course with grass (Turkey2, France1, ...): PS2 grass and shrubs
   in **both** halves, each matching its own camera, nothing drawn across the middle line, HUD/UI unchanged.
2. Drive both cars apart (one ahead, one behind): grass around each car in its own half.
3. Finish with one player: grass stays in both halves.
4. Frame time A vs B in split screen (grass is now drawn twice per frame).
5. Control: single-player Quick Race with Grass/Shrubs — unchanged from PERF3.1.

## What to send back

Screenshots of 1 and 2; from `session-*.jsonl` the lines `ps2_grass_draw` / `ps2_grass_gate` / `ps2_grass_build`
(with `"mode":"split_screen"`). If the grass is missing in split screen, the `ps2_grass_gate` reason and one F10
capture inside the split-screen race.
