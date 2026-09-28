# Restoring demo vehicle models for retail

This guide describes how to convert already-cooked demo vehicle DX files and
use them with an existing retail vehicle slot. It does not add a new slot.

## Before you start

You need your own copy of a compatible Master Rallye demo and your own retail
installation. The DX Upgrader includes no game files and does not extract
assets from an installation or archive.

The converter supports the observed vehicle DX revision-131 layout. It does
not accept GXM source files directly. If your source is only GXM, the original
Demo 9.10.0 cooker remains the established source-side bridge; cooker setup
is outside this guide.

## Convert a vehicle package

1. From your demo copy, locate a vehicle model folder that contains one or
   more of `car.dx`, `complete.dx`, and `wheel.dx`. Keep the original folder
   unchanged and work from a copy.

2. Extract `MasterRallye-DX-Upgrader-v0.1.0.zip`. Open PowerShell in the
   extracted `MasterRallye-DX-Upgrader-v0.1.0` folder and check the CLI:

   ```powershell
   python tools/upgrade_dx_131_to_135.py --version
   ```

3. Convert the DX roles. For a whole folder, use:

   ```powershell
   python tools/upgrade_dx_131_to_135.py --vehicle-dir "DemoVehicle" --output-dir "DemoVehicle-Rev135"
   ```

   Replace `DemoVehicle` with the folder you found in your own demo copy. The
   output directory must be new. The tool processes direct `car.dx`,
   `complete.dx`, and `wheel.dx` files when they are present, and writes a
   `manifest.json` describing each conversion or unchanged revision-135 copy.

   To convert one file instead, use:

   ```powershell
   python tools/upgrade_dx_131_to_135.py "DemoVehicle\car.dx" -o "Converted\car.dx"
   ```

   Single-file mode also writes a JSON report beside the output file. Do not
   use the same path for input and output.

4. Directory mode outputs only DX files and its manifest. Copy the matching
   DXT textures and any other required model resources from your own source
   package into a separate assembled package, unchanged. The DX Upgrader does
   not convert or copy them.

5. Use the assembled model package through your existing retail restoration
   workflow. Do not replace the original demo or retail source files while
   preparing the package.

## Model, physics, and vehicle slots are different

- **Model conversion** makes supported old vehicle DX serialization usable
  by the tested retail build. It does not create a full vehicle by itself.
- **Physics** comes from the named vehicle configuration selected by the
  retail runtime or Vehicle Composer.
- **Vehicle slot / executable patching** determines which vehicles are
  selectable. DX conversion does not add a new roster slot.

The current practical route is:

```text
demo vehicle DX -> DX Upgrader -> converted model package -> Vehicle Composer -> existing retail carrier slot
```

Vehicle Composer is a separate tool and release:
[Master Rallye Vehicle Composer v0.1.0](https://github.com/MaRZ113/master-rallye-re/releases/tag/v0.1.0).
It can combine an existing carrier slot, a physics family, and an independent
model donor. The DX Upgrader is not bundled into Vehicle Composer.

Creating additional permanent slots, including a 26th slot or later, requires
a separate executable/roster project. That work is not part of model
conversion or this guide.

## Runtime-tested examples

The tested retail runtime successfully loaded converted `car.dx`,
`complete.dx`, and `wheel.dx` resources for Trooper and Subaru Forester. These
are the runtime-tested families. Other current corpus payloads passed
structural conversion checks but should not be described as individually
runtime-tested.

The conversion preserves the revision-131 local triangle order. It does not
reproduce the official Demo 9.10.0 triangle reorder; the no-reorder result was
runtime-tested for Trooper and Forester.

## Safety and scope

Keep originals and converted outputs separate. The tool refuses in-place
conversion, does not overwrite existing output without `--force`, and validates
converted output before writing it. Existing revision-135 files are checked
under a separate policy and copied unchanged by directory mode.

The current corpus establishes support for the observed vehicle revision-131
grammar, not every historical DX resource. GXM cooker behavior, full GXI
format reconstruction, DXT conversion, new retail vehicle slots, and arbitrary
physics/model combinations are outside this conversion workflow.
