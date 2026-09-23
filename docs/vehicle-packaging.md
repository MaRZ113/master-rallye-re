# Vehicle staging and SMA packaging (R4E)

`inspect-vehicle VEHICLE_DIR` lists exact car/complete/wheel draw-slot DXT references and unresolved names. `bundle-vehicle VEHICLE_DIR replacements.json --output STAGING` copies validated replacements into `STAGING/DataGx/Vehicles/<vehicle>/` and writes `manifest.json` at the staging root. Replacements JSON maps an existing basename to a separately written file. Unchanged game resources are recorded as dependencies and need not be copied. Sidecar TXT remains optional tooling metadata. An unresolved texture blocks bundling.

The R4G build-vehicle-mod command accepts a VehicleProject JSON with source_vehicle_dir, resources, texture_edits and/or texture_replacements; see docs/vehicle-project.md. It validates and stages only changed resources. --sma requires a full unpacked original tree via --sma-root and a fresh explicit archive destination. A sparse staging tree alone is not a complete Data.sma replacement. Existing output and source-overwrite checks fail closed.

`pack-sma ROOT --output Data.sma [--overrides overrides.json]` accepts a tree whose immediate roots are DataGame, DataGx, and/or DataScene. Overrides map archive-relative paths to replacement files, leaving the unpacked tree untouched. `unpack-sma source.sma --output DIR` checks root layout and CRC before extraction. The E5 full-tree Python-generated archive is **CONFIRMED_BY_RUNTIME**: the game accepted it, loaded Astero, and displayed the known E1 UV edit. This proof applies to the original extracted tree plus a controlled override; it does not cover sparse or malformed archives.

## R4G VehicleProject build

The VehicleProject validator checks all source roles, donor hashes, fixed draw/material identities, topology candidates, bounds, tag101 transform, texture dependencies and referenced DXT integrity. The builder compiles approved changes and stages only modified resources, with an optional explicit full-tree Data.sma destination. It refuses to overwrite an existing archive or source vehicle. See docs/vehicle-project.md. The established full-tree Python SMA workflow remains runtime-confirmed; B1/C1/P1/W1 asset effects are pending.
