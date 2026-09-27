# R-VEH1 — Human Runtime Test Plan

These are the three static candidates prepared for the human. No composition
was applied and no new behavior is runtime-confirmed by this report. Test one
composition at a time and restore its manifest before starting the next test.

## Before each test

From the repository directory, run:

```powershell
python tools/physics_bind.py
```

The wizard detects the install root from the repository's parent when it can;
otherwise enter `D:\Game\Master Rallye`. Select carrier type `7` / Navara,
then the physics family and model source listed below. Review the preview,
confirm with `Y`, and use the generated executable shown by the tool. The
candidate names below match the current read-only plan; if a same-named output
or manifest already exists, follow the suffixed path displayed in the preview.

Keep the game closed while applying or restoring a composition. Restore each
manifest after the observation, before applying another test. Restore checks
all tracked hashes first and refuses without partial restore if any applied
file was changed after the test setup.

## Runtime test 1 — Full-family regression

Wizard choices:

```text
Carrier:       7 / Navara
Physics family: Trooper
Model source:  1 / Use physics-family model (Trooper)
Confirm:       Y
```

Current static plan:

| Item | Planned value |
|---|---|
| Composition | `C=Navara, P=Trooper, M=Trooper` |
| Runtime family | `Trooper` |
| EXE | Patch required; `D:\Game\Master Rallye\MRallye_C-Navara-P-Trooper-M-Trooper.exe` |
| Planned EXE SHA-256 | `ca2301742aade178d93424a9b3bdffc74618608b1f9fe026e59f4875bedf43d7` |
| Model overlay | None; natural Trooper package is 31 archive files |
| Manifest | `D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Trooper-M-Trooper-composition.vehicle-compose.json` |

Observe whether the frontend model appears where applicable, the race body and
wheels load, wheel placement is correct, Trooper driving behavior remains, and
the game loads normally. This checks that the new composer preserves the
previous full-family setup; it is not pre-marked as a new runtime pass.

Restore:

```powershell
python tools/physics_bind.py restore --manifest "D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Trooper-M-Trooper-composition.vehicle-compose.json"
```

## Runtime test 2 — Independent model and physics families

Wizard choices:

```text
Carrier:       7 / Navara
Physics family: Trooper
Model source:  2 / Keep carrier model (Navara)
Confirm:       Y
```

Current static plan:

| Item | Planned value |
|---|---|
| Composition | `C=Navara, P=Trooper, M=Navara` |
| Runtime family | `Trooper` |
| EXE | Patch required; `D:\Game\Master Rallye\MRallye_C-Navara-P-Trooper-M-Navara.exe` |
| Planned EXE SHA-256 | `ca2301742aade178d93424a9b3bdffc74618608b1f9fe026e59f4875bedf43d7` |
| Model overlay | 31 Navara archive files written under `DataGx\Vehicles\Trooper`; no archive fallbacks or existing loose files were found in the current local plan |
| Manifest | `D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Trooper-M-Navara-composition.vehicle-compose.json` |

Observe whether the Navara model is visible while Trooper physics/handling
remains active. Record wheel placement, missing textures/resources, frontend
and race loading, and any crash. This is the central independent-donor test
and remains **NOT_RUNTIME_CONFIRMED** until the human reports the result.

Restore:

```powershell
python tools/physics_bind.py restore --manifest "D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Trooper-M-Navara-composition.vehicle-compose.json"
```

## Runtime test 3 — Pure model swap with forklift

Wizard choices:

```text
Carrier:       7 / Navara
Physics family: Navara
Model source:  3 / Choose another model donor
Model donor:   forklift
Confirm:       Y
```

Current static plan:

| Item | Planned value |
|---|---|
| Composition | `C=Navara, P=Navara, M=forklift` |
| Runtime family | `Navara` |
| EXE | **No patch and no EXE copy** because `C == P` |
| Model overlay | 22 forklift archive files written under `DataGx\Vehicles\Navara`; 21 unrelated, unreferenced Navara archive paths remain as fallbacks |
| Manifest | `D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Navara-M-forklift.vehicle-compose.json` |

The planner resolved every texture reference it parsed from forklift
`car.dx`, `complete.dx`, and `wheel.dx` to the donor package. The 21 listed
archive fallbacks are not referenced by those parsed core DX records, but
unknown implicit runtime reads remain unresolved. Observe game startup, model
visibility, car/complete/wheel resources, texture completeness, race loading,
wheel placement, collision, damage, and crashes or missing resources. Static
package completeness does not predict forklift runtime behavior.

Restore:

```powershell
python tools/physics_bind.py restore --manifest "D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Navara-M-forklift.vehicle-compose.json"
```

## Evidence to return

For each test, report the actual executable launched (or confirm the pure
model-only test used the retail EXE), whether frontend and race loading
succeeded, body/wheel/texture visibility, wheel placement, handling, collision
and damage behavior, and any crash or missing resource. Also return the
generated manifest path and restore result. These reports will be recorded as
human runtime evidence; the current static plans and unit tests do not promote
any R-VEH1 composition to `HUMAN_RUNTIME_CONFIRMED`.
