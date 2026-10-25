# Creating a donor-based vehicle

Vehicle SDK v1 Option A edits compatible existing vehicle packages. It does
not import arbitrary FBX/OBJ models or create new draw/material/collision
formats.

## Project files

`addon init` creates:

```text
Project/
  addon.json                 addon identity and policies
  vehicle-project.json      existing VehicleProject edit recipe
  donor-provenance.json     source and compatibility reminder
  README.md                 project-specific first steps
  assets/source/<donor>/    empty local donor drop folder
  assets/build/             reserved for author intermediates
  physics/                  reserved for authored physics notes
  artwork/                  reserved for frontend artwork
```

The initializer never copies an installed donor. Set the generated
`source_vehicle_dir` to a user-owned retail/demo vehicle directory or put a
copy you are entitled to use in the project source folder.

## Existing authoring workflow

Use `py -3 tools/mrtool.py validate-vehicle <vehicle-project.json>` during
editing and `build-vehicle-mod` when you need the existing vehicle-only
staging output. Blender import/export and the DX/DXT operations documented in
[`docs/vehicle-sdk.md`](../../../../docs/vehicle-sdk.md) remain the source of
truth for supported edits. The addon project validator calls the same
`VehicleProject` checks; it does not duplicate DX/DXT parsing, collision
validation, or Blender logic.

Supported edits remain bounded by the donor: preserve draw/material identity,
use same-dimension DXT replacements, keep finite recognized collision data,
and allow the existing validators to recompute/verify supported bounds.
Unknown fields or unsupported byte layouts fail validation.

## Retail versus demo donors

A demo directory is not accepted just because its files are named `car.dx`.
The current project bridge runs the same grammar, draw/material, bounds,
collision and DXT dependency validators used by VehicleProject. That is a
necessary static check, not a general demo-build compatibility qualification.
No broad demo runtime profile was added in J.3-A. If a demo file fails, use a
qualified retail donor or keep the demo candidate outside runtime packaging
until its precise incompatibility is separately resolved.

## Independent family output

The addon manifest supplies a unique family. The build copies only the
validated DX roles and resolved DXT dependencies to
`DataGx/Vehicles/<model_family>`. The source donor directory and stock files
are read-only inputs. Resource names are checked for collisions when manifests
are compiled together.
