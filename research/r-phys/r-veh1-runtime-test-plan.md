# R-VEH1 — Runtime Test Closeout

The three planned compositions were run successfully. Results below reflect
the runtime observations supplied by the project operator. No executable hash,
manifest path, or rollback outcome was included with those observations.

## Original test setup and restore

The compatibility entrypoint used when these plans were prepared was:

```powershell
python tools/physics_bind.py
```

The wizard detects the install root from the repository's parent when it can;
otherwise enter `D:\Game\Master Rallye`. For a rerun, select the physics
family first, then carrier type `7` / Navara and the model donor listed below.
Review the preview, confirm with `Y`, and use the generated executable shown
by the tool. The candidate names below match the original read-only plan; if a
same-named output or manifest already exists, follow the suffixed path shown
in the preview.

Keep the game closed while applying or restoring a composition. Restore each
manifest after the observation, before applying another test. Restore checks
all tracked hashes first and refuses without partial restore if any applied
file was changed after the test setup.

## Runtime test 1 — Full-family regression

Composition:

```text
Carrier:       7 / Navara
Physics family: Trooper
Model donor:   Trooper (use physics-family model)
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

**Result: PASS — `CONFIRMED_BY_RUNTIME`.** The Trooper model appeared
correctly and Trooper physics was active. This confirms the composer preserved
the previously verified full-family behavior.

Restore:

```powershell
python tools/vehicle_composer.py restore --manifest "D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Trooper-M-Trooper-composition.vehicle-compose.json"
```

## Runtime test 2 — Independent model and physics families

Composition:

```text
Carrier:       7 / Navara
Physics family: Trooper
Model donor:   Navara (keep the carrier model)
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

**Result: PASS — `CONFIRMED_BY_RUNTIME`.** The visible model was Navara while
Trooper physics was active. The different wheel placement visibly reflected
Trooper configuration rather than Navara configuration. This confirms that
model donor and physics family can differ in this tested composition.

Restore:

```powershell
python tools/vehicle_composer.py restore --manifest "D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Trooper-M-Navara-composition.vehicle-compose.json"
```

## Runtime test 3 — Pure model swap with forklift

Composition:

```text
Carrier:       7 / Navara
Physics family: Navara
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
unknown implicit runtime reads remain unresolved.

**Result: PASS — `CONFIRMED_BY_RUNTIME`.** The forklift model appeared, the
game loaded into a race, and Navara physics remained active and functional.
Because carrier and physics family were both Navara, no EXE family mapping
change was required. This also confirms forklift can serve as a model donor
without a same-named normal physics family.

**Additional runtime result — `CONFIRMED_BY_RUNTIME`:** collision and damage
behavior were absent in this composition. The current retail
`forklift/car.dx` has a tag-101 block, but the parser rejects its hull because
nine coordinate components are non-finite; it therefore contains no usable
collision hull. This structural finding is consistent with the runtime result,
but does not prove the exact cause of the absent collision or damage behavior.
See [the tag-101 corpus report](../r4b/tag101-corpus.md). A future forklift
model package with valid collision data could behave differently.

Restore:

```powershell
python tools/vehicle_composer.py restore --manifest "D:\Game\Master Rallye\.research-output\r-veh1\manifests\MRallye_C-Navara-P-Navara-M-forklift.vehicle-compose.json"
```

## Runtime conclusion

The demonstrated cases establish full-family replacement, independent model
and physics selection, and a model-only donor swap without an EXE family
patch. The tested forklift package has no runtime collision or damage
behavior; this asset-specific result does not establish that every arbitrary
pairing works or make unreported rollback claims.
