# R5V-J.2 remaining human runtime qualification

Use the existing combined two-addon candidate. Do not build or install two
separate profiles. The raw 2026-10-09 captures already prove that this bundle
has materialized Mercedes ID26 and R5VQualifier ID27 in separate player/AI
scenarios, but the combined lifecycle gates below remain open.

## Exact candidate and preflight

From the `master-rallye-re-vehicles` checkout:

```powershell
$exe = 'D:\Game\Master Rallye\MRallye.exe'
$loader = '.research-output\vehicles\sdk\j1\launcher-release-final\mr-runtime-launcher.exe'
$bundle = '.research-output\vehicles\sdk\j1\reference-runtime-final'

Get-FileHash -Algorithm SHA256 $exe
& $loader --verify $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'J.2 combined runtime bundle verification failed' }
```

Expected retail EXE SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
(3,121,214 bytes). Expected launcher SHA256:
`9d4a98d01166362933974f8c376f3a42323feecfdfd021af7df0a3b1aceb31b5`.
Expected addon plan SHA256:
`357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`.
Expected native patch manifest SHA256:
`78c1070f2e656677f02d22f5d4fdff457e43c7ba74c67bb4e5a5c1488ca53179`.
Expected resource index SHA256:
`2fc7121c3d4f66c407cedbcb47dc223c580301971e3d12d16aa197c7a70a3384`.
The effective resource root is
`.research-output\vehicles\sdk\j1\reference-runtime-final\resource-root`.
Only after preflight reports 243 verified resources and 246 native patch
operations should the integrated launch begin:

```powershell
& $loader --integrated $exe $bundle
```

Do not alter the retail EXE or replace/overwrite stock files. Keep all game
profile/save files external and preserve them after the test. Existing
unqualified adjacent wrapper DLLs are fail-closed conflicts; do not bypass
that refusal. After each test, verify the retail EXE SHA again.

## Required test order and captures

Use the same combined candidate, record the loader log separately from
Observatory Broker captures, and write down the visible result. The archive
labels below are proposed labels; the observer must verify the actual values.

1. **SplitScreen composition, if the stock mode permits the pairing.** Use
   ID26/T1 and ID27/T2 as the two human vehicles. Verify independent controls,
   cameras and rendering; capture `j2-splitscreen-dual-addon`. For each player,
   verify its physical ID, class and `CarType`/`WheelType`. If stock mode rules
   prevent the pairing, capture that state and report the limitation without
   forcing invalid values.
2. **Vehicle Select re-entry.** Run a race using ID27, return through the
   normal results/frontend route, reopen Vehicle Select without navigating,
   and capture `j2-reentry-id27`. Expected selected identity: ID27, T2 local
   index 7, `R5V T2 QUALIFIER`. Repeat for ID26 (`j2-reentry-id26`, T1 local
   index 7) and stock ID7 (`j2-reentry-stock-id7`). Distinguish stored
   Quick Race `Car0`, displayed `CarModel`, `selectedCar`, and XYButton local
   ordinal; `selectedCar` alone is not a commit oracle.
3. **Rallye Cup persistence.** Start a genuinely new T2 Cup and continue until
   ID27 is naturally selected. Save `j2-cup-id27-stage1`, finish and advance
   one stage, then capture `j2-cup-id27-stage2`. Compare the complete physical
   ID/class/DriverID roster. The roster must be reused, not rerolled.
4. **Master Rallye persistence.** Start a genuinely new T2 competition and
   continue until ID27 naturally appears. Capture `j2-master-id27-new`, allow
   native save, close the process, start a fresh process through the same
   verified bundle, resume and capture `j2-master-id27-resume`; advance a stage
   and capture `j2-master-id27-next` if practical. Compare the native
   `MasterRallye/CarN` and live `Race/CarN` identity including DriverID. Do not
   use or mutate an older stock-only competition as the inclusion test.
5. **Visual and removal controls.** Confirm both addon models/wheels, frontend
   names, locked and unlocked presentation where available, Results identities,
   Race Details, HUD and progress marker colors (Mercedes red, qualifier
   magenta). Close the modded run, then start the unchanged EXE without the
   launcher and verify stock startup; do not delete external profile data.

## Expected identity oracle

| Vehicle | Physical ID / class | Runtime family | Race colour |
|---|---|---|---|
| Mercedes | 26 / T1 | `Mercedes` for CarType and WheelType | `[1,0,0,1]` |
| R5VQualifier | 27 / T2 | `R5VQualifier` for CarType and WheelType | `[1,0,1,1]` |

Results display names are `JEAN-PIERRE STRUGO` for ID26 and `R5V TEST DRIVER`
for ID27; these do not set or replace native DriverID. A successful Broker
capture proves state values, not visual artwork or gameplay quality.

## Stop conditions

Stop the affected test on a wrong physical ID/class/family, missing resource,
crash, corrupt model, control/camera crossover, unexpected profile mutation,
or failed hash/preflight. Do not continue into J.3 or ID28 qualification.
