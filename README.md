# Master Rallye RE

Clean-room interoperability and preservation research for *Master Rallye* (2001).

The repository contains only tools, documentation, machine-readable forensic
metadata, and synthetic test data. Original game resources remain external and
read-only.

## Current scope

Phase R3 is complete: the validated vehicle DX/DXT library drives a native
Blender add-on with single-resource and vehicle-folder import, editable meshes,
preview materials, preserved draw/group/source metadata, and a fail-closed
same-topology **positions-only** DX export. All 78 vehicle resources produce a
byte-identical zero-edit result and pass an in-memory single-position patch.
On 2026-09-22, human testing in the original game runtime confirmed visible,
artifact-free same-topology position edits in `complete.dx` (presentation/menu)
and `car.dx` (race). Course resources, general DX serialization, and executable
analysis remain out of scope.

**FIRST CONFIRMED WRITABLE MASTER RALLYE VEHICLE GEOMETRY — 2026-09-22.**
The confirmed scope is same-topology vertex-position editing only. Topology,
UV, normal, and material writing are not runtime-confirmed.

## Blender add-on

Build the installable local ZIP with:

```powershell
py -3 tools/build_blender_addon.py
```

Install the ignored `dist/master_rallye_io-r3.zip` from Blender preferences.
The add-on provides **File > Import > Master Rallye DX (.dx)** and **Import
Master Rallye Vehicle Folder**. It was tested with Blender 5.2.2 LTS; Blender
4.3+ is the expected API baseline, but other versions were not tested.

The importer creates one normally editable mesh per DX, retains physical draw
membership, source vertex/triangle IDs, and exact source-normal provenance as
mesh attributes, and stores group, texture-slot, material-candidate,
validation, and trailing-layout metadata on the object. Blender preview UVs use
direct source V; this is intentionally independent from the unchanged glTF
`flip-v` policy. Blender-calculated display normals avoid known Blender 5.2.2
native custom-normal crashes while the source values remain preserved. Only
same-topology position edits can be written through the experimental
original-template exporter; arbitrary edits cannot be written back. See
`docs/blender-importer.md` and `docs/dx-writer.md`.

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

## R2.5 legacy evidence consolidation

The recovered texFinder project was treated as non-authoritative historical
evidence. Its useful DXT writer model was independently reproduced: all 1,143
vehicle DXT resources round-trip byte-identically through the new conservative
same-size, exact-header-preserving encoder. Legacy DX v1 demonstrates a safe
positions-only template patch; legacy v3 fails modern draw/index validation and
was rejected. Evidence-scored TXT discovery now handles nonstandard filenames,
and nullable `HasAlpha` / `UsesAlpha` / `IsNoise` values survive into Blender
metadata. The read-only audit is available as:

```powershell
py -3 tools/mrtool.py audit-textures `
  "..\Data.sma_unpacked\DataGx\Vehicles" `
  --report ".research-output\r2_5\texture-audit.json"
```

See `research/r2_5/findings.md` for legacy consolidation and
`research/r3/findings.md` / `docs/dx-writer.md` for the safe writer.
