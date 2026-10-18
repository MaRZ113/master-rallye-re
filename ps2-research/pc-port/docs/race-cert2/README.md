# RACE-CERT2: overlay-owned race certificate (Attract demo + finished phase)

Status: plan written before the implementation. Code: `renderer/ps2_race_certificate.hpp`
(replaces `renderer/race_finish_continuation.hpp`, which is preserved in
`dist/race-finish1/handoff.zip`). Tests: `tests/ps2_race_certificate_contracts.hpp`, run by the
existing CTest target `ps2_hud_damage_contracts`. Patch 0001 is unchanged and stays hash-locked.

## 1. Why the baseline certificate cannot be reused as is

The frozen baseline (`modernization/renderer`, never edited) checks, in this fixed order
(`check_live_race_certificate`, `src/race_epoch.cpp`):

| # | Proof | Baseline reason on failure |
|---|-------|----------------------------|
| 1 | Owner registry: unique `RaceLimits` registration, actor flags, AI slot + vtable `0x69152c`, unique live-list membership | `read_race_owner` reasons |
| 2 | Lifecycle: owner temporal match + `correlated_owner_candidate` (completed root job, every job of the generation succeeded, HUD children only under the root) | `lifecycle_ancestry_or_completion_unproven` |
| 3 | Course: root job is `RaceTest/<course>` from `DataScene/RaceTest/<course>.xml`, flags 1/1 | `supported_course_job_not_verified` |
| 4 | Context (`check_race_context`): typed fields, Type 1/2, NumPlayers 1, no network/attract/ghost/replay, NumCars = owner count, participant states 0/2 | six context reasons |
| 5 | Camera: manager count 1, selected == expected == renderer-holder current | `single_camera_identity_not_verified` |
| 6 | Course id copy from the root job | `course_identity_copy_failed` |

Only steps 4–5 reject the two cases we need:

* **Finished phase**: local `RaceState` 3 fails step 4 (`participant_race_state_not_active_or_starting`).
* **Attract demo**: `Race/Type` 14, `NumPlayers` 0 fail step 4
  (`unsupported_race_or_player_configuration`; `AttractMode=1` would fail next).

Evidence (baseline F10 snapshot `frame-15308-d1-00156657.jsonl`, Attract on `Racetest/france2`):
`correlated_owner_candidate=true`, `course_identity_verified=true`, owner `valid_native_owner=true`
(unique live owner), committed `Hud/AttractMode` child of root lifetime 25, camera `count=1`,
`Race/Type=14`, `NumPlayers=0`, `AttractMode=1`, `NumCars=4`, participant states `[0,0,0,0]`,
`live_certificate_reason=unsupported_race_or_player_configuration`. So owner, lifecycle, course
and camera identity are all provable in Attract. No mode without an owner or camera proof is
admitted, so no user decision is needed for this phase.

## 2. What the overlay reproduces read-only, and from where

The baseline `RaceEpoch` lives in an anonymous-namespace observer. The overlay cannot and does not
touch it. It only uses exported, read-only baseline APIs plus its own native reads:

| Proof | Overlay source | Same as baseline? |
|-------|----------------|-------------------|
| Owner registry (step 1) | Baseline `read_race_owner()` called by the overlay with the actor/AI/owner lifetime/generation from `live_race_certificate()`, through a key-caching live reader | identical function |
| Lifecycle (step 2) | `live_race_certificate()` reason: a step-4/5 reason means steps 1–3 passed **this frame** | identical (baseline-evaluated) |
| Course job (step 3) | Same as step 2 | identical (baseline-evaluated) |
| Course id | Valid baseline certificate's `course_id`; otherwise one exported `race_epoch_capture_json(0,0)` snapshot per (race generation, owner lifetime, actor, AI). The overlay accepts its `root_job_success.scene` only when the snapshot says `poisoned=false`, `course_identity_verified=true`, `correlated_owner_candidate=true`, the race generation, actor, AI, the owner's race generation and the owner lifetime equal the live certificate, the root lifetime equals the owner's `execution_job_lifetime`, and the text is `RaceTest/<[A-Za-z0-9_-]{1,96}>` (case-folded prefix, as `valid_race_root`). | same root job text the baseline would copy |
| Context fields (step 4) | Baseline `race_broker_scalar` over `RACE_CONTEXT_KEYS`/`RACE_CONTEXT_TAGS` | identical reads |
| Camera (step 5) | Overlay re-check: manager count 1, selected == expected == renderer holder current | identical rule |
| Attract HUD scene | Baseline `live_race_hud_context()` valid with `attract=true` (committed `Hud/AttractMode`, exact `DataScene/Hud/AttractMode.xml` child of the proven root) and the same generation/owner | identical (baseline-evaluated) |
| Pause | Baseline `read_pause_menu_state_readonly()` | identical |

Thread safety: `live_race_certificate()` and `race_epoch_capture_json()` poison the epoch when
called off the observer thread. The overlay calls the snapshot only after `live_race_certificate()`
returned a step-4/5 reason (which proves the thread check passed), and the HUD path calls
`live_race_certificate(0)` only after `live_race_hud_context()` passed its own thread check.

## 3. Admission rules

Every admitted certificate needs: a step-4/5 baseline reason (or a valid baseline certificate),
a re-read owner with `valid`, `storage_readable`, `native_live_unique`, `arrays_ready`,
all nine context fields present and typed, `NumCars == owner.count`, the camera check (certificate
only) and a course id from section 2. Identity fields (generation, owner lifetime, actor, AI,
camera, course) are copied from those proofs, never from a cached earlier frame.

| Mode | Fields | Participants | Status |
|------|--------|--------------|--------|
| `race` | baseline `check_race_context` supported | 0/2 (baseline) | **identical**: the valid baseline certificate is returned unchanged |
| `finished` | baseline `check_race_context` supported with only the participant-state bit normalised | unique `PlayerType==1` local participant in state 3; every other 0, 2 or 3; every state key present and typed | **newly admitted phase** (replaces RACE-FINISH1's "last valid certificate" continuation) |
| `attract` | baseline `check_race_attract_hud_context`: Type 14, NumPlayers 0, NumNetworkPlayers 0, NetworkSync 0, AttractMode 1, Ghost 0, Replay 0, FinishingType 0, NumCars 1–8 | all 0/2 | **newly admitted mode**, plus the baseline Attract HUD scene proof for the same generation/owner |

Not admitted (unchanged): replay, ghost, network, split screen, startup countdown (state 1) for
the certificate, any unknown race type, any state other than 0/1/2/3, any frame whose owner,
lifecycle, course or camera proof failed.

HUD context: a valid baseline HUD context is returned unchanged (this already includes the
baseline Attract variant). A baseline HUD rejection with exactly the participant-state reason
(committed `Hud/Hud0` and its lifecycle passed) is admitted only in mode `finished` from the same
proofs (camera not required, as for the baseline HUD). Pause comes from the typed baseline reader.

## 4. Consumers

* `courseintegration::certificate` no longer drops Attract after the HUD gate; the camera
  certificate stays mandatory, so frontend scenes are still rejected before race key reads.
* Reflections, X-Trail, grass, course objects use the certificate unchanged (Attract now valid).
* Fleet car/wheels/lamps keep `single_human_car_race && participant_count==1`. Attract has
  `NumPlayers=0`, `NumCars=4`, so the fleet stays off in Attract exactly like multi-car AI races.
* HUD damage and HUD map no longer short-circuit Attract; their feed still requires a unique
  `PlayerType==1` car and fails closed (`single_local_player_unproven`) in the demo.
* Motion blur runs in Attract (camera effect; no player identity needed), still off when paused.

## 5. Multi-car AI races

Mode 2 races with AI already pass the baseline (`NumPlayers 1`, `NumCars` 1–8, owner count match).
New here: their finished phase (local 3, AI 0/2/3) is certified the same way. Fleet stays
single-car only (separate policy, not a certificate question).

## 6. Runtime checks still needed

Attract: reflections, grass (on courses that have it) and motion blur visible in the demo
(certificate reason `ps2_attract_demo_certificate`). Finish line: effects stay on after the finish
(`ps2_finished_phase_certificate`, HUD `ps2_finished_phase_hud_context`). Both still need user
runtime confirmation. If Attract ever shows more than one camera, the certificate stays off
(`single_camera_identity_not_verified`); admitting that would need a user decision.

The user later allowed edits to the frozen baseline. They were not used: `build_overlay.py`
refuses tracked changes in `modernization/renderer` (the tree is pinned to the locked commit), so a
baseline fix would need a commit, and commits are out of scope for this phase.
