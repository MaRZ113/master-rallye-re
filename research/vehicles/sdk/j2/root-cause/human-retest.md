# R5V-J.2 ID27 reverse-map fix — minimal runtime retest

Use only the `root-cause-candidate` generated for this audit. Do not reuse the
stack-hotfix candidate: it is crash-free but still restores ID27 as Navara.
This candidate is not runtime-qualified until the check below passes.

## Candidate and preflight

```powershell
$root = 'D:\Game\Master Rallye\master-rallye-re-vehicles'
$exe = 'D:\Game\Master Rallye\MRallye.exe'
$candidate = Join-Path $root '.research-output\vehicles\sdk\j2-reentry\root-cause-candidate'
$loader = Join-Path $candidate 'mr-runtime-launcher.exe'
$bundle = Join-Path $candidate 'bundle'

Get-FileHash -Algorithm SHA256 $exe
Get-FileHash -Algorithm SHA256 $loader
& $loader --verify $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'Candidate verification failed; do not launch' }
```

Expected retail EXE SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

Expected launcher SHA256:
`1fb190ae85d2b7b119576a650e4723abb1130ef4bbdee6d353357087e3de66c7`.

The launcher must report `RUNTIME_BUNDLE_VERIFIED` with 248 operations and
243 resources. Do not continue if any identity differs.

## Short fresh-process test

Start a new process:

```powershell
& $loader --integrated $exe $bundle
```

Keep the same player context throughout each select/leave/reopen pair. Do not
switch PlayerID between the before and after observations.

1. Open Vehicle Select with a stock vehicle; confirm no crash.
2. Switch T1 -> T2 -> T3 and back; confirm native class navigation still works.
3. Select and normally commit ID27. Return to Quick Race and record the
   active player ID plus `Frontend/QuickRace/Car0` (or Car1 for player 1).
4. Reopen Vehicle Select for that same player. Expected state: `PlayerID`
   unchanged, stored Quick Race CarID still 27, `CarModel=27`,
   `selectedCar=27`, `YValue=1`, `XValue=7`, and visible `R5V T2 QUALIFIER`.
5. Repeat once for ID26. Expected: T1/local7, CarModel and selectedCar 26,
   YValue=0, XValue=7, Mercedes identity unchanged.
6. Select stock ID7 and reopen for the same player. Expected: T2/local0 and
   the ordinary Navara selection remains functional.
7. If the profile has ID27 locked, verify its normal accept action remains
   blocked. Do not change unlock state to force this check.

One Observatory capture of the reopened ID27 state is useful. Include the
same player's before/after `PlayerID`, `Frontend/QuickRace/Car0`,
`Frontend/QuickRace/Car1`, `Frontend/VehicleSelect/CarModel`,
`FrontEnd/Network/selectedCar`, `UI/XYButton/YValue` and
`UI/XYButton/XValue`. This distinguishes stored physical identity from the
scene-local highlight and prevents a cross-player comparison.

If ID27 still resolves to Navara, stop. Capture the same-player pair and the
loaded bundle identity; do not add another patch until the new first divergent
state is known. No new Cup, Master Rallye, AI, or SplitScreen run is required
for this bounded correction.
