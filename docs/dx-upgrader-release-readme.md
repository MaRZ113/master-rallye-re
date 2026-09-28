# Master Rallye DX Upgrader v0.1.0

Convert supported older Master Rallye **vehicle model files** for the verified
retail build. The tool works on DX files you already have; it does not include
or obtain any game files.

## What this tool does

Some vehicle models cooked by older Master Rallye demos use DX revision 131.
The tested retail build expects the later revision-135 vehicle serialization.
This tool converts supported revision-131 vehicle DX files into revision 135.

The tool has been runtime-tested with Trooper and Forester `car.dx`,
`complete.dx`, and `wheel.dx`. Other supported vehicle files have passed the
project's corpus and structural checks, but have not all been tested in-game.

## What this tool does not do

- It does not convert GXM source files. It needs already-cooked DX files.
- It does not rewrite DXT textures. Keep the matching texture files unchanged.
- It does not download, extract, or include demo or retail game assets.
- It does not add a new selectable vehicle slot or change vehicle physics.

## Supported game build

Runtime compatibility was verified with the retail executable whose SHA256 is:

```text
bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4
```

This hash identifies the runtime-tested build; the converter itself processes
DX files and does not patch or require the executable.

## Requirements

- Windows and Python 3.10 or later.
- Your own compatible Master Rallye demo and retail files.
- No third-party Python packages. The command-line tool uses the Python
  standard library.

## Quick start

Extract this ZIP, open PowerShell in the extracted
`MasterRallye-DX-Upgrader-v0.1.0` folder, and check the tool:

```powershell
python tools/upgrade_dx_131_to_135.py --version
python tools/upgrade_dx_131_to_135.py --help
```

To convert one vehicle file, replace the example paths with paths in your own
demo copy:

```powershell
python tools/upgrade_dx_131_to_135.py "DemoVehicle\car.dx" -o "Converted\car.dx"
```

The tool writes a JSON report next to the output DX. It refuses to overwrite
existing output files unless you add `--force`. `--force` is for single-file
mode only and never permits using the same input and output path. Single-file
mode rejects revision-135 input as already converted.

To convert the direct vehicle roles in a folder:

```powershell
python tools/upgrade_dx_131_to_135.py --vehicle-dir "DemoVehicle" --output-dir "DemoVehicle-Rev135"
```

Directory mode processes `car.dx`, `complete.dx`, and `wheel.dx` when present.
It writes a manifest and copies valid revision-135 DX files unchanged. The
output folder must not already exist. DXT and other non-DX files are not
copied or changed by this command; directory mode does not accept `--force`.

## Using converted vehicle files

Keep the source package unchanged. Put the converted DX files into a separate
working copy of the model package and bring over its matching DXT textures
unchanged. Then use your normal retail restoration setup.

Model conversion, physics, and selectable slots are separate:

- **Model conversion** changes supported DX serialization.
- **Physics** comes from a named vehicle configuration family.
- **Vehicle slots** are retail executable/menu registration and are not added
  by this tool.

The separately published
[Vehicle Composer](https://github.com/MaRZ113/master-rallye-re/releases/tag/v0.1.0)
can use a converted model package with an existing retail carrier slot. See
the [demo vehicle restoration walkthrough](docs/restoring-demo-vehicles.md).

## Validation evidence

The current corpus covers 8 vehicle families, 20 unique revision-131 DX
payloads, and 15 unique revision-135 payloads. All 20 unique revision-131
payloads converted and passed strict generated-output validation. Ten
same-source role pairs were verified using matching GXM SHA256 values; all
135 directly paired draw records matched the conversion rule, with no
mismatches. The generated candidates differed from the official revision-135
outputs only in local triangle ordering for those ten pairs.

Trooper and Forester `car`, `complete`, and `wheel` candidate outputs were
loaded successfully in the tested retail runtime. These two families are the
runtime-tested examples; corpus validation of other files is not an in-game
test.

## Known limitations

- The converter supports the proven Master Rallye vehicle DX revision-131
  grammar. It does not claim support for arbitrary DX resources.
- It does not reproduce the original 9.10.0 output byte-for-byte. The
  official local triangle reorder is intentionally not reproduced; preserving
  the original revision-131 triangle order was runtime-tested for Trooper and
  Forester.
- It does not convert GXM or DXT, add vehicle physics, or patch vehicle slots.
- Full historical GXM/GXI/cooker format reconstruction is outside the scope
  of this release.

## License

The tool's original code and documentation are MIT licensed; see `LICENSE`.
Master Rallye and its game assets remain the property of their respective
rights holders. No game files are included.
