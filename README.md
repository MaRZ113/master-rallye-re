# Master Rallye RE

Clean-room interoperability and preservation research for *Master Rallye* (2001).

The repository contains only tools, documentation, machine-readable forensic
metadata, and synthetic test data. Original game resources remain external and
read-only.

## Current scope

Phase R4G hardens the runtime-confirmed R4F topology writer into a vehicle project workflow. Earlier R4C work established: the validated vehicle DX/DXT library drives a native
Blender add-on with single-resource and vehicle-folder import, editable meshes,
preview materials, preserved draw/group/source metadata, and a fail-closed
same-topology **positions-only** DX export. All 78 vehicle resources produce a
byte-identical zero-edit result and pass an in-memory single-position patch.
On 2026-09-22, human testing in the original game runtime confirmed visible,
artifact-free same-topology position edits in `complete.dx` (presentation/menu)
and `car.dx` (race). Course resources and general DX serialization remain
out of scope; targeted executable material tracing is documented below.

**FIRST CONFIRMED WRITABLE MASTER RALLYE VEHICLE GEOMETRY — 2026-09-22.**
That R3 milestone confirmed position writing. Subsequent E1, E3 and E4 human tests confirmed same-topology UV, vertex-color, and alpha-flag edits. The stronger R4E.1 normal test confirmed normal writing; topology writing remains outside the same-topology baseline.

Phase R4A has mapped the three vehicle resource roles across all 26 vehicle
folders: `complete.dx` is the assembled presentation resource, `car.dx` is the
race body/chassis resource, and `wheel.dx` is a separately instantiated race
visual template. Static `$chull`, collision XML, draw-group, and trailing-data
links are documented without claiming that collision is wholly stored in
`car.dx`. See `docs/vehicle-runtime-roles.md` and `research/r4a/`.

Phase R4B reconstructs the exact vehicle tag-101 collision-hull structure.
All 78 vehicle DX resources parse; tag 101 occurs in 28, with 27 finite,
non-empty validated hulls and one explicitly retained Forklift non-finite
outlier. Representation A is an AABB helper and representation B is a closed
convex polyhedron at **HIGH** confidence. The Blender add-on can display both
as read-only overlays. R3 remains positions-only; R4B adds no collision writer.
See `docs/formats/dx-collision.md` and `docs/blender-collision.md`.

Phase R4C adds an exact tag-101 serializer and conservative template-preserving
rigid translation. All 28 tag-101 sections and complete DX templates round-trip
byte-identically at zero edit; all 27 validated finite hulls pass in-memory
translation and full-DX reparse. An ignored Astero `(+0.40, 0, 0)` lateral
collision-only translation is **CONFIRMED_BY_RUNTIME** per the project owner's 2026-09-23 status update; the detailed observation log remains external. R4C itself did not add scale, rotation, topology, BSP, cylinder, or Blender collision
export; R4G per-axis scale is confirmed by the C1 human wall-contact test. See `docs/collision-writer.md` and `research/r4c/`.

Phase R4D.1 traced the serialized DX draw through its material loader to Direct3D 8: the draw mask copies to runtime +0x34; flag bytes 0/1 select alpha blend/test; the base and environment shaders expose concrete render and texture-stage states. Blender Preview V2 uses only the verified alpha mapping. Four isolated DXT probes now have human in-game results: M1/M3 reflection helpers, M2 glass source-alpha, and M4 active brake-glow alpha. See research/r4d_1/runtime-results.md. See docs/vehicle-materials.md and research/r4d_1/findings.md.

Phase R4E adds same-topology attribute authoring, same-size DXT replacement, exact
vehicle texture-user manifests, staging, and ZIP-compatible SMA helpers. Human testing confirms E1 UV, E3 vertex color, E4 alpha flag, and E5 full-tree Python Data.sma packing. E2 normal was inconclusive; stronger R4E.1 N1 and M1 human tests confirmed normal and environment-feature writing. The SAME-TOPOLOGY VEHICLE SDK V1 BASELINE is now frozen. See
`docs/vehicle-authoring.md`, `docs/texture-authoring.md`, and
`docs/vehicle-packaging.md`.

Phase R4F reconstructs existing-draw render topology while preserving material identities and collision bytes. The protected 78-file vehicle corpus rebuilds byte-identically at zero edit; the Astero +3-vertex/+1-triangle F1 candidate is **CONFIRMED_BY_RUNTIME**: its new triangle is visible and collision, damage, glass, wheels and general vehicle function remain normal. The old same-topology patch exporter remains the frozen SDK v1 path. See `docs/topology-authoring.md`, `docs/dx-render-rebuilder.md`, and `research/r4f/findings.md`.

## Blender add-on

Build the installable local ZIP with:

```powershell
py -3 tools/build_blender_addon.py
```

Install the ignored `dist/master_rallye_io.zip` from Blender preferences.
The add-on provides **File > Import > Master Rallye DX (.dx)** and **Import
Master Rallye Vehicle Folder**. It was tested with Blender 5.2.2 LTS; Blender
4.3+ is the expected API baseline, but other versions were not tested.

The importer creates one normally editable mesh per DX, retains physical draw
membership, source vertex/triangle IDs, and exact source-normal provenance as
mesh attributes, and stores group, texture-slot, material-candidate,
validation, and trailing-layout metadata on the object. Blender preview UVs use
direct source V; this is intentionally independent from the unchanged glTF
`flip-v` policy. Blender-calculated display normals avoid known Blender 5.2.2
native custom-normal crashes while the source values remain preserved. The original-template exporter now patches same-topology positions, source-space normals, UVs, raw vertex colors and selected fixed material-state bytes. E1, E3, E4, and E5 are runtime-confirmed; the stronger R4E.1 N1 resolved the earlier inconclusive E2 normal probe. The environment feature-bit writer and R4F topology writing have runtime confirmation in their tested contexts. See
`docs/blender-importer.md`, `docs/blender-collision.md`, and
`docs/dx-writer.md`.

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

py -3 tools/mrtool.py vehicle-roles `
  "..\Data.sma_unpacked\DataGx\Vehicles" `
  --report research/r4a/vehicle-resource-matrix.json `
  --markdown research/r4a/vehicle-resource-matrix.md `
  --comparison research/r4a/car-vs-complete.md

py -3 tools/mrtool.py scan-collision `
  "..\Data.sma_unpacked\DataGx\Vehicles" `
  --report research/r4b/tag101-corpus.json `
  --markdown research/r4b/tag101-corpus.md

py -3 tools/scanner/validate_collision_writer.py `
  "..\Data.sma_unpacked\DataGx\Vehicles" `
  --json research/r4c/tag101-writer-corpus.json `
  --markdown research/r4c/tag101-writer-corpus.md
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

## MASTER RALLYE VEHICLE SDK v1 — RUNTIME-CONFIRMED BASELINE

R4G adds typed marker-1339 bounds, a conservative out-of-donor-bounds topology path, finite tag101 per-axis collision scale, and a VehicleProject validator/builder with Blender controls. Four isolated Astero candidates (B1 bounds, C1 scale, P1 complete topology, W1 wheel topology) were generated under ignored local output and then tested in-game. B1, C1, P1 and W1 each passed original-game testing. The full existing-donor Vehicle SDK v1 baseline is frozen; see research/r4g/runtime-results.md for the separate human evidence. See docs/vehicle-sdk.md and research/r4g/runtime-test-plan.md. No game asset or Data.sma is committed.

## R-DEMO research branch

Development-era demo asset archaeology is isolated on `research/r-demo-pipeline`. Start with [the pipeline evidence](docs/demo-development-pipeline.md) and [R-DEMO findings](research/r-demo/findings.md). GXI, GXB, GXP, and a conservative GXM prefix reader are documented under `docs/formats/`. First-pass human Trooper 8.4.1 tests confirm live GXM body/presentation/wheel visual roles. R-DEMO2 now confirms byte-exact runtime GXI→DXT regeneration, 9.3.1 GXM→persistent DX and DX-only fallback on tested resources, and a `$chull` edit that crashed both demos. Repeated cooker determinism, DebugView and ProcMon traces remain open; see [R-DEMO2 findings](research/r-demo2/findings.md).
