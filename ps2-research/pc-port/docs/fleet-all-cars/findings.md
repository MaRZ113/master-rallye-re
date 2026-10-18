# FLEET-ALL-CARS1 — research findings

Static evidence: retail `MRallye.exe` (SHA-256 `bf8aef32…f96b4`), Ghidra 12.1.4 headless import of the
original PE (read-only probe script, no annotation saved), plus the retail data tree
`Data.sma_unpacked`. No memory was read or written in a running game in this phase.

## 1. How the PC creates and renders every race car

Every RaceTest scene has eggs `Car0`..`Car7` driven by `gaBootAICar` (`ctor 0x4b6750`, vtable
`0x691128`; XML fields `Car Active`, `Race/Car/PlayerType`, `Race/Car/InputType`, `AI/DriverID`,
`Car Name`, `Casts a shadow?`, `Produces tyre tracks?`). The boot callback `0x4b6a00` (vtable slot +0x14):

| Step | Original code | Meaning |
|---|---|---|
| egg name prefix `"Car"` (`0x6b18ac`), `atoi` of the rest → boot+0x14 | `0x4b6a00` head | the egg name `Car<N>` **is** the participant index N |
| `"vehicles/"` + lower(car name) + `"/car"` → `0x4d1010` → `en3d(egg+0x50)->set_model` | `0x4b6f9f..0x4b7027`, setter `0x4f5b70` | `0x4d1010` lower-cases the whole path and replaces `/` by `\` before taking the pool id, so en3d+0xc names `vehicles\<carname>\car` (confirmed live, see section 5); en3d+0x74 = cached instance |
| loop i=0..3: `new egg(0x78)` (`0x4f5670`), name = car egg name + `"/Wheel"` + i (`0x4f59f0`), model `vehicles/<CarName>/wheel` | `0x4b714e..0x4b724e` | each car owns four wheel eggs `Car<N>/Wheel0..3` with their own en3d/instance |
| `AISimulateeTransform` (`0x4f5290`) on slot 0, further components on slots 1/2 | `0x4f5950` | per-egg simulation transform |

Egg layout (`0x4f5670`): +0x00 flags (bit 2 = retired, as in the baseline owner check), +0x04..+0x10 four
component slots, +0x50 en3d state (`0x4f5a80`, 0x78 bytes), +0x5c name pool id, +0x60 manager list
node. `0x4f59f0` sets +0x5c and re-registers the egg in the manager `base+0x2f96fc` name registry
(`registry = manager+0x1c`, `registry[id]` = bucket vector, `0x50e450`). This is exactly the registry the
frozen baseline uses to prove the unique `RaceLimits` owner (`read_race_owner`).

The renderer side is already proven in earlier phases: the shared emitter `0x57707e` queue record gives
the instance; `instance+0xb0 → en3d`, `en3d+0x74 → same instance`, `instance+0x8c → compiled model`,
`instance+0x90` → private (damaged) node list. So:

**Exact identity chain (no position or geometry heuristics):**
`draw → queue record → instance → en3d (instance+0xb0, en3d+0x74 == instance) → egg with egg+0x50 == en3d`,
and the egg is the *unique* registry entry of pool id `"Car<N>"` (body) or `"Car<N>/Wheel<i>"` (wheel).
The same pool id `"Car<N>"` is also the Broker record of the `gaVehicleOutputData` the HUD feed already reads.

## 2. Answers to the research questions

* **Which owner/scene trees render opponents?** The same emitter, the same instance/en3d/model structures
  as the player. Each car is its own egg + instance; damage creates a per-instance private tree
  (instance+0x90), so damage state is naturally per car.
* **LOD meshes / different textures for distant cars?** No vehicle LOD asset exists: every `Vehicles/<Name>`
  folder has only `car.dx`, `complete.dx`, `wheel.dx` (+ textures); the boot always selects `car` / `wheel`.
  Whether the engine culls individual nodes of a distant car is not visible statically; the existing
  whole-cohort queue check (`car_queue_cohort`) fails closed (Stock for that car) if it does. Runtime item.
* **Can opponents use different car models in one race?** Yes. `Car Name` is per egg; for non-local
  participants the boot resolves the car through `Race/Car%d/DriverID`. Several PS2 profiles must be
  loaded at once. The PC model-name text (`vehicles/<Name>/car`) names the folder, which equals the
  fleet `family` strings (`Astero`, `Jump`, …, `Forester`, `megane`). Cars without a PS2 profile
  (Mercedes, Trooper, Bowler, Rav4, forklift, …) stay Stock.
* **Same model twice in one race** shares the compiled model and buffers (healthy tree); the per-draw owner
  is still the queue record's instance, so two Jumps are two participants.
* **Certificate for AI races:** the baseline certificate already certifies `Race/Type` 2 with 1..8 cars
  (`check_race_context`: owner registry, lifecycle, course job, offline context, all participants
  ready, single camera). It sets `single_human_car_race=false` and `participant_count=N`. RACE-CERT2
  (`ps2_race_certificate.hpp`, session *port-race-certification*) adds the finished phase and Attract
  (`Type 14`, no players). What was missing is not the race certificate but the per-draw **participant
  identity**, which section 1 supplies. FLEET-ALL-CARS1 consumes `ps2_race_certificate()` unchanged and
  does not edit any certification file.
* **Wheels:** the current single-car fleet attributes any matching wheel draw to the only car, and the
  X-Trail wheel pilot even uses a 4 m distance test to the chassis. Both are only sound with one car.
  With the egg names the wheel's owner is exact (`Car<N>/Wheel<i>`), so that heuristic is never used for
  a multi-car race.
* **Reflections:** one shared PS2 env target per frame (`mixed_capture`, captured once per frame),
  per-model learned environment matrix from that car's own native reflective submission. Nothing global
  changes; every PS2 car keeps its own environment state.

## 3. Budget for 8 cars

* CPU: identity table built once per frame: per participant one registry bucket read + 5 eggs × ~6 words;
  pool ids are resolved once per race generation (linear pool scan, ~40 keys) and re-verified by text
  per use like the RACE-CERT2 key cache.
* Memory: one participant parent per car (as the single-car path today), each with its own CAR child
  (asset + managed textures, ~1–4 MB per family) and wheel child. Eight different families ≈ 8× the
  single-car footprint; no sharing is attempted in this phase.
* GPU: each PS2 car is one DrawPrimitiveUP batch per mesh (≈2–6k faces per car), the native car draws of
  that car are suppressed; frame time must be measured (runtime-ab.md).

## 4. Limits

* All offsets above come from static analysis of the retail PE; the runtime gate re-proves each link
  every frame and every draw and falls back to Stock with a logged reason on any mismatch.
* Node culling of distant cars, Attract demo cameras and replays are runtime questions (runtime-ab.md).

## 5. Runtime correction (FLEET-ALL-CARS2)

First kit run (PID 26308, DLL 7f620448, four-car races, generations 8..31): every participant passed the
registry, egg, en3d and instance links but failed `body_model_name_not_vehicle_car`, so no PS2 body was
ever admitted in races with opponents (player car included); the cars the user saw were PC bodies with
the RACE-FINISH1 PS2 reflections, and lamp entries logged `fleet_owned_lamp_path_rejected_legacy_override_blocked`.
Cause: the parser expected `vehicles/<name>/car`, the game stores the `0x4d1010` normalised name
`vehicles\<name>\car` (decompiled: copy, `0x4d19f0` lower-case, `0x4d1ae0('/','\')`, strip the data root).
The parser now accepts one separator style per path (`/` or `\`), still requires the exact
`vehicles<sep><name><sep>car|wheel` shape and the case-insensitive family match, and a rejected body name
is logged as `model_text` in `ps2_fleet_participants`.
The F10 sidecars of that run show the opponents' CAR/WHEEL draws at the shared emitter with exact profile
geometry (Kamaz, WildCat, SeatBuggy, LandCruiser, Tata, Pajero, X-Trail), including damaged private trees.
