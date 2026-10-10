# R-CAM1-A3c: one read-only France1 restart capture

This DLL is a lifecycle observation build. It has **no Freecam toggle or flight**.
Do not enable new FreeCamera settings or deliberately break game assets.

Use the pristine retail EXE (SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`)
and the user's accepted Windowed/Borderless renderer settings. Keep the existing
INI; enable its existing `[Trace] Enabled=1` if disabled. There is no new config
version. The final build/package and hashes are recorded in [validation.md](validation.md).
With the game closed, keep the previously accepted DLL separately and place this
candidate `d3d8.dll` beside the game EXE. No deployment or game launch was done by
the agent. Returning to the accepted DLL reverses the observer installation.

Perform one ordinary sequence:

1. Launch and enter **France1, offline single-player Quick Race**.
2. Confirm ordinary gameplay; return to frontend.
3. Enter **France1 Quick Race again**, using the same setup.
4. After successful second entry, press **F10** once.
5. Quit normally. Keep that newly generated `frame-*.jsonl` and its `session-*.jsonl`
   from `D:/Game/Master Rallye Pristine/MRRRenderer/logs`.

The ring retains transitions from before F10. Old A3b logs do not contain the new
`race_epoch_snapshot` and cannot answer this question. A full camera sweep is not
requested. Several native requests may occur, so generation need not equal two.

Expected observation integrity:

- Session has `race_epoch_observer`: `installed=true`, reason
  `read_only_native_lifecycle_installed`.
- F10 has `race_epoch_snapshot`: `observing=true`, `hook_ownership_intact=true`,
  `poisoned=false`, and `camera_writes_authorized=false`.
- Distinct request/queue lifetimes lead to commit and **execute_return**. The
  current successful generation follows the current request, not the first race.
- A newly attached RaceLimits owner has a new lifetime serial, including if its
  address is reused. The current owner has one registration/live membership,
  zero pending memberships, clear retirement, correct AI, initialized readable
  allocations and supporting offline participant/context values.
- UI/rendering, F10 and normal quit remain healthy.

The observation will determine whether `owner_attach` occurs **inside** the job's
execute interval (nonzero `execution_job_lifetime`) or afterwards (zero/unproven
link). The latter is an honest blocker, not a failed visual test: that event's
source relationship must be traced before a certificate can be introduced. Copied
scene/source names identify which native load actually corresponds to France1;
they must be reconciled with source rather than using a guessed course number.

FAIL for the observer: crash, hook ownership mismatch, missing expected events,
wrong-thread/reentrant quarantine, or stale earlier-owner proof after the new
request. A reused job pointer is explicitly unqualified and needs lifetime proof;
the trace should show its old/new serials, never inherited authorization.
No deliberate failed-load runtime test is needed: native-source failure fixtures
already verify that error/default paths cannot reactivate earlier success.

Optional offline summary, from the canonical repository:

```powershell
python modernization/renderer/tools/analyze_race_epoch.py "D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-<new-capture>.jsonl"
```

Report whether both races and return to frontend worked, whether normal rendering
and quit were unchanged, and provide the new F10/session files. Even a healthy
capture does not test camera flight, restoration, input, error paths or distant
world activation. Those remain for the functional implementation after admission
is closed.
