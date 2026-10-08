# R5V-I.1 — independent T2 family human qualification

## Status and scope

**HISTORICAL HUMAN HANDOFF — SUPERSEDED BY RUNTIME EVIDENCE.** The exact
candidate's player-family routing and natural T2 AI participant materialization
are now recorded as `CONFIRMED_BY_RUNTIME` in
[`i1-runtime-evidence.json`](i1-runtime-evidence.json). This file preserves
the original test protocol and should not be read as a current request to
repeat it. The authored qualifier `R5VQualifier` at physical ID27/T2 local7 is
not historical Master Rallye content. Vehicle Select re-entry and race-marker
color remain public runtime-release gates.

Candidate profile: `i1-id27-r5v-qualifier-independent-t2-family`.

* Candidate EXE SHA256:
  `90abfbf9825f1cc7acebb3a1a2811a179e6474f2406433854e1ffdbc60bdd955`
* Candidate size: 3,121,214 bytes.
* Retail source SHA256:
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
* H.2 parent SHA256:
  `de5e81c0b126619574834f25ac941cd491139235fd2f89086d8e125f063dcac9`.
* Complete staged package:
  `D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\multislot\i1\runtime-package`.
* Effective executable: `MRallye.exe` in that package root.
* Effective runtime/resource root and working directory: that same package
  root; launch the EXE from there so its loose `DataScene`, `DataGame`, and
  `DataGx` resources are the staged ones.
* Effective Vehicle Select scene:
  `DataScene/FrontendScreens/VehicleSelect.xml` under the package root;
  expected SHA256
  `0b8c61efd2959a5b3b5dcef0d3810c2b445e021c465816627e87b9e3da2b4490`.
* Runtime package manifest:
  `r5v-i1-runtime-package.json` in the package root.
* Tracked derived patch inventory:
  [i1-candidate-manifest.json](i1-candidate-manifest.json); the generated
  package manifest and raw resource inventory remain in ignored output.

## Mandatory prelaunch verification

From the repository root, run:

```powershell
python tools\build_vehicle_multislot_i1.py verify
if ($LASTEXITCODE -ne 0) { throw 'R5V-I.1 candidate verification failed' }
python tools\vehicle_multislot_i1_runtime_package.py verify
if ($LASTEXITCODE -ne 0) { throw 'R5V-I.1 runtime package verification failed' }
```

Both commands must finish successfully. The candidate verifier reproduces the
EXE and manifest from the exact retail source and checks the known parent and
patched bytes. The package verifier checks the staged EXE, scene, family
assets, physics/modification overlays, hashes, and exact package file set. Do
not launch if either command fails. Do not copy only the EXE to another game
directory or reuse the I.0 package.

The generated package contains the candidate and 243 inventoried runtime
resources. It contains no user PlayerState/save, raw Observatory capture,
screenshot or Ghidra project. Do not inject unlock state or use cheats for the
qualification.

## Player/vehicle-select pass

Use a normal game profile and do not edit saves or bypass progression. First
record the native ID10/T2CupCar1 lock state. If ID27 is locked, verify its
locked presentation/requirement, `UI/Enabled=False`, and that normal accept
cannot commit it. Then complete the native T2 Cup requirement normally. If the
profile already has `Progress/UnlockedCars/T2CupCar1=True`, test the unlocked
selection and only repeat the locked check with a genuinely fresh profile if
one is readily available; do not reset or rewrite an existing save. T2 must be
legitimately reachable for either test.

1. Launch the package's `MRallye.exe` with the package root as its working
   directory.
2. Open Vehicle Select and navigate to T2 local7 / physical ID27.
3. Confirm the identity reads `R5V` / `T2 QUALIFIER`, not `SLOT PROOF` or
   `NAVARA DONOR`; confirm the current donor frontend art and stats 7/6/6/5 are
   expected for this qualification profile.
4. Confirm the independent preview loads. The body should show the magenta
   `paintjeep-tga.dxt` canary. The wheels and other donor-derived materials
   may remain Navara-derived.
5. Capture a Broker snapshot if available. Expected physical/class identity:
   `Frontend/VehicleSelect/CarModel=27`, class T2/local7. The capture supports
   identity but does not prove the visible material by itself.

## Player race and AI pass

First run one short offline Quick Race using a stock T2 player and randomizer
Stock/disabled. Verify after materialization:

* `Race/Car0/CarID=27`, `Race/Car0/CarClass=1`, player type.
* `Race/Car0/CarType=R5VQualifier` and `Race/Car0/WheelType=R5VQualifier`.
* The magenta body canary is visible, and the vehicle moves under normal
  controls with stable physics.
* Collision and damage remain functional; the HUD icon and progress marker
  still render for ID27.
* If practical, complete one race. A full stage/results/return pass is not a
  prerequisite for this short qualifier unless an anomaly appears.

Then start newly generated T2 Quick Races until ID27 is naturally selected for
one AI participant. Do not force it into a slot. Verify the selected AI has
`CarID=27`, `CarClass=1`, `PlayerType=AI`, `CarType=R5VQualifier`, and
`WheelType=R5VQualifier`; human observation must confirm the distinct magenta
vehicle drives normally. One natural AI pass is enough. No Cup/Master
persistence repeat is needed because the ID27 pool code is unchanged from
runtime-qualified I.0.

Suggested capture labels:

* `i1-id27-qualifier-select`
* `i1-id27-qualifier-player-race`
* `i1-id27-qualifier-ai-race`

## Regression and evidence limits

Confirm ID26 remains physical ID26 / T1 / Mercedes if it is visible during the
test. Do not change or infer native DriverID from the Results display label
`R5V TEST DRIVER`. ID25/Trooper's physical slot and frontend mapping remain
preserved, but its model payload is not included in this package. ID26 and
ID27 simultaneous SplitScreen was already runtime-proven by I.0; repeat only
if I.1 changes that routing or a regression appears.

This candidate preserves unlock oracle ID10, audio profile7, sparse T2/local7
mapping, all T2 AI pools and existing-roster persistence. The new physics
family is a separately named clone of Navara's 147 values; it intentionally
has no handling delta. Collision remains donor-derived. A pass proves that
the existing architecture can resolve a second independently named T2 family
at ID27; it does not prove arbitrary registry growth, unique model topology,
unique collision topology, custom audio authoring, or historical authenticity.

The remaining human re-entry/color checks are recorded separately from J0
compiler work; do not infer them from the older checklist below. No ID28,
custom ordering, or public runtime loader is included in this qualification.
