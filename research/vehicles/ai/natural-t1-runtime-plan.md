# R5V-H.1 natural T1 ID26 runtime handoff — completed / historical

This pre-test handoff is retained as provenance. H.1 natural Quick Race
selection and the fixed Results name have since been
`CONFIRMED_BY_RUNTIME`; see the closeout in
[runtime-results.md](runtime-results.md). The active H.2 procedure is
[mode-aware-runtime-plan.md](mode-aware-runtime-plan.md).

## Candidate and prelaunch gate

Use only the staged `natural-t1-id26` runtime package:

* EXE: `.research-output/vehicles/ai/natural-t1-id26/runtime-package/MRallye.exe`
* SHA256: `e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a`
* Size: 3,121,214 bytes
* Runtime Root: `.research-output/vehicles/ai/natural-t1-id26/runtime-package/`
* Patch manifest: `.research-output/vehicles/ai/natural-t1-id26/candidate/MRallye.patch-manifest.json`

From the repository root, verify the staged package before launch:

```powershell
python tools\vehicle_hardened_runtime_package.py verify `
  --runtime-root '.research-output\vehicles\ai\natural-t1-id26\runtime-package' `
  --source-root '.research-output\vehicles\unlock\runtime-package' `
  --candidate-manifest '.research-output\vehicles\ai\natural-t1-id26\candidate\MRallye.patch-manifest.json' `
  --profile natural-t1-id26
if ($LASTEXITCODE -ne 0) { throw 'Natural T1 package verification failed' }
```

Launch the package's `MRallye.exe` from that package directory. The package
does not include PlayerState; let the game create a fresh profile and do not
copy a progressed save. The randomizer is absent. This test uses the normal
native T1 Quick Race chooser, not a forced-slot hook.

## Natural-selection test

1. Set up a normal single-player Quick Race: one human, three opponents, T1,
   stock initial player ID0, ordinary stock course. Leave ID26 locked as a
   player choice; the AI pool is expected to be independent of that player
   unlock gate.
2. Start a newly generated race and capture its active state as
   `natural-t1-race-01` (then `-02`, etc. for subsequent new races). Do not use
   Restart as another selection sample; Restart reuses the current roster.
3. For every capture, expect four participants and one player. AI CarIDs must
   be distinct T1 IDs from `{1,2,3,4,5,6,26}`; ID7 is a failure because it is
   the first T2 vehicle. CarClass must remain 0/T1. If ID26 is absent, return
   to the frontend and create a new Quick Race; do not call absence from a
   finite sample a pool failure.
4. Stop at the first structural anomaly: wrong class, duplicate AI identity,
   ID7, changed participant count, wrong vehicle family, crash, or inert AI.
   To keep the observation bounded, stop after ten independently generated
   races if ID26 has not appeared and report the captures without a runtime
   pass claim.
5. When any AI slot contains CarID26, capture active race state as
   `natural-t1-id26-race`. Verify that slot's DriverID is a normal published
   native value and record it without expecting a particular ID; verify
   CarClass 0, CarType/WheelType `Mercedes`, and that the visible Mercedes AI
   drives and progresses normally. Finish the race.
6. Capture Results as `natural-t1-id26-results`. For the ID26 row, expect the
   display-only name `JEAN-PIERRE STRUGO` and the correct Mercedes result icon.
   The exact ML-320 historical pairing is unproven. The patch must not change
   the native DriverID selection or participant DriverID. Other stock result
   names should remain normal.
7. Optionally invoke native Debug->Dump on Results to check that the composed
   hardened candidate remains alive and continues past the NULL StringList.
   The older H.0.1 pass already confirmed StringList safety; this is a
   regression check on the new composition. Preserve its output separately.

For each saved Observatory JSON capture, preserve the matching raw sidecar.
The checker validates exact candidate provenance and Broker identity, but it
cannot prove visible rendering, AI behavior, physics, or race completion.

Example Broker checker command for an active-race capture:

```powershell
$runtimeRoot = (Resolve-Path '.research-output\vehicles\ai\natural-t1-id26\runtime-package').Path
python tools\check_vehicle_ai_runtime.py --mode natural `
  --candidate-manifest '.research-output\vehicles\ai\natural-t1-id26\candidate\MRallye.patch-manifest.json' `
  --expected-exe-sha256 'e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a' `
  --expected-image-path "$runtimeRoot\MRallye.exe" `
  --expected-active-root "$runtimeRoot" `
  'PATH_TO_CAPTURE\natural-t1-id26-race.json'
```

The highest checker status is `NATURAL_T1_POOL_CAPTURE` or
`NATURAL_T1_MULTI_CAPTURE_SUMMARY`, a Broker-state match only. Human runtime
observation is required to promote the natural pool and Results display.

## Pass boundary

The H.1 runtime pass requires an actual naturally selected ID26 AI, its
independent Mercedes actor identity, normal AI driving/progression, a normal
finish, and the fixed Results display. The test does not change `Race/NumCars`
from four, prove other modes, alter native DriverID selection, or establish
any AI pool probability distribution.
