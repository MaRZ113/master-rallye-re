# VehicleProject and build

A project JSON points to an unchanged donor vehicle folder and optional edited artifacts. wheel.dx is optional. Paths in the JSON may be absolute or relative to the JSON file. Blender's Save Vehicle Project collects imported roles, last exported DX paths, staged DXT replacements, and car collision transform settings.

Example fields:

    vehicle_name: Astero
    source_vehicle_dir: protected original Astero directory
    resources.car.dx.source_sha256: source file SHA-256
    resources.car.dx.candidate: edited car.dx path
    resources.car.dx.collision_scale: [1.2, 1.0, 1.0]
    resources.car.dx.collision_translation: [0.0, 0.0, 0.0]
    resources.complete.dx.source_sha256: source file SHA-256
    resources.wheel.dx.source_sha256: source file SHA-256
    texture_replacements.body-tga.dxt.source_sha256: source DXT SHA-256
    texture_replacements.body-tga.dxt.candidate: edited DXT path

The candidate field accepts a safe same-topology DX export or an existing-draw topology export. The validator reparses each edited DX, checks source hashes and draw/material identities, checks geometry coverage by marker-1339 bounds, proves same-topology candidates by reproducing the byte patch, and checks topology candidates against fixed donor draw records and collision bytes. It validates source roles, texture references, referenced DXT headers/payload sizes, and optional wheel presence. Results are PASS, WARN, or FAIL with diagnostics. Unsupported project/edit keys fail.

For source-indexed edits instead of a candidate file, a resource can use attributes with the validate-edit schema. For PNG texture input, texture_edits maps a DXT basename to source_sha256 and png fields. Texture outputs preserve the donor header and dimensions.

build-vehicle-mod validates first, compiles permitted edits and collision transforms, and writes only changed assets under output/staging/DataGx/Vehicles/<vehicle>/. output/manifest.json includes source/output hashes, validation and dependencies. For a full archive, pass --sma-root pointing to the complete original unpacked tree and --sma to a fresh, explicit output path. Packaging never overwrites an existing SMA. Installation into the game is a deliberate separate action.

The current Blender workflow is: Import Vehicle Folder -> edit/export each changed DX or DXT -> set and preview collision transform on car.dx -> Save Vehicle Project -> Validate Vehicle -> Build Vehicle Mod. The advanced source metadata remains available.
