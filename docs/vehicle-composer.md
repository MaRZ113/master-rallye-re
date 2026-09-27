# Master Rallye Vehicle Composer

**Version: 0.1.0**

The Vehicle Composer builds a supported vehicle setup by combining a retail
carrier, a named physics family, and a model donor. The choices can be
independent. It creates a separate executable when a family binding is needed
and installs a reversible loose model overlay when the donor differs from the
runtime family.

## Supported game build

Only the verified retail executable build is supported:

```text
MRallye.exe SHA-256:
bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4
```

The tool refuses unknown executable builds. Do not use it as evidence of
compatibility with another release or executable revision.

## Requirements

- Python 3.10 or newer.
- A retail game installation with `MRallye.exe`.
- No additional Python packages are required for the CLI.

The project test suite uses Python's built-in `unittest` framework.

## Quick start

Extract the release ZIP, open a terminal in the
`MasterRallye-VehicleComposer-v0.1.0` folder, and run:

```powershell
python tools/vehicle_composer.py
```

The wizard detects or asks for the game installation root. If you prefer to
start in the game folder, run the script by its full path, for example:
`python "<COMPOSER_FOLDER>\tools\vehicle_composer.py"`.

The interactive wizard detects the install root when possible, lists all
named configuration families, asks for the physics family first, then asks
which initialized retail carrier to replace and which model donor to use.
Review the preview before confirming. Use `--dry-run` to preview without
writing files:

```powershell
python tools/vehicle_composer.py --dry-run
```

## Concepts

- **Carrier:** the initialized retail vehicle type/slot being replaced, such
  as Navara.
- **Physics family:** the named `Vehicles/<family>` configuration used by the
  native vehicle broker. It also determines the runtime family namespace.
- **Model donor:** the model resource package whose files are supplied at the
  runtime family path when donor and physics family differ.
- **Runtime family:** the physics family. Retail uses this identity for both
  `DataGx\Vehicles\<family>` model/resource lookup and
  `Vehicles/<family>` configuration plus `<family>/Player1` modifications.

The carrier, physics family, and model donor are separate choices. If carrier
and physics family match, no executable family patch is needed. An independent
model donor is supplied by a loose model overlay; a donor does not need a
same-named physics family.

## Runtime-verified examples

The following compositions passed the project's runtime tests on the
supported retail build:

### Full Trooper restoration

```text
Carrier: Navara
Physics family: Trooper
Model donor: Trooper
```

The Trooper model appeared and Trooper physics was active.

### Trooper physics with Navara model

```text
Carrier: Navara
Physics family: Trooper
Model donor: Navara
```

The Navara model appeared while Trooper physics was active. The changed wheel
placement reflected the Trooper configuration.

### Forklift model swap

```text
Carrier: Navara
Physics family: Navara
Model donor: forklift
```

The forklift model appeared in a race while Navara physics remained active.
Because carrier and physics family are both Navara, this composition needs no
EXE family mapping change. Collision and damage behavior were absent at
runtime. The current package has no usable collision hull: its parsed `car.dx`
tag-101 block fails validation because nine coordinate components are
non-finite. This is an asset limitation, not a composition failure; a future
forklift package with valid collision data could behave differently.

These tests establish the listed composition classes, not every possible
model/physics pairing.

## Model resource sources

The Composer inventories vehicle resources from the packaged `Data.sma` and
loose files under `DataGx\Vehicles`. Loose files override archive members at
the same family-relative path. The manifest records the source and hashes of
files used by an overlay.

## Apply, status, and restore

The Composer previews destinations and changes before applying them. It writes
a separate executable when a carrier-to-runtime-family patch is required,
backs up replaced or removed loose model files, and records hashes in a
manifest. It never needs to overwrite the original `MRallye.exe`. Restore
checks that applied files still match the recorded hashes and refuses an
unsafe partial restore if a tracked file was externally changed.

Useful interactive commands:

```powershell
python tools/vehicle_composer.py status
python tools/vehicle_composer.py restore
```

Restore can discover known manifests and offer a menu. To restore one known
composition directly:

```powershell
python tools/vehicle_composer.py restore --manifest "<GAME_INSTALL_ROOT>\.research-output\r-veh1\manifests\example.vehicle-compose.json"
```

Keep the game closed while applying or restoring. Launch the separate output
executable shown in the preview when one is created.

## Special cases

- **Ufo:** absence of `wheel.dx` is expected for this wheel-less package. A
  Ufo donor cannot replace a runtime package if an unmaskable archive wheel
  resource would remain active.
- **forklift:** the retail model package is available as a model donor; no
  same-named normal physics family is required for the verified model-only
  Navara composition.

## Advanced and automation commands

The JSON workflow remains available for automation. These commands require an
existing schema-v1 family-binding or schema-v2 composition JSON file; most
users can use the interactive wizard instead. `validate` checks that file,
`apply` uses the same validated backend as the wizard, and `restore` restores
a tool-created copy or composition:

```powershell
python tools/vehicle_composer.py validate `
  --install-root "<GAME_INSTALL_ROOT>" `
  --config "<PATH_TO_BINDING_JSON>"

python tools/vehicle_composer.py apply `
  --install-root "<GAME_INSTALL_ROOT>" `
  --config "<PATH_TO_BINDING_JSON>"

python tools/vehicle_composer.py restore --output-exe "<GAME_INSTALL_ROOT>\MRallye_physicsbound.exe"
```

For a composition, `apply` chooses the output executable name automatically
unless `--output-exe` is supplied. Existing schema-v1 binding files continue
to mean that the model donor equals the physics family. Schema-v2 compositions
name the donor explicitly.

`tools/physics_bind.py` remains available for existing scripts and users; it
dispatches through the same implementation.

## License

The MIT license applies to this project's original code and documentation.
Master Rallye and its game assets remain the property of their respective
rights holders. The Vehicle Composer release does not include game files.

## Known limitations

The mechanism is confirmed by runtime tests for the three examples above. Every
arbitrary asset combination has not been tested. Geometry, wheel placement,
textures, damage, collision, and other runtime dependencies can vary by donor.
The tool supports only the exact retail executable hash listed above.
