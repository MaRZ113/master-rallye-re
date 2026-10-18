# RACE-MODES1 — runtime A/B

Kit: `dist/race-modes1`. Replace only `d3d8.dll` (assets and INI from FLEET-ALL-CARS2). Add to `PS2Port.ini`:

```
PS2RaceAllModes=1
PS2FrontendAllCars=1
```

(keep `RaceFleet=1`, `PS2FleetAllCars=1`, `FrontendModel=2`, `Reflection=4`, `Diagnostics=1`).
B = both new keys `0` (same DLL): behaviour of FLEET-ALL-CARS2, except that the Challenge preview no longer
slows down (the second preview car stays PC).

## Runs

1. **Master Rallye, Rallye Cup, Invitation, Challenge** — one race each: PS2 cars (player and opponents),
   reflections, PS2 HUD/map if enabled, finish phase. Log: `race_epoch_snapshot` still says
   `unsupported_race_or_player_configuration` (baseline), the PS2 paths run with `ps2_competition_mode_certificate`
   (look for `ps2_fleet_participants` and `ps2_fleet_car_replacement` in that race).
2. **Replay** after a Quick Race and after a cup stage: PS2 cars during playback, all camera views of the replay.
3. **Challenge preview**: both cars PS2, no slowdown; switch challenges back and forth. With B: no slowdown,
   one car PS2, the other PC.
4. Quick Race / Attract control: unchanged.

## What to send back

Screenshots per mode, fps in the Challenge preview (A and B), and `session-*.jsonl` lines with
`ps2_fleet_participants`, `ps2_fleet_car_replacement`, `ps2_fleet_car_fallback`, `ps2_frontend_model_gate`,
`ps2_frontend_model_replacement`. If a mode still shows PC cars, the matching `race_epoch_snapshot` line.
