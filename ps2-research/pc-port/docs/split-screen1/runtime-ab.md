# SPLIT-SCREEN1 — runtime A/B

Kit: `dist/split-screen1`. Replace only `d3d8.dll`. Add to `PS2Port.ini` (keep the RACE-MODES1 keys):

```
PS2SplitScreen=1
```

B = `PS2SplitScreen=0`: split screen stays PC, everything else as RACE-MODES1.

## Runs

1. **Split-screen Quick Race, two players, no AI**: PS2 cars for both players in both halves, reflections, lamps,
   damage on each car.
2. **Split screen with AI opponents** (if the menu allows): opponents PS2 in both halves.
3. **Finish**: one player finishes first, the other keeps driving — both stay PS2.
4. Frame time A vs B in split screen.
5. Control: single-player Quick Race and a cup race unchanged.

## What to send back

Screenshots of 1 and 3; `session-*.jsonl` lines with `ps2_fleet_participants`, `ps2_fleet_car_replacement`,
`ps2_fleet_car_fallback`; one F10 capture inside the split-screen race if cars stay PC.
LAN: if you can start a LAN race (two PCs), an F10 capture from it with `Diagnostics=1`.
