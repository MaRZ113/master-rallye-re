# R5V-H.2 human runtime handoff

This procedure has been completed. R5V-H is now **FULL PASS / CLOSED**; this
page is retained as test provenance and is no longer a pending human handoff.
Capture values and integrity checks are in
[runtime-results.md](runtime-results.md).

## Exact candidate and prelaunch check

Use the staged H.2 package only:

* Profile: `mode-aware-natural-t1-id26`
* Executable: `.research-output/vehicles/ai/mode-aware-id26/runtime-package/MRallye.exe`
* Executable SHA256: `de5e81c0b126619574834f25ac941cd491139235fd2f89086d8e125f063dcac9`
* Size: 3,121,214 bytes
* Resource Root: `.research-output/vehicles/ai/mode-aware-id26/runtime-package/`
* Patch manifest: `.research-output/vehicles/ai/mode-aware-id26/candidate/MRallye.manifest.json`
* Patch manifest SHA256: `9cb7adbd71a6207218cfba10e94b48d13363f698e6398b03994725f1bf6882eb`
* Runtime package manifest SHA256: `1fbdc6bc2f0e760717ceb8102b580f683d7b45ba93a8edc84b25e84eda22d5cb`

From the repository root, run this exact verifier before launching:

```powershell
python tools\vehicle_hardened_runtime_package.py verify `
  --runtime-root '.research-output\vehicles\ai\mode-aware-id26\runtime-package' `
  --source-root '.research-output\vehicles\unlock\runtime-package' `
  --candidate-manifest '.research-output\vehicles\ai\mode-aware-id26\candidate\MRallye.manifest.json' `
  --profile mode-aware-natural-t1-id26
if ($LASTEXITCODE -ne 0) { throw 'R5V-H.2 package verification failed' }
```

The package verifier checks exact pristine source reconstruction, exact H.1
parent, candidate and manifest, staged resource inventory, and the pinned
VehicleSelect overlay. The package excludes generated PlayerState, so use an
isolated profile/state directory. Launch the packaged EXE with its runtime
package as the working directory. No randomizer DLL or old randomizer is
present.

## Test 1 — new Rallye Cup

1. Start a new T1 Rallye Cup. Do not Resume or continue a Cup created before
   installing H.2; its old roster is expected to remain unchanged.
2. Create a newly generated Cup until an AI participant naturally has physical
   `CarID=26`. Do not infer a probability from attempts. Capture the first
   matching active race as `h2-rallyecup-id26-stage1`.
3. Confirm that the same slot has `CarClass=0`, AI PlayerType, and
   `CarType=Mercedes` / `WheelType=Mercedes`. Human observation should confirm
   a distinct Mercedes model and normal AI driving/progression; the Broker
   checker cannot prove visible behavior.
4. Complete/advance to the next Cup race and capture
   `h2-rallyecup-id26-stage2`. Verify that the slot's `CarID`, `CarClass`, and
   `DriverID` remain the same and no new roster generation occurred.
5. If ID26 does not appear, create another *new* Cup. Do not use Restart or a
   later stage as a fresh roster sample. Stop at any wrong class, ID7 in T1,
   duplicate-selection regression, changed count, or gameplay anomaly.

## Test 2 — new Master Rallye competition and native resume

1. Create a **new** T1 Master Rallye competition. Do not Resume an old save for
   the inclusion test; an old roster is expected to remain as saved.
2. Generate a new competition until its native AI roster includes ID26. Capture
   the active state and native roster as `h2-master-id26-new`. Record the
   matching `MasterRallye/CarN/{CarID,CarClass,DriverID}` and `Race/CarN/*`.
3. Confirm CarClass 0, AI PlayerType, and Mercedes runtime family. Complete the
   stage far enough for the stock native save/progression path to run.
4. Close `MRallye.exe` completely. Start a fresh process with the same isolated
   native save and resume the same Master Rallye competition. Capture as
   `h2-master-id26-resume`; verify the exact same physical roster entry and
   native DriverID were restored.
5. Advance to the next stage if practical and capture
   `h2-master-id26-next`; verify the ID26 roster entry remains unchanged.

## Test 3 — Invitation shared-generator smoke

Invitation uses the same audited generator and T1 pool as Cup through
`FUN_0045BE10 -> FUN_0045ABC0` (RaceType 8). If Invitation is available in the
test profile, create a new Invitation and confirm that an AI CarID26 can
materialize as T1/Mercedes. A later-stage same-roster check is useful and
consistent with the historical parallel-branch observation. Keep the evidence
labelled separately from Cup/Master; current-branch Invitation runtime is
pending.

## Controls and evidence

* Keep Quick Race at H.1's already-confirmed natural pool. No new Quick Race
  human pass is needed unless shared behavior regresses.
* Leave Challenge unchanged; its opponents remain authored.
* Player ID26 may remain locked. AI eligibility is independent of
  `Progress/UnlockedCars/T1CupCar1`.
* Preserve matching Observatory JSON/raw pairs and candidate provenance.
  Record CarID, CarClass, DriverID, CarType, WheelType, mode/RaceType, player
  unlock state, active slot, and roster-generation point.
* For results, expect display-only `JEAN-PIERRE STRUGO` when physical CarID is
  26; do not expect native DriverID to be changed to Strugo. G.2 should resolve
  the AI vehicle's stock audio profile 0 while retaining physical CarID26.
* Complete the available Cup/Master lifecycle checks, but do not infer support
  for unrelated events, higher participant counts, or any selection
  probability from these runs.

The highest automated state verdict is a Broker/package match. Only the human
runtime observation can establish visible vehicle identity, AI behavior,
stage reuse, fresh-process persistence, or race completion.
