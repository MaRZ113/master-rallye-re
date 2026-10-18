# FLEET-ALL-CARS2 — runtime A/B (fix of FLEET-ALL-CARS1)

Kit: `dist/fleet-all-cars2`. Replace only `d3d8.dll` of the test install (same INI and asset folders as
FLEET-ALL-CARS1). Keep the FLEET-ALL-CARS1 DLL for comparison.

## What was wrong in FLEET-ALL-CARS1

Your log (PID 26308) shows every car of every four-car race rejected with
`body_model_name_not_vehicle_car`: the game stores the car model name as `vehicles\<name>\car` (lower case,
backslashes), the overlay expected `vehicles/<Name>/car`. So in races with opponents **no PS2 body was
applied at all**, the player car included; what you saw were PC bodies with PS2 reflections (that part
comes from RACE-FINISH1 and works). Nothing about damage was involved yet. Single-car races were not
affected (they use the original single-car path).

## INI

```
RaceFleet=1
Reflection=4
PS2FleetAllCars=1
Diagnostics=1
```

## Runs

1. **Race with 4 participants**: player and opponents with a PS2 model show PS2 bodies, wheels and lamps from
   the start. Log: `ps2_fleet_participants` with `proven 4` (or the number of cars), `local` = your car,
   and `ps2_fleet_car_replacement` records for several families.
2. **Damage**: hit an opponent and take damage yourself. Expected: the damaged car keeps the PS2 body
   (deformed) and its lamps; if a family cannot transfer damage it falls back to the PC body with PS2
   reflection (`unsupported_private_tree` in the F10 capture) — note which family.
3. **8 participants**, frame time A (`PS2FleetAllCars=1`) vs B (`=0`).
4. **Finish phase** and **Attract demo**: PS2 cars stay / appear.
5. **Window Reset** during a race with opponents.

## What to send back

Screenshots of 1 and 2, and from `MRRRenderer\logs\session-*.jsonl` the lines with
`ps2_fleet_participants`, `ps2_fleet_car_replacement`, `ps2_fleet_car_fallback`,
`ps2_fleet_car_participant_model_mismatch`, `ps2_fleet_car_invariant_failure`. An F10 capture right after
a crash (damaged opponent in view) helps if a damaged car still drops to PC.
If a car is rejected again, `ps2_fleet_participants` now prints its `model_text`.
