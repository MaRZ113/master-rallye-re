# R5V-I — multi-slot registry and independent-family qualification

## Current status

**R5V-I.0 second physical slot: FULL PASS / CLOSED.** Runtime capture pairs
confirm physical ID27 at T2 local7 in Vehicle Select and as the player in a
single-player Quick Race. A separate active SplitScreen capture shows ID27/T2
and ID26/T1 as distinct simultaneous human participants. The owner observed
the ID27 Navara donor model, wheels, movement, HUD icon and progress marker
working without obvious corruption. These observations close the slot proof;
they do not turn the Navara donor alias into an independent vehicle.

**R5V-I.1 authored independent T2 family: core routing CONFIRMED_BY_RUNTIME.**
The exact candidate preserves physical ID27/T2 local7 but changes its runtime
family to `R5VQualifier`. The player-race capture shows ID27 with
`CarType`/`WheelType=R5VQualifier`; the owner reports the normal player
materialization check. The natural AI capture shows ID27/T2/AI using the same
family. The audited candidate pool includes ID27 and has no forced
participant override, so natural AI materialization is confirmed. No completed
AI race lifecycle or finish position is claimed. Six capture/raw hashes are
recorded in [the runtime ledger](i1-runtime-evidence.json).

The re-entry comparison shows stored Quick Race ID27 with a scene-local
Navara/T2-local0 selection in one snapshot and R5VQualifier/T2-local7 in its
control; its native writer remains unidentified. The captured marker remains
white, while J0's example requests magenta. Both are explicit public runtime
release gates; neither blocks compiler foundation work.

## I.0 runtime record

The exact I.0 EXE SHA256 is
`50ff267d2758c1ff894d91bcdafd7dba4a2fa278d678a075e7767120727abbea`
(3,121,214 bytes). Four JSON/raw pairs and their raw-byte hashes are recorded
in [runtime-results.md](runtime-results.md). Vehicle Select publishes
`CarModel=27`, `SLOT PROOF` / `NAVARA DONOR`; the player race has
`NumCars=4`, `NumPlayers=1`, `Race/Type=2`, `Car0=ID27/T2`, `CarType=Navara`,
`WheelType=Navara`, and a cyan canary. The AI remain valid T2 stock IDs 7, 11,
and 13; ID14 does not enter T2 local7.

The active SplitScreen capture has `NumCars=4`, `NumPlayers=2`: Car0 is ID27/T2
Navara with the cyan canary, Car1 is ID26/T1 Mercedes with the red canary, and
the two AI are T2 IDs11 and 9. The owner confirmed both human views operated
normally. The separate SplitScreen menu capture is not treated as actor
proof because its race participant fields are stale/inconsistent.

ID25 remains mapped to T3 local11 and its frontend slot is preserved, but the
Trooper model files are absent from this test package. This is a package
content gap, not an I.0 registry blocker. No full stage/results/collision/
damage claim is made for the I.0 run unless separately reported.

## Sparse identity map

| Class | Local indices | Physical IDs | Evidence |
|---|---:|---|---|
| T1 | 0–6 | 0–6 | retail mapping preserved |
| T1 | 7 | 26 | Mercedes, runtime qualified |
| T2 | 0–6 | 7–13 | retail mapping preserved |
| T2 | 7 | 27 | I.0 slot and I.1 family routing runtime-confirmed |
| T3 | 0–11 | 14–25 | retail mapping preserved; ID25 remains Trooper slot |

Registry layout is formula-based through 28 records: `record_count = highest
physical_id + 1`; RaceTest base is `4 + record_count * 0x34`; the adjacent
39-row RaceTest allocation ends at `0xC68`. For ID27, base is `0x5B4`.
I.0/I.1 retain 39 initializer and 11 indexed-consumer relocation sites. This
is demonstrated through two added IDs, not arbitrary-N runtime qualification.

## I.1 authored qualification identity

| Layer | ID27 I.1 value | Qualification meaning |
|---|---|---|
| Physical/class identity | ID27, T2 local7 | unchanged from I.0 |
| Registry/runtime/model/wheel name | `R5VQualifier` | distinct native lookup family |
| Render package | `DataGx/Vehicles/R5VQualifier/*` | 98 separately staged DX/DXT files |
| Physics family | `Vehicles/R5VQualifier/*` | 147 Navara-derived values under a new namespace |
| Player modifications | `Vehicles/R5VQualifier/*` | 26 Navara-derived rows under a new namespace |
| Body asset canary | `paintjeep-tga.dxt`, 16×16 magenta RGBA `[255,64,210,255]` | visible independent-package probe |
| Collision | Navara-derived `car.dx` hull | donor-derived, no unique hull claim |
| Frontend strings | `R5V` / `T2 QUALIFIER` / `R5V T2 QUALIFIER` | independent visible identity |
| Results label | `R5V TEST DRIVER` | presentation-only; native DriverID unchanged |
| Unlock | mirrors stock ID10, `T2CupCar1` | no progression redesign |
| Audio | stock profile7 | preserved tuned stock mapping |
| Frontend art/stats | Navara frame23; 7/6/6/5 | explicitly donor-derived |
| T2 AI pools | `[7,8,9,10,11,12,13,27]` | unchanged I.0 pool eligibility |

This is an authored SDK qualification vehicle, not a historical Master Rallye
car and not an authentic Navara-independent topology. The proof target is
family-address routing and identity separation: runtime ID27 should request
`R5VQualifier` model, wheel, and physics paths rather than resolving through
the Navara family name. The named physics clone is intentionally semantically
unchanged; it proves separate path lookup without introducing a risky handling
change.

The runtime package is generated under ignored
`.research-output/vehicles/multislot/i1/runtime-package`. It composes the
verified H.2 runtime resources, deterministic I.1 executable, qualified
T2_Car8 scene, new family assets, and full `vehicles.xml` /
`Modifications.xml` overlays. It contains no PlayerState, save, screenshot,
raw capture or Ghidra project. Package verification checks every staged file
hash and rejects loose Navara model paths for the ID27 family.
The tracked [derived candidate manifest](i1-candidate-manifest.json) records
the exact candidate/source hashes and all 81 patch sites with lengths and
before/after SHA256 values, but omits raw executable patch bytes.

## Boundaries

I.1 does not add ID28, alter participant count, change the randomizer, change
AI roster lifecycle, add an authored sound, change collision topology, or
claim arbitrary-N runtime support. Existing ID26 Mercedes behavior and ID25
Trooper mapping remain regression constraints. Player family routing and
natural AI participant materialization are now runtime-confirmed; Vehicle
Select re-entry and marker-color changes remain gates before public runtime
release. J0 offline SDK development is in progress.
