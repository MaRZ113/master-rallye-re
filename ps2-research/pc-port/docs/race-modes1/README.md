# RACE-MODES1 — PS2 port in every offline race mode, replay and the Challenge preview

Builds on FLEET-ALL-CARS2 and RACE-CERT2. Two new opt-in keys (default 0) in `PS2Port.ini`:

| Key | Effect |
|---|---|
| `PS2RaceAllModes=1` | race certificate also for Master Rallye (Race/Type 5), Rallye Cup (6), Challenge (7), Invitation (8) and replay playback (`Race/PlaybackReplay` 1) |
| `PS2FrontendAllCars=1` | with `FrontendModel=2`: one PS2 COMPLETE model per car shown at once (Challenge preview shows two) |

## Evidence (runtime PID 15928, DLL 8b83872b, Diagnostics=1)

* `race_epoch_snapshot` in Master Rallye / Rallye Cup / Invitation: the baseline passed owner registry,
  lifecycle and course job and stopped at `unsupported_race_or_player_configuration` (Type 5/6/8; Type 7 in
  older logs, Challenge also with `FinishingType` 1). Replay: `network_attract_ghost_or_replay` with
  `PlaybackReplay` 1 (Type 1 and 2). Mode numbers: `research/r-ai1-2/mode-map.json` (CONFIRMED_BY_EXE and runtime).
* The baseline HUD context is already valid in replay (`check_race_hud_context` normalises the replay flag);
  for Types 5..8 it stops at the race type after the `Hud/Hud0` scene, its lifecycle and the owner read passed.
* Challenge preview: 1049 `ps2_frontend_model_gate` records (gate 8, uncertified) within ~500 frames. The
  frontend model owns one car; the preview draws two, so every draw of the other car re-bound the model,
  re-hashed its geometry and, when the two cars differ, re-decoded the other PS2 COMPLETE asset from disk.
  Nothing was ever certified and the game slowed down.

## Certificate (`renderer/ps2_race_certificate.hpp`)

`normalise_race_mode` runs before the baseline context rules, only with `PS2RaceAllModes=1`:
Types 5..8 with `FinishingType` 0 (Challenge also 1) are checked as Type 2 Quick Race; `PlaybackReplay` 1 is
checked as 0. Everything else is the unchanged RACE-CERT2 chain: baseline owner/lifecycle/course stage,
`read_race_owner`, all nine typed fields, participant count and states (finished phase as before), single
camera rule, course id from the baseline snapshot. New modes `Competition` and `Replay`; a normalised
context only replaces the baseline's own type/replay/participant rejection, never a camera one.
HUD: for Types 5..8 the baseline race HUD rules (`check_race_hud_context` with the scene countdown, one local
PlayerType 1, `race_hud_player_drawable`, pause state) run on the normalised fields
(`ps2_competition_mode_hud_context`). Type 3 and other values stay rejected.

## Frontend (`frontend_model_native.hpp`, `FrontendSlotTable` in `fleet_participants.hpp`)

A draw proven to belong to a flat COMPLETE owner tree binds a slot by its queue-record instance; each slot is a
full `FrontendModel` with its own owner certificate, profile and textures. A slot keeps its instance while it
is drawn every frame. Without `PS2FrontendAllCars` there is one slot: a second car drawn in the same frame now
stays PC instead of re-binding (fixes the slowdown); with the key both cars get PS2 models.
Repair, pending states and device Reset cover every slot.

## Tests

`ps2_hud_damage_contracts` → `race_certificate_modes_tests`: Types 5..8 admitted only with the key, other
types, FinishingType rules, players/network/ghost/count/camera/owner/retired still rejected, countdown,
finished phase, replay of Quick Race and of a cup, camera rejection kept, Attract unchanged, competition HUD
(pause, two locals, countdown, stale owner, wrong stage). `ps2_reflection_pilot_contracts`: slot table.
`ps2_port_extension_contracts`: slot count/routing per key.
