# FLEET-ALL-CARS1 — PS2 cars for every race participant

Opt-in: `PS2FleetAllCars=1` together with `RaceFleet=1` in `PS2Port.ini` (default `0`). With the key off,
or for any draw that does not prove its participant, every path behaves exactly as the single-car fleet.

Research and evidence: [findings.md](findings.md). Runtime check: [runtime-ab.md](runtime-ab.md).

## What changes

* **Identity per draw** (`renderer/fleet_participants.hpp`, `renderer/fleet_participant_native.hpp`).
  Once per frame, for every participant N of the live race certificate, the overlay proves
  `pool id "Car<N>" → unique live egg in the egg-manager registry (base+0x2f96fc,+0x1c) → egg+0x50 en3d →
  en3d+0x74 instance, instance+0xb0 == en3d`, the en3d model name `vehicles/<CarName>/car`, the Broker
  `Car<N>` `gaVehicleOutputData` record and `Race/Car<N>/PlayerType`; the same for the wheel eggs
  `Car<N>/Wheel0..3` (`vehicles/<CarName>/wheel`). The table is rejected as a whole if two participants
  claim the same egg/en3d/instance or more than one local driver exists. Each draw entry
  (`draw_race`, `draw_race_part`, `draw_wheel`, the lamp entry) looks up its queue record's instance in that
  table and sets a participant scope.
* **Per-participant ownership** (`PS2PortExtension`). Slot 0 is the original single-car parents (the local
  driver, and every draw without a participant scope). Slots 1..8 are one race parent + one wheel parent per
  non-local participant, created at start-up when the key is on. `race_model()` / `wheel_model()` return the
  parents of the active participant, so each car keeps its own CAR child (PS2 profile), damage state and
  deformation transfer, wheel owners, lamp/brake continuity and learned environment matrix. Several PS2
  profiles are loaded at once (one per participant parent).
* **Gate** (`fleet_frame_policy.hpp`): `fleet_single_car_race` keeps the old predicate and additionally
  admits a draw whose participant scope matches the current single-camera race certificate (same race
  generation and owner lifetime, index < `Race/NumCars`). All inline copies of the single-car predicate use
  this one function, including the final re-checks before submission.
* **Exact profile join**: the PS2 profile is still chosen from exact source geometry; with a participant
  scope it must also equal the egg's model folder (`vehicles/<family>/car`, case-insensitive), and the
  role must be Body for body paths and Wheel for wheel paths. The X-Trail wheel path's 4 m chassis distance
  is no longer the only owner evidence for a participant: its wheel egg must belong to an X-Trail participant.
* **Repair/reset**: `repair()` restores pending transactions of every slot; `native_states_pending()` covers
  all participant parents; device Reset resets them (`fleet_before_reset`, from the existing pre-reset hook).

Not changed: the race certificate (`ps2_race_certificate.hpp`, RACE-CERT2) and every baseline/certification
file; patch 0001 and `baseline-lock.json` are untouched. The certificate already certifies races with
AI opponents (Type 2, 1..8 cars) and, through RACE-CERT2, the Attract demo; FLEET-ALL-CARS1 adds only the
per-draw participant identity.

## Diagnostics

`Diagnostics=1` session log: one `ps2_fleet_participants` record per change of the proven set (max 16 per race
generation) with every car's reason (`participant_egg_chain_proven`, `egg_retired`,
`en3d_instance_not_created`, `body_model_name_not_vehicle_car`, …), player type, folder and wheel mask.
Existing `ps2_fleet_car_*` records are written per participant parent.

## Budgets

Per participant: one race parent (+X-Trail assets when `RaceFleet=1`), one wheel parent, the selected CAR,
wheel and OFF children with their managed textures. Eight different families need about 8× the single-car
memory. CPU per frame: one table (≈5 registry chains per car); per draw one queue-record read shared by the
four entries of a DrawIndexedPrimitive call.

## Tests

`ps2_reflection_pilot_contracts` (`fleet_participant_tests`): proven chains, Body/Wheel lookup, retired
egg, broken instance link, non-unique registry bucket, missing vehicle output, missing instance, foreign
wheel model, duplicate instances, two local drivers, pool-id caching per race generation, gate policy and
slot mapping. `ps2_port_extension_contracts` (`fleet_all_cars_slots`): opt-in, slot routing, local driver
and unscoped draws on slot 0, one distinct parent per participant, slot iteration, pending/reset.
