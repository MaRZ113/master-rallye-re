# G.1 locked-state correction — staged runtime handoff

## Why the previous retest is inconclusive for XML behavior

The candidate EXE was active in the supplied captures: its SHA256 was
`3346eb00442b88cca3f76f7a65606ca56006c5b981acdbf0ee4ad16412e5b055`. The
native dump's `Root` header and executable image path both resolve to the
captured `.../.research-output/retired-worktrees/e0.1/research-output/r5v_f_2e/runtime/`
directory. That directory had `Data.sma` and the qualified loose Mercedes
assets, but no `DataScene/FrontendScreens/VehicleSelect.xml`. The generated
correction overlay was elsewhere in `.research-output/vehicles/unlock/overlay/`.
Thus the prior run tested the EXE half, but could not have consumed the
generated loose XML from its active Root. The archive/loose-file precedence is
not inferred from that absence.

The path above is only a read-only source for the captured resource files. The
new package is materialized under the canonical checkout's ignored
`.research-output/vehicles/unlock/runtime-package/`; the historical tree is not
modified or used as an active source checkout. The packager omits prior
`PlayerState.xml` files so the new package starts with a fresh profile.

## Stage and verify before launch

From the `master-rallye-re-vehicles` checkout, stage the one coherent package:

```powershell
python tools\vehicle_unlock_runtime_package.py stage `
  --resource-root ".research-output\retired-worktrees\e0.1\research-output\r5v_f_2e\runtime" `
  --candidate-exe ".research-output\vehicles\unlock\candidate\MRallye_g1_locked_state_correction.exe" `
  --scene-overlay ".research-output\vehicles\unlock\overlay\DataScene\FrontendScreens\VehicleSelect.xml" `
  --output-root ".research-output\vehicles\unlock\runtime-package"
```

Then run this verification command immediately before launch:

```powershell
$root = (Resolve-Path ".research-output\vehicles\unlock\runtime-package").Path
python tools\vehicle_unlock_runtime_package.py verify --package-root $root
if ($LASTEXITCODE -ne 0) { throw "G.1 runtime package verification failed" }
```

Proceed only when the verifier prints `PASS`. It prints the exact staged paths:

* effective executable: `<package root>\MRallye.exe`
* intended resource Root: `<package root>`
* staged scene: `<package root>\DataScene\FrontendScreens\VehicleSelect.xml`
* expected EXE SHA256: `3346eb00442b88cca3f76f7a65606ca56006c5b981acdbf0ee4ad16412e5b055`
* expected scene SHA256: `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`

Launch that executable with the package root as its working directory:

```powershell
Start-Process -FilePath (Join-Path $root "MRallye.exe") -WorkingDirectory $root
```

After launch, the next Observatory capture's raw header must report `Root` as
that same package root. The prelaunch verifier proves the on-disk tree; the
capture header proves which root the process selected. If they differ, stop.

## Fresh-profile locked comparison

Use the new package's fresh profile, with `UnlockCars` and `UnlockAll` off.
Compare ID3 first, then ID26:

| Oracle | Locked ID3 control | Locked ID26 expected |
|---|---:|---:|
| `Progress/UnlockedCars/T1CupCar1` | `False` | `False` |
| `Frontend/VehicleSelect/CarModel` | `-1` | `-1` |
| `Frontend/VehicleSelect/ManufacturerName` | `CAR LOCKED` | `CAR LOCKED` |
| `Frontend/VehicleSelect/ModelName` | `UNLOCK BY WINNING 2 T1 CUPS` | same |
| `FrontEnd/Network/selectedCar` | `3` | `26` |
| `UI/Enabled` | `False` | `False` |

`selectedCar` is the highlighted/current frontend identity; it is not a commit
oracle. Confirm visually that the locked thumbnail is shown and normal accept
does not enter Vehicle Setup or a race. The previous ID26 interaction was
accepted into a race (`Race/Car0/CarID=26`, class `0`), so this interaction
check is required.

The corrected package has not yet received a human runtime test. Do not trace
the appended AI/control path unless the capture confirms the package Root and
the expected scene hash was staged, and the UI still differs from the ID3
control.

## Separate known Race Details issue

The two additional Broker captures show ID26 (`Race/Car0/CarID=26`) while
`Frontend/RaceDetails/CurrentVehicleString` is `GALOCAL UNKNOWN` in both
Master Rallye and Rallye Cup. Their race-description fields are respectively
`LEG 1/10 - FRANCE` and `RACE 1/3`. This is a separate, observed display defect;
its producer has not been traced in this correction pass because the tested
scene deployment was not proven. Do not claim a Race Details fix or start a
commit-handler investigation from these captures.

After scene provenance and locked behavior are confirmed, continue the bounded
G.1 check: test naturally unlocked ID26 for normal thumbnail, `MERCEDES` /
`ML-320`, Vehicle Setup `MERCEDES ML-320`, existing Quick Race identity, both
Race Details modes, and one short Mercedes race regression. Preserve
`Race/Car0/CarID=26`, `CarClass=0`, `CarType=Mercedes`, and
`WheelType=Mercedes`. This is not a full stage/results lifecycle test.
