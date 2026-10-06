# Master Rallye Vehicle Composer v0.1.0

Builds a vehicle package from a retail carrier, a physics family, and a model donor, subject to asset-specific compatibility.

## Quick Start

1. Download and extract [Vehicle Composer v0.1.0](https://github.com/MaRZ113/master-rallye-re/releases/tag/v0.1.0).
2. Open a terminal in the extracted package folder and run `python tools/vehicle_composer.py`.
3. Select the detected or prompted game installation root.
4. Choose a physics family, retail carrier, and model donor; review the preview.
5. Confirm the build and follow the generated install instructions. Use `--dry-run` to preview without writing.

Exact combinations vary in wheel placement, textures, collision, damage, and resource dependencies. Review the build report before installing.

## What it does

The Composer inventories packaged resources and loose overrides, validates vehicle configuration, and produces a staged vehicle package. Tested workflows include interactive CLI use and retained automation commands.

## Requirements

- Windows and Python 3.10 or newer
- A supported Master Rallye retail installation
- The release package and the user's own game files

## Compatibility

The release supports the pristine retail executable with SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Other executable builds and arbitrary model/physics pairings have not been verified.

## Known limitations

Runtime-verified examples include Navara carrier/Trooper physics/Trooper model, Navara carrier/Trooper physics/Navara model, and a Forklift model on Navara physics. The tested Forklift payload has no usable collision hull, so collision and damage behavior were not demonstrated for it.

## License

Original project code and documentation are MIT licensed. The release contains no game files.
