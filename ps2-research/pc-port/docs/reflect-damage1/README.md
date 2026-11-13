# REFLECT-DAMAGE: PS2 reflection and brake glow lost after collisions

Owner reports (2026-11-13). With the PS2 reflection in mode 4 (`PS2_STATIC_PLUS_PC_FRAMEBUFFER_APPROXIMATION`),
the reflection on PC car bodies (seen on Kamaz and Astero) switched off on some body parts after collisions.
After the first fix (build 6e62ce19) both the reflection and the PS2 brake glow still switched off. Grime is not
involved.

## Evidence

Host `host-grime-g0-01`, logs in `MRRRenderer/logs`.

* `session-20261112-141158-32596` / `ps2diag-20261113-001212-32596` (build before the fix, three AI races on
  Italy2):
  * The `reflection_body` ledger counted only `applied` and a few `vehicle_body_unverified`. Damaged parts were
    invisible in it, because a draw with an unknown digest kept `vehicle = "UNKNOWN"` and was not noted.
  * The baseline classifier `frame_summary` counters drop from 83 vehicle body draws to 55 or 28 after
    collisions (`vehicle_identity_demotions`).
* `session-20261112-145707-29720` / `ps2diag-20261113-005711-29720` / `frame-29720-d1-00001528` (build
  6e62ce19, owner run with AI on Italy2):
  * `reflection_body`: 42190 `applied`, 14764 `deformed_or_unregistered_no_learned_body`.
  * Race start (frame 108): every car is drawn from VB generation 624 and IB generation 625.
  * From about frame 450 every car, healthy parts included, is drawn from re-created buffers: VB 674 and IB
    670/950, with other offsets.
  * In frame 1528 the PS2 override is missing exactly on the large deformed panels: Astero 452/546, Kamaz 176/188
    and 82/91, megane 141/185. The undeformed parts of the same cars, which still match their exact digest, keep
    it.
  * The Astero additive glow (40/40, texture generation 752, the same texture as the healthy glow at frame 349) is
    drawn as stock in frame 1528.

## Common root cause

Every PS2 identity on a native car part is an exact hash of the current vertex positions. This covers the
reflection body digest, the vehicle partition face hashes, and `exact_native_lamp` for the ON core and glow
lamps. Collision deformation changes the positions. The damage fallbacks that existed either were keyed to
something the game also changes after collisions, or were never reached:

1. **Reflection.** The learned healthy body was keyed by VB/IB resource, generation and draw range. The game
   re-creates the car VB/IB after collisions, so a deformed part never matched its learned entry. Before 6e62ce19
   the fallback also required the baseline vehicle classifier proof, which is itself content based and loses
   deformed cars. It also never learned bodies proved by source material authority.
2. **Vehicle partition** (LandCruiser, Bruno, SeatBuggy, ChevyBlazer, X-Trail, Forester). There was no
   deformation fallback at all.
3. **Brake lamps of PC cars.** `pc_lamp_family` names the fleet family only from the exact lamp positions. A
   deformed lamp therefore has no family. The existing damaged branch of `NativeLampContinuity::match_source`
   (private damage tree, same owner, material, texture and UV/index topology as the healthy reference) was
   never reached for it.

## General fix (REFLECT-DAMAGE2)

The healthy witness is keyed by content that collision damage does not change: the part's UV set and index
topology, plus the vertex and triangle counts. It is never keyed by the VB/IB resource, generation or offset.
It is learned only from an exact healthy match, so it is bounded by the registries. A topology seen with two
different identities is marked ambiguous and never resolves.

* `ReflectionPilot::classify`: `learned_` maps `damage_uv_topology_sha` to the healthy digest, vehicle and proving
  authority. A mode-4 draw that is not accepted and whose topology is learned is re-evaluated against the learned
  digest. The learned proof replaces the vehicle proof the baseline classifier lost. All other rules still apply:
  live race owner, coordinate policy, native states, textures, opaque body and material stages. Reasons:
  `learned_uv_topology_on_deformed_body`, and `learned_body_proof_while_classifier_lost_body` for a healthy
  digest.
* `VehiclePartitionPilot::classify`: an accepted plan is learned by the ordered UV and index topology
  (`partition_ordered_topology`), so the runs stay in index order. A deformed upload reuses the plan
  (`learned_uv_topology_on_deformed_partition`).
* `pc_lamp_family` → `learned_lamp_family`: ordered lamp topology (`NativeLampContinuity::topology`) plus counts
  map to the family seen on the exact healthy lamp. This only names the candidate family. The damaged branch of
  `match_source` still has to prove the private damage tree, the same current owner, material and texture, and the
  healthy reference topology.

## Diagnostics (race ledger)

`reflection_body`:
* `deformed_<reason>`: the learned identity was re-evaluated and failed one of the remaining rules.
* `deformed_ambiguous_uv_topology`: two different healthy digests share this topology.
* `deformed_or_unregistered_no_learned_topology` (vehicle `VEHICLE_BODY`): a body-verified draw on a registered
  layout with an unknown digest and a topology never seen healthy. The damage changed UVs or indices, or the part
  was never drawn healthy in this session.

`models` (lamps of a car on its private damage tree): `lamp_damaged_pc_lamp_unidentified` (no family by exact
positions or learned topology), otherwise the literal rejection reason of the lamp path, for example
`damaged_uv_or_index_topology_changed` or `damaged_texture_identity_changed` (see `fleet_lamp_native.hpp`).

## Parts that still cannot keep the effect

* A part whose damaged upload changes its UVs or index topology. That is a different mesh, and the ledger names
  it.
* A part never drawn healthy in this session before it was damaged. The witness persists across races and
  restarts within one game session.

## Tests

`tests/reflection_pilot_tests.cpp`:
* `learned_deformed_body_tests` uses a synthetic 176/188 body and a registry seam
  (`ReflectionPilot::set_identity_for_tests`). It covers: deformation while the classifier lost the body,
  re-created VB/IB with other offsets, attributed rejections, UV change, a repaired healthy digest, mode-4 only,
  source-authority bodies, and an ambiguous topology.
* `learned_lamp_family_tests` covers a lamp family carried across deformation and a re-created VB, a UV change,
  and ambiguity.

## REFLECT-DAMAGE3: PS2 fleet body and its glow fell back to PC after collisions

Owner report on build e43eebed: after collisions the PS2 model switched to the PC model, and the glow layer
switched with it. Logs: `session-20261112-151158-31876`, `ps2diag-20261113-011203-31876` (SeatBuggy fleet race on
Italy2). `fleet_gate_2` was noted 443 times, with `ps2_fleet_car_certificate_failure` reason `private_unselected`,
`matched_mask` 0xBFFFFF of 0xFFFFFF. One of 24 source records (slot 22) was not found in the private damage tree.

This was not caused by REFLECT-DAMAGE2, which does not touch `fleet_body_certificate`, nor by the grime pass. It
existed before, and this was the first SeatBuggy race with damage.

**Cause.** Every fleet profile has twin parts: one 19/29 mesh used twice (SeatBuggy slots 20/22, Kamaz 3/5,
Astero 3/6 and so on, 22 profiles). The twins have identical UVs, winding and owned material. On the private
damage tree, `FleetDamageState::select` disambiguates candidates only by exact original positions. So once one
twin is deformed, both slots match its draw and neither matches exactly, and the draw is unselected. The
certificate then lacks one slot, the whole PS2 body falls back to stock, and the PS2 lamps fall back with it,
because `owned_lamp_context` needs the certified fleet body.

**Fix.**
* `FleetDamageState::candidates` returns every slot a private-tree draw can be.
* `fleet_body_certificate` resolves the unselected draws after the main pass:
  1. by elimination, when the other twin was matched exactly;
  2. otherwise by the clearly nearest healthy reference: mean squared distance at most a quarter of the runner-up,
     and not contested by another unresolved draw.
  Every assignment is still observed against the owned healthy material and UV proof. If a twin stays unresolved,
  the reason is `private_twin_unresolved`.
* `fleet_damage_reflection` uses the slot that the current certificate bound to the mesh when `select` is
  ambiguous.

Not covered: the Kia damage path (`kia_damage`, twins 4/9) keeps its own selection.
