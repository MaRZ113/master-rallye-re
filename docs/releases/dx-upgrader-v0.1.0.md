# Master Rallye DX Upgrader v0.1.0

Converts supported Master Rallye vehicle DX revision-131 files into revision-135 serialization.

## Quick Start

Extract the release ZIP, open PowerShell in the extracted
`MasterRallye-DX-Upgrader-v0.1.0` folder, then check the command:

```powershell
python tools/upgrade_dx_131_to_135.py --version
python tools/upgrade_dx_131_to_135.py --help
```

Convert a complete vehicle folder:

```powershell
python tools/upgrade_dx_131_to_135.py --vehicle-dir "DemoVehicle" --output-dir "DemoVehicle-Rev135"
```

Or convert one DX file:

```powershell
python tools/upgrade_dx_131_to_135.py "DemoVehicle\car.dx" -o "Converted\car.dx"
```

Inputs are preserved; converted files go to the output path.

## What it does

The tool converts supported revision-131 vehicle DX data to the revision-135 format accepted by the verified retail build. It does not include game files, a GXM cooker, or a DXT converter.

## Requirements

- Windows and Python 3.10 or newer
- A supported Master Rallye revision-131 vehicle DX file or vehicle folder
- The release ZIP from [GitHub Releases](https://github.com/MaRZ113/master-rallye-re/releases/tag/dx-upgrader-v0.1.0)

## Compatibility

Retail loading was tested with the listed Trooper and Subaru Forester `car.dx`, `complete.dx`, and `wheel.dx` candidates. Other corpus results are structural checks, not individual in-game tests.

## Known limitations

The converter preserves revision-131 local triangle order; it does not reproduce the official 9.10.0 triangle optimizer. Results are limited to the tested resources and their dependencies.

## License

Original project code and documentation are MIT licensed. The release contains no game assets or executables.
