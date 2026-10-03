# Master Rallye RE

Clean-room interoperability and preservation research for *Master Rallye* (2001).

The repository contains only tools, documentation, machine-readable forensic
metadata, and synthetic test data. Original game resources remain external and
read-only.

## Current scope

Optional R5V-A vehicle-slot archaeology maps the final EXE registry and two PC demos without patching the game. The final build has 25 explicitly named vehicle IDs (0-24) in a fixed 26-record heap array; the trailing record and extra-slot safety remain unresolved. Forklift has assets and localized text but no initialized registry entry or physics block. See `research/r5v_a/findings.md` and `research/r5v_a/vehicle-slot-feasibility.md`.

Phase R4G hardens the runtime-confirmed R4F topology writer into a vehicle project workflow. Earlier R4C work established: the validated vehicle DX/DXT library drives a native
Blender add-on with single-resource and vehicle-folder import, editable meshes,
preview materials, preserved draw/group/source metadata, and a fail-closed
same-topology **positions-only** DX export. All 78 vehicle resources produce a
byte-identical zero-edit result and pass an in-memory single-position patch.
On 2026-09-22, human testing in the original game runtime confirmed visible,
artifact-free same-topology position edits in `complete.dx` (presentation/menu)
and `car.dx` (race). General DX serialization remains out of scope; R5T-A adds
a separate read-only course research and import path, summarized below.

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

Phase R4D.1 traced the serialized DX draw through its material loader to Direct3D 8: the draw mask copies to runtime +0x34; flag bytes 0/1 select alpha blend/test; the base and environment shaders expose concrete render and texture-stage states. Its M1/M3 reflection, M2 glass source-alpha and M4 active brake-glow human results retain their tested scope; see research/r4d_1/runtime-results.md.

R-MAT1 closes the observed vehicle material runtime model with non-blocking
unknowns: exact slot0/stage0 and slot1/stage1 bindings, no NULL-slot promotion,
byte2 diffuse and byte3 UV gates, all stock feature bits and the transparent
queue's bound-depth sort key. Blender Preview V3 uses generic slot1 semantics
with explicit approximation limits; 1478/1478 draws classify and 78/78 loaded
Blender zero-edit exports are byte-identical. No new runtime result or material
writer capability is claimed. See [research/r-mat1/findings.md](research/r-mat1/findings.md)
and [docs/vehicle-materials.md](docs/vehicle-materials.md).

Phase R4E adds same-topology attribute authoring, same-size DXT replacement, exact
vehicle texture-user manifests, staging, and ZIP-compatible SMA helpers. Human testing confirms E1 UV, E3 vertex color, E4 alpha flag, and E5 full-tree Python Data.sma packing. E2 normal was inconclusive; stronger R4E.1 N1 and M1 human tests confirmed normal and environment-feature writing. The SAME-TOPOLOGY VEHICLE SDK V1 BASELINE is now frozen. See
`docs/vehicle-authoring.md`, `docs/texture-authoring.md`, and
`docs/vehicle-packaging.md`.

Phase R4F reconstructs existing-draw render topology while preserving material identities and collision bytes. The protected 78-file vehicle corpus rebuilds byte-identically at zero edit; the Astero +3-vertex/+1-triangle F1 candidate is **CONFIRMED_BY_RUNTIME**: its new triangle is visible and collision, damage, glass, wheels and general vehicle function remain normal. The old same-topology patch exporter remains the frozen SDK v1 path. See `docs/topology-authoring.md`, `docs/dx-render-rebuilder.md`, and `research/r4f/findings.md`.

## Course resources and RaceTest authoring (G0)

The Vehicle SDK v1 baseline remains frozen. The read-only revision-135 course
DX parser and Italy1/France1 Blender imports remain validated. R5T-C confirms
that moving the old GXM `startpoint` candidate changes tag100 deterministically,
but its +3 translation did not change the visible grid. Cross-runtime controls
separate runtime participant ordering from physical slot geometry.

R5T-D.0 runtime edits confirm that France1 `MarkerLists/StartArea` controls
physical grid translation, orientation, spacing, and heading; `FinishArea`
contributes to race completion. R5T-D.1 closes the France1 SplitTime0 center:
its main Egg `en3d Matrix` Row3 drives both the yellow sign and gameplay
trigger center, while `gaRaceSplitTimeAI/Radius` defines a 3D spherical
proximity test. The executable reads center XYZ through
`[context+0x50]+0x4C/+0x50/+0x54`; baseline and moved-position debugger captures
match the Egg Row3, and a separate on-road edit triggered early at its new
position. Per-car one-shot state explains the earlier StartArea false negative:
all four cars had already activated the moved sphere during race startup.
`SplitTimeN-0..3` remain separate visual checkpoint objects; ExtraTime's exact
meaning is unknown. The initializer derives a RaceLine percentage from the
split center, not the reverse. `src/master_rallye/course_sdk.py` now composes
render DX, semantic RaceTest logic, HNT dependencies, structural SFL, and
optional TXT/GXM source metadata without replacing the forensic parsers. The
existing Blender add-on consumes this model and displays the split trigger as
a wire sphere driven by its explicit Radius property, while keeping visual
checkpoint companions separate. Course tag100 is surfaced as a neutral opaque
region with unknown semantics. `$bsp -> tag100` and tag100 physical meaning
remain unknown. See
[`docs/course-sdk.md`](docs/course-sdk.md), `research/r5t_d1/`, and
`docs/course-importer.md`.

G0 adds bounded RaceTest authoring; human runtime testing through Blender
export passed for StartArea, FinishArea, and the SplitTime0 trigger center.
Combined StartArea + FinishArea editing loaded normally. G0.1 adds exact
SplitTime visual-companion Row3 editing, a translation-only checkpoint group,
semantic manifest roles, int32 ID bounds, quieter area transforms, and a
Blender 5.2 panel-draw smoke that validates icons against Blender RNA. Retail
validation remains 36/36 byte-identical no-op XML files, 110 main split
records, and 440/440 visual-companion positions supported. The two 5-marker
FinishAreas remain read-only. **G0: PASS — RUNTIME AUTHORING CONFIRMED.**
**G0.1: PASS — BLENDER/CORPUS VALIDATED.** Visual-companion XML edits have not
been separately runtime-tested. No course geometry/physical writer or EXE
patch exists. See
[`docs/course-race-logic-authoring.md`](docs/course-race-logic-authoring.md),
[`research/g0/runtime-results.md`](research/g0/runtime-results.md), and
[`research/course_marker_backlog.md`](research/course_marker_backlog.md).

See
[`docs/course-assets.md`](docs/course-assets.md),
[`docs/course-importer.md`](docs/course-importer.md),
[`research/r5t_b1/findings.md`](research/r5t_b1/findings.md),
[`research/r5t_c/findings.md`](research/r5t_c/findings.md), and
[`research/r5t_c/whole-x3-closeout.md`](research/r5t_c/whole-x3-closeout.md).

R5T-E.1 closes read-only version-7 GXM topology: the Demo 9.3.1 loader's
52-byte triangle grammar is implemented and cross-validated on France1,
Italy1, Boinds, and Demo 9.10 AI Track. France1's source `startpoint` resolves
to a closed 12-triangle box. The Course SDK now exposes literal source meshes
and position bounds without assigning gameplay semantics to node names. No
course writer or standard Blender importer change was added. See
[`docs/formats/gxm-course.md`](docs/formats/gxm-course.md) and
[`research/r5t_e/findings.md`](research/r5t_e/findings.md).

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
legacy glTF material preview uses the first non-`Null` texture only; all original ordered
slots and candidates remain metadata.
Vehicle Blender Preview V3 uses fixed runtime slot semantics instead; see
`docs/blender-materials.md`.

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

## R5V-B dormant retail vehicle slot audit

Targeted Ghidra analysis found that retail record 25 is allocated but its ID, class and stat integers are unwritten; the class-2 vehicle selector has an independent hardcoded limit of 11. `Frontend/VehicleSelect/VehicleList` is the class-label list, not a dynamic car registry. A case-25 unlock branch exists, but resource/physics and quick-race safety remain unproved. No patch or runtime candidate was produced; see `research/r5v_b/findings.md`.

## R5V-C duplicate-Astero ID25 runtime proof

A hash-locked patcher now creates an ignored retail EXE copy that initializes the allocated ID25 through the original owned-string initializer, raises class-2 navigation capacity to 12 and overrides only ID25's locked flag for testing. Automated PE, instruction, byte-diff and synthetic checks pass. **RUNTIME VALIDATION: WAITING FOR HUMAN P0** (menu/preview only); P1 Quick Race is gated on the owner's P0 report. No game assets or original EXE were changed. See research/r5v_c/findings.md and research/r5v_c/runtime-test-plan.md.
