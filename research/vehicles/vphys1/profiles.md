# Physics profile v1

Place an optional `physics-profile.json` next to `addon.json` and
`vehicle-project.json`. No sidecar preserves the existing clone-only workflow.
The profile requires the exact original `vehicles.xml` and `Modifications.xml`
member hashes, donor family, addon family, typed overrides and text notes.

```json
{
  "profile_version": 1,
  "donor_family": "Navara",
  "runtime_family": "MyAddon",
  "source_sha256": {
    "DataGame/vehicles.xml": "<exact SHA256>",
    "DataGame/Modifications.xml": "<exact SHA256>"
  },
  "overrides": {
    "DataGame/vehicles.xml": {
      "Dimensions/WheelBase": 2.51,
      "Chassis/CentreOfGravity": [0, 0.35, 0.2],
      "Chassis/UseCuboidMOI": false
    },
    "DataGame/Modifications.xml": {
      "Player1/Modifications/Suspension/Front/SpringRate": 1000
    }
  },
  "notes": "User-supplied parameters; player spring value is an additive native-unit delta."
}
```

That example has placeholder hashes; generate a valid donor-default starter:

```powershell
C:/Python315/python.exe tools/vehicle_physics_profile.py init --vehicles ../corpora/retail/Data.sma_unpacked/DataGame/vehicles.xml --modifications ../corpora/retail/Data.sma_unpacked/DataGame/Modifications.xml --donor Navara --family MyAddon --output my-physics.json
```

Edit only existing relative field paths. Types are recovered from the pinned
donor: numbers for Float/Int, real JSON booleans for Bool, arrays of exactly 2/3
numbers for vectors, safe existing tyre prefixes for TyreType. Integer booleans,
unknown paths, foreign namespaces, duplicate JSON keys, wrong hashes, invalid
identities, NaN/infinity and malformed arrays are rejected. Engine gear/torque
array counts cannot change in v1; existing indexed values can be edited.

Each CarID routes through its manifest's runtime/physics family. This format
does not reassign a stock donor or use `Vehicles/CarN` as a persistent family.
Those names are native per-participant outputs. Multiple profiles can compose
into distinct named namespaces; tests prove ownership isolation. Actual runtime
installation still follows the separately qualified capacity/layout compiler.

## Validation limits

The builder checks source archive identity and identical loose member inputs,
full typed schema, positive dimensions, positive sprung mass, inertia inputs,
known DriveType values, idle/rev ordering, increasing torque-curve abscissae,
existing tyre prefixes and nonnegative rates/travel where required. Player
defaults are added to the base and checked again for both Player1 and Player2.

SDK authoring guards include dimensions (0,20], |RideHeight|≤2, travel≤2,
finite float32-compatible numbers of magnitude≤1e9, and bounded native-unit
player deltas (ride ±2, bias ±1, diff ratio ±20, rates ±1e6). These are **policy
guards, not verified engine clamps or a promise of stable handling**. Negative
ride height has native prefix evidence but no stock example; qualify it in-game.
Global Surface.xml and Vehicles/Tyres tables are immutable in profile v1.

## Rebuild a frozen visual project

```powershell
C:/Python315/python.exe tools/build_vehicle_physics_candidate.py --project .research-output/vehicles/vlancer6/candidate-04/project --profile research/vehicles/vphys1/fitment-physics.json --output .research-output/vehicles/vphys1/my-next-test
```

The output must be new and under the repository's ignored research-output
directory. The helper copies authoring configuration/UI, retains source hashes,
builds typed family XML and the ordinary asset closure, invokes the existing
collection/native damage compiler and builds/verifies the external launcher.
It does not rebuild GT geometry or launch the game. Existing unsupported
capacity/layout requests fail; there is no fallback stock replacement.
`--base-manifest`, `--retail-data-sma`, `--retail-data-root` and `--retail-exe`
can select compatible local inputs. Original EXE/DLL files remain read-only.

Change the **project profile and rebuild**. Generated runtime XML remains sealed;
editing it directly is correctly rejected by the launcher. Do not weaken runtime
integrity checking to make physics files writable inside a prepared bundle.

## Diagnostics

```powershell
C:/Python315/python.exe tools/preview_vehicle.py .research-output/vehicles/vlancer6/build-04/assets/car.dx --model race --physics-xml .research-output/vehicles/vphys1/final-fitment/author-build/DataGame/vehicles.xml --physics-family LancerEvo4
C:/Python315/python.exe tools/diagnose_vehicle_fitment.py --assets .research-output/vehicles/vlancer6/build-04/assets --vehicles .research-output/vehicles/vphys1/final-fitment/author-build/DataGame/vehicles.xml --family LancerEvo4 --reference-profile .research-output/vehicles/vlancer6/build-04/preview-profile.json --output .research-output/vehicles/vphys1/my-fitment-report.json
C:/Python315/python.exe tools/validate_vehicle_physics_candidate.py --baseline .research-output/vehicles/vlancer6/candidate-04/runtime --candidate .research-output/vehicles/vphys1/final-fitment/runtime --profile research/vehicles/vphys1/fitment-physics.json --output .research-output/vehicles/vphys1/my-regression.json
```

For exact native CPU replay use `validate_vehicle_physics_native.py` with
`--exe`, `--vehicles`, `--family`, `--output`, optionally `--sensitivity`.
It needs the locally available Unicorn package; no library is bundled or
installed automatically. For this workstation it is available through
`.research-output/vehicles/scale1/python-tools` in PYTHONPATH.
The Previewer and prefix replay do not perform contact integration or establish
live wheel poses/handling. Blender is not required.
