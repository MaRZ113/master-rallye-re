# SPLIT-SCREEN1 — PS2 port in two-player split-screen races

Opt-in `PS2SplitScreen=1` (default 0), on top of RACE-MODES1 / FLEET-ALL-CARS2.

## Evidence (user runtime, PID 24180, DLL 5d4a6102)

F10 capture `frame-24180-d1-00000670` inside a split-screen race (Turkey2): committed scene `Hud/Hud1`,
`Race/Type 1`, `NumPlayers 2`, `NumCars 2`, race owner valid and unique (one registration, one live membership,
states [2,2]), course job verified, **two active cameras**, live certificate
`lifecycle_ancestry_or_completion_unproven`. Epoch events: the HUD request `Hud/Hud1` came from caller
`0x4aa0c1` as a child of the race root job, but the baseline accepted only `Hud/Hud0` from that caller, so the
request started a new lifecycle generation and revoked the race proof.

Static (retail PE): selector `0x4aa040` requests `Hud/AttractMode` in Attract, otherwise by the number of players
`Hud/Hud0` (1) or `Hud/Hud1` (2), all through `0x522330` returning to `0x4aa0c1`. Camera manager
(`docs r-cam1-a`): four slots `+0x00..+0x0C`, active count `+0x10`; the frame scheduler `0x653080` binds each
active camera through the renderer holder before its traversal.

## Changes

* **Baseline** (patch 0001, lock updated): `RaceEpoch::request` accepts `Hud/Hud1` from `0x4aa0c1` exactly like
  `Hud/Hud0`; `race_hud_scene_proven` accepts one `Hud/Hud1` HUD job (`DataScene/Hud/Hud1.xml`) of the root;
  the HUD context recognises the committed `Hud/Hud1` scene. Baseline consumers (free camera, physics, HUD
  hiding) still reject split screen at the context stage (`NumPlayers 2`, two cameras) — only the reason moves.
* **Overlay certificate** (`ps2_race_certificate.hpp`): with the key, `NumPlayers 2` and Type 1/2 are checked as one
  player of Type 2; exactly two local PlayerType 1 participants are required (HUD: both drawable); the
  single-camera rule is replaced by `race_split_camera`: count 2, two distinct slots, the requested camera is one
  of them and is the renderer's current camera. Mode `SplitScreen`; finished phase lets either driver finish first.
* `courseintegration::certificate`: with two cameras it certifies the renderer's current camera (the pass being
  drawn) and reports `single` only for a `SplitScreen` certificate.
* Fleet participant table accepts two local drivers in that mode; every car keeps its own parents, and the
  existing per-pass logic (view/projection/viewport change = new pass) draws each PS2 car in both viewports.

## Not covered: LAN / network races

The logs show only LAN menus (`Race/Type 9`, NetworkGames/NetworkHost screens); no network race was reached, so
there is no evidence of how remote participants, `NumNetworkPlayers` and `NetworkSyncActive` look in a race.
Network races stay Stock (baseline `network_attract_ghost_or_replay`). A LAN race with `Diagnostics=1` and an
F10 capture is needed before a network certificate can be designed.

## Tests

`ps2_hud_damage_contracts` → `race_certificate_split_tests`: patched `RaceEpoch` with `Hud/Hud0`/`Hud/Hud1` from
`0x4aa0c1` (proven) and from another origin (revoked), unknown `Hud/Hud2` refused; split certificate only with the
key, both passes/cameras, wrong/absent/third camera, duplicate slot, one or three local drivers, three players,
network, ghost, replay, lifecycle reason kept, finished phase, split HUD context. `ps2_reflection_pilot_contracts`:
two local drivers allowed only with `max_locals 2`.
