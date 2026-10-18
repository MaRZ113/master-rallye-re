# FLEET-ALL-CARS1 — runtime A/B

Kit: `dist/fleet-all-cars1`. Install by hand (nothing is deployed automatically): copy `d3d8.dll` beside
`MRallye.exe` of the test install, keep the existing `PS2Vehicles/`, `PS2Grass/`, `PS2Hud/` asset folders
from the previous kits (no new assets in this phase). Keep the previous `d3d8.dll` for B.

INI (`PS2Port.ini`, section `[PS2Port]`): your current config plus

```
RaceFleet=1
Reflection=4
PS2FleetAllCars=1
Diagnostics=1
```

A = `PS2FleetAllCars=1`, B = `PS2FleetAllCars=0` (same DLL). B must look exactly like RACE-FINISH1:
PS2 player car in single-car races, Stock opponents.

## Runs

1. **Single-car race (control)**, A and B: player car PS2 as before, damage, wheels, lamps, reflections
   unchanged. Session log: one `ps2_fleet_participants` record with `count 1, proven 1, local 0`.
2. **Race with 4 participants** (Quick Race with 3 opponents), A: every opponent whose car has a PS2 model
   shows the PS2 body, PS2 wheels and lamps; cars without a PS2 model (e.g. Mercedes, Trooper) stay PC.
   Check from chase and front cameras, close and far (overtake, then let them pass).
3. **Race with 8 participants**, A: same as 2 with the maximum field; note the frame time (F10 timing or
   fps counter) for A and B at the start grid and in a busy section.
4. **Damage on opponents**, A: hit an opponent hard (front and side). Its PS2 body must deform and keep its
   PS2 reflection; the other cars must not change. Damage on the player car must stay independent.
5. **Reflections**, A: opponents' paint shows the PS2 environment reflection (same look as the player car),
   also after damage.
6. **Two cars of the same model** (if the field has it): both PS2, independent damage.
7. **Finish phase**: cross the line, keep driving; opponents still finishing stay PS2.
8. **Attract demo** (wait in the main menu): AI cars PS2 if RACE-CERT2 certifies the demo
   (`ps2_attract_demo_certificate`); otherwise Stock with the certificate reason in the log.
9. **Window Reset** (Alt+Enter or resolution change) during a race with opponents, and MSAA 4x: no
   corruption, PS2 cars return after the reset.

## What to send back

* Screenshots of runs 2, 4, 5 (and 8 if PS2).
* `MRRRenderer\logs\session-*.jsonl` lines with `ps2_fleet_participants`, `ps2_fleet_car_replacement`,
  `ps2_fleet_car_fallback`, `fleet_car_certificate_failure`, `ps2_fleet_car_invariant_failure`.
* Frame time A vs B for runs 2 and 3.

## Known runtime questions

* Whether the engine culls single nodes of a distant car (the whole-cohort queue check then keeps that car
  Stock until it is close again — look for `queue_multiplicity` in the log).
* Attract demo cameras/replays: certification belongs to RACE-CERT2, not this phase.
