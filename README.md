# Master Rallye RE

Clean-room interoperability and preservation research for *Master Rallye* (2001).

The repository contains only tools, documentation, machine-readable forensic
metadata, and synthetic test data. Original game resources remain external and
read-only.

## Current scope

Phase R2 is complete: the validated vehicle DX/DXT library now drives a native
Blender add-on with single-resource and vehicle-folder import, editable meshes,
preview materials, and preserved draw/group/source metadata. The R1 corpus
result remains 78/78 vehicle DX resources parsed and validated. R2 excludes
course resources, executable analysis, and writing game formats.

## Blender add-on

Build the installable local ZIP with:

```powershell
py -3 tools/build_blender_addon.py
```

Install the ignored `dist/master_rallye_io-r2.zip` from Blender preferences.
The add-on provides **File > Import > Master Rallye DX (.dx)** and **Import
Master Rallye Vehicle Folder**. It was tested with Blender 5.2.2 LTS; Blender
4.3+ is the expected API baseline, but other versions were not tested.

The importer creates one normally editable mesh per DX, retains physical draw
membership, source vertex/triangle IDs, and exact source-normal provenance as
mesh attributes, and stores group, texture-slot, material-candidate,
validation, and trailing-layout metadata on the object. Blender preview UVs use
direct source V; this is intentionally independent from the unchanged glTF
`flip-v` policy. Blender-calculated display normals avoid known Blender 5.2.2
native custom-normal crashes while the source values remain preserved. It is
an import/authoring tool only: arbitrary edits cannot yet be
written back to the game. See `docs/blender-importer.md`.

## Library and research CLI

The package lives in `src/master_rallye`. Run the CLI from the repository root:

```powershell
py -3 tools/mrtool.py inspect "..\Data.sma_unpacked\DataGx\Vehicles\Astero\complete.dx" --json ".research-output\r1\astero-inspect.json"

py -3 tools/mrtool.py export `
  "..\Data.sma_unpacked\DataGx\Vehicles\Astero\complete.dx" `
  --format gltf `
  --output ".research-output\r1\astero-complete" `
  --flip-v --strict

py -3 tools/mrtool.py scan-vehicles `
  "..\Data.sma_unpacked\DataGx\Vehicles" `
  --report research/r1/vehicle-coverage.json `
  --markdown research/r1/vehicle-coverage.md `
  --unknown-records research/r1/unknown-records.json
```

Exports are local validation artifacts under ignored `.research-output/` and
must not be committed. DXT parsing preserves raw stored BGRA rows; PNG export
explicitly uses the `flip-vertical` presentation policy. The evidenced glTF
vehicle preview uses `--flip-v` as a separate UV-coordinate transform. The
material preview uses the first non-`Null` texture only; all original ordered
slots and candidates remain metadata.

## Reproduce R0 metadata

```powershell
py -3 tools/scanner/inventory.py `
  --source "..\Data.sma_unpacked" `
  --inventory research/r0/inventory.json `
  --relationships research/r0/relationships.json

py -3 tools/scanner/text_map.py `
  --source "..\Data.sma_unpacked" `
  --relationships research/r0/relationships.json

py -3 tools/scanner/probe_dxt.py `
  research/r0/inventory.json `
  --output research/r0/dxt-probe.json
```

The generated paths are archive-relative; the external source location is not
embedded in reports. Earlier forensic tools remain under `tools/prototypes`
and `tools/scanner` for reproducibility.

Run the synthetic-only suite with:

```powershell
py -3 -m unittest discover -s tests\synthetic -v
```
