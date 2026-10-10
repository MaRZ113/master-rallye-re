# R-CAM1-A3e — first-flight certificate correction

## Scope and result

This phase changes only race-certificate evidence interpretation and bounded
diagnostics. It does not change camera scheduler ABI, the native camera scope,
the owned 176-byte ranges, FOV coordination, restoration, controls, or display,
Broker, UI, and R-ATTR1 behavior. It does not establish a successful Freecam
flight; that still needs the human movement test below.

The canonical target remains pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

## France1 root and HUD child flags

The exact A3d first-flight capture is
`D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-16956-d1-00020128.jsonl`.
It records root lifetime 7 (`RaceTest/France1`,
`DataScene/RaceTest/France1.xml`) with `flag21=1, flag22=1`, and child lifetime
8 (`Hud/Hud0`, `DataScene/Hud/Hud0.xml`) with `flag21=1, flag22=0` and parent
lifetime 7.

The observer obtains these bytes from the queued job (`+0x21`, `+0x22`) and
checks them again at execute entry. Static evidence at VA `0x004AA020` shows
the dedicated HUD selector calling the request helper at `0x004AA0B5`; it
passes `1,0` and calls `0x004F5840` at origin `0x004AA0C1`. Thus these are
per-job native request flags: the outer course job's observed `1/1` tuple must
not be mistaken for the HUD helper's `1/0` tuple. The exact course admission
now requires a parentless root with the captured scene/source and `1/1`; the
HUD child still requires its separate native origin, ancestry, and `1/0`.
Neither flag tuple by itself authorizes the camera.

## Commit meaning and job-local success

At VA `0x00522680` / RVA `0x00122680`, native code reads the success boolean
from `[ESP+4]`. On success it copies SceneManager `+4` (the latest requested
scene ID) into SceneManager `+0`. A HUD request made while the France1 parser
is executing can therefore change that global ID before the outer parser
returns. In the captured sequence, root lifetime 7 commits while the manager
already holds the Hud/Hud0 ID.

The observer now records the manager ID observed after the call as
`manager_scene_after_commit` only.
`commit_success` comes from the native boolean for the currently executing
job, plus the existing error/failure fence; it no longer compares a global
scene ID with the latest global request. The root remains tied to its own
queued scene/source/flags and job lifetime. `correlated_owner_candidate()`
still requires the root and every admitted HUD child to complete successfully
in the current race lifecycle. A successful HUD child cannot revive a failed,
stale, or unsupported root.

## RaceState gate

Static evidence in the A3b native map places the producer at VA `0x0048E820` /
RVA `0x0008E820`: when its `+0x10` branch is clear, the startup counter selects
state 1 before phase 10 and state 2 at/after phase 10; the other branch writes
state 0. The normal finish policy at `0x00489EC0` writes state 3. These values
are phases, not a universal `playable iff state == 2` test.

The supplied live France1 F10 record has `RaceState=0` while the race is
rendering and reports one current RaceLimits owner, one participant, offline
single-player typed Broker values, completed root/HUD jobs, and one selected
camera. A3e therefore treats only states 0 and 2 as supporting active-race
evidence. State 1 (startup), state 3 (finished), missing/wrong-typed values,
and other values reject. State 0 is never sufficient by itself: the full
course job, lifecycle ancestry/completion, current unique live owner, typed
offline context, and single-camera identity checks remain mandatory. Frontend,
loading, retirement, stale-owner, results, replay, ghost, attract, and network
paths continue to fail those independent checks.

## Diagnostics

The existing F10 snapshot now names root and HUD job completion evidence,
copies flags and scene/source, labels the manager scene at commit, includes the
observed participant states and admission reason, and retains the final live
certificate reason. Meaningful Freecam state or configured-toggle transitions
also emit this bounded lifecycle snapshot automatically, with focused state,
configured toggle VK, whether it was sampled pressed, and whether the flight
controller received an edge. F10 remains reserved.

## Retest required

Use the exact-build candidate DLL and the existing first-flight configuration:

1. Start France1 and wait until active gameplay is visibly running.
2. Press F8 once, move briefly with the configured preset controls, and press
   F8 again to return to the stock view.
3. If the camera does not activate, inspect the first `R-CAM1-A3e`
   `race_epoch_snapshot` and report `live_certificate_reason`, root/HUD job
   evidence, `participant_states_reason`, `toggle_pressed_while_focused`, and
   `controller_toggle_edge`.

Only the human test can establish a flight. A valid certificate without a
toggle edge points to input/focus; a valid certificate and edge without a
scope points to the later displayed-view/scope gate; an invalid certificate
names the exact remaining predicate.
