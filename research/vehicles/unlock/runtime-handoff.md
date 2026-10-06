# R5V-G.1 final Race Details runtime handoff

The locked-state and natural-unlock tests have passed on the corrected staged
Vehicle Select scene. This handoff tests the new display-only Race Details
hooks and a short ID26 race regression. It does not require replaying the cup
unlock.

## Candidate and exact runtime provenance

Run commands from the `master-rallye-re-vehicles` checkout. The currently
staged runtime tree is:

```text
effective executable:
D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\unlock\runtime-package\MRallye.exe

effective resource Root:
D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\unlock\runtime-package\

effective Vehicle Select scene:
D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\unlock\runtime-package\DataScene\FrontendScreens\VehicleSelect.xml

expected executable SHA256:
722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7

expected VehicleSelect.xml SHA256:
6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d
```

The source retail EXE SHA256 is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
the final candidate is 3,121,214 bytes and has 78 verified patch operations.
Three ID26-only wrappers cover all group-`0x35` Race Details branches. The
runtime package updater replaces only `MRallye.exe` and its package manifest;
it preserves existing profile and options state without reading or writing
those state files.

If the package still contains the preceding G.1 EXE, close the game and update
only that file and the package manifest with:

```powershell
python tools\vehicle_unlock_runtime_package.py install-candidate `
  --package-root ".research-output\vehicles\unlock\runtime-package" `
  --candidate-exe ".research-output\vehicles\unlock\candidate\MRallye_g1_final_racedetails.exe"
```

Immediately before launch, verify the full package:

```powershell
python tools\vehicle_unlock_runtime_package.py verify `
  --package-root ".research-output\vehicles\unlock\runtime-package" `
  --allow-runtime-state
if ($LASTEXITCODE -ne 0) { throw "G.1 runtime package verification failed" }
```

Continue only on `PASS`. Launch the verified copy with the package as working
directory so its active resource Root remains unambiguous:

```powershell
$root = (Resolve-Path ".research-output\vehicles\unlock\runtime-package").Path
Start-Process -FilePath (Join-Path $root "MRallye.exe") -WorkingDirectory $root
```

The previous capture header reported this exact package Root, and the human
confirmed locked slot art and disabled acceptance there. After launch, confirm
the next capture still reports the same Root.

## Human checks

Use the already-unlocked profile in the staged package (`T1CupCar1=True`). Do
not reset or replace its PlayerState.

1. Enter **Master Rallye → Race Details** with Mercedes ID26. Confirm the
   visible vehicle line reads `MERCEDES ML-320`, `GALOCAL UNKNOWN` is absent,
   and the current leg/country text remains correct. Capture as
   `g1-racedetails-masterrallye`.
2. Enter **Rallye Cup → Race Details** with the same vehicle. Confirm the same
   Mercedes name and normal race number text. Capture as
   `g1-racedetails-rallyecup`.
3. Switch to stock ID0 and visit Race Details in either mode. Confirm its stock
   vehicle name is unchanged.
4. With ID26 selected, run one short race smoke. Confirm the Mercedes model and
   textures still load and steering/physics remain normal. Capture
   `Race/Car0/CarID=26`, `Race/Car0/CarClass=0`, `Race/Car0/CarType=Mercedes`,
   `Race/Car0/WheelType=Mercedes`, and the established red colour canary if
   available.

Broker evidence for each Race Details capture should include:

```text
Frontend/RaceDetails/CurrentVehicleString = MERCEDES ML-320
Frontend/RaceDetails/CurrentRaceString    = mode-appropriate current event text
Frontend/RaceDetails/Race                 = MASTER RALLYE or RALLYE CUP
RaceData/Competitor0/CarID                = 26
Race/Car0/CarID                           = 26
```

The Broker proves the published string and participant identity; the human
visual check proves the rendered name. The current race string naturally
varies by event and should not be matched to a fixed literal.

## Already confirmed separately

The exact preceding G.1 candidate and corrected active Root passed the human
locked-state gate: fresh state showed `CAR LOCKED`,
`UNLOCK BY WINNING 2 T1 CUPS`, locked slot art, `UI/Enabled=False`, and normal
accept did not select ID26. After fulfilling the T1 Cup requirement, ID26
became selectable with its normal Mercedes thumbnail and `UI/Enabled=True`.
The new Race Details candidate preserves those hooks and the physical ID26
record. A full stage/results/frontend-return lifecycle is not required or
claimed by this handoff.
