# RACE-FINISH1: PS2 effects through the finish, and reflections on deformed AI cars

## 1. Finished phase (all PS2 effects turned off at the finish line)

**Cause.** In the finish frame, `Race/Car<N>/RaceState` of the player becomes 3. The frozen baseline
(`check_race_context`, `check_race_hud_context`) accepts only states 0, 1 and 2. So
`live_race_certificate` and `live_race_hud_context` fail with
`participant_race_state_not_active_or_starting`. Every PS2 path (reflections, fleet car, grass,
course objects, HUD layers) shuts off in that same frame. The session log for user PID 15308
confirms this.

**Fix.** `renderer/race_finish_continuation.hpp` (overlay only). `ps2_race_certificate` and
`ps2_race_hud_context` wrap the baseline calls. They continue the last valid certificate only when
all of these hold:

* the baseline reason is exactly the participant-state one. The owner registry, lifecycle and
  course checks run before it, so they passed in this frame;
* the race generation, owner lifetime, actor and AI equal the last valid certificate;
* the unique local player (PlayerType 1) has RaceState 3, and every other participant has 0, 2 or 3;
* the single-camera identity is re-checked exactly the way the baseline does it (certificate only).
  The pause state is read for the HUD.

A restart or exit changes the generation, which ends the continuation. All overlay call sites now
use the wrappers:
* course objects (and through them grass, fleet, brake glow);
* reflections;
* X-Trail;
* the HUD layers and motion blur.

## 2. Reflections lost on damaged cars in AI races

**Cause.** In races with AI the cars stay PC models: the PS2 fleet path covers single-car races
only. Reflection identity is the exact geometry SHA, which includes vertex positions, and in-game
deformation changes it. The only deformation exception so far was a hand-pinned Terrano bumper.

**Fix.** `ReflectionPilot::classify` remembers each body that was accepted on its exact healthy
digest. The key is the device, reset generation, VB/IB resources with their generations, and the
draw layout. The content revision is not part of the key. The pilot also stores the UV + index
topology SHA for that body.

A later revision of the same draw keeps the identity only when its UV/topology SHA is equal.
Deformation moves positions and normals only. Every other admission rule of
`reflection_identity_for_hash` still applies: live race, vehicle body, native states, textures and
material. The log reason is `learned_uv_topology_on_deformed_body`.

## 3. Attract mode (no PS2 effects at all) — not fixed here

The baseline certificate rejects the demo in several places:
* the participant state;
* `Race/AttractMode` (`network_attract_ghost_or_replay`);
* single human car only.

Only the HUD context has an attract variant. Course id, camera and owner proofs for the demo need
the certification system itself to move into the overlay, which the user has asked for anyway.
