# Paris-Dakar Source Lab — recovered original vehicles

29 October2026. Started from clean `research/vehicles` at
`ec8779615d7eb5f9ad653b7badaa4e9209450782`. The actual4Runner stabilization
is present: five rejected visual flags fail before source/output IO, Stable
keeps the accepted fixed-final assembly. No4Runner/accepted project was edited.
The retained complete Master Planv7.0 remains an exact canonical prefix.

## Result

Both original Pajeros and one unrelated **Nissan Patrol** now reconstruct into
Universal Vehicle Scenev1 and render through the existing D3D9 source preview.
This is actual original geometry and texture extraction, not image tracing or
MR-native authoring. Stable resource IDs, original byte snapshots, per-material
batch spans, texture samples/palettes/mips and component placement records are
preserved in private scene projects.

| Source | TC records / Gex / images | MainBody triangles | Retained unique resources: vertices / triangles | Selected assembled draws |
|---|---:|---:|---:|---:|
|PajeroRED.tc|65 /8 /56|1376|3415 /1956|25|
|PajeroSilver.tc|65 /8 /56|1446|3454 /2002|25|
|NissanPatrol.tc|72 /11 /60|1562|3622 /2074|26|

Retained totals include separate shadow meshes and count shared wheel geometry
once. Visible assemblies instance wheels four times. Body/part resource names
and original IDs remain inspectable; material splitting is derived grouping,
not a claim about original scene parent nodes.

**L0 PASS:** original archive and reliable resource ranges. **L1 PASS** for the
qualified Gex/PC TIM structures and source assembly references; suspension pose
and material interpretation retain explicit warnings. **L2 WARN:** actual
textured neutral D3D9 geometry was visually inspected in multiple views;
this does not establish original renderer parity. **Gameplay NOT TESTED** and
outside scope. Eight original Patrol triangles have normal/winding disagreement;
no automatic repair was made.

## Original files and scope

Read-only root: `E:/RallyWorkshop_Sources/sources/Paris-Dakar Rally`.
Windows x86; exact commercial edition/region are not independently authenticated.
The existing corpus readme date/build observations remain context, not a new
version claim. Only the three selected vehicle containers were decoded, not a
fleet. Prior corpus inventory records222 TC files and surrounding audio/front
resources; the current reader does not claim support for all222.

| Original relative path | Bytes | SHA256 |
|---|---:|---|
|dakar.exe|1925177|94008b8708ddaf918397b56c2e194086ed9b088a7ec0e7e185effdebd51d1482|
|Data/PajeroRED.tc|4187796|38b1d5ba438b3b384e029ab4feb395907ea7f6436e27dc40efa0ed0e53964d7d|
|Data/PajeroSilver.tc|4187796|fe5b111f88309fa8167d9df8a996a8d478c912a2a189126d5534bad3f14a82ae|
|Data/NissanPatrol.tc|4577696|acdb8fc6ae19e6c4dce83e60b35bc86885389f4d3cf89812dce609c40801b765|

[Machine-readable manifest](PARIS_DAKAR_SOURCE_MANIFEST.json) includes every
selected resource name, exact original hash/size/offset, source measurements
and generated scene/manifest hashes. Complete original TC/header/table bytes
stay private. Source filenames alone do not establish V60/V20 identity.

## Measured source assembly

Dimensions below are numerical **source units**, not independently verified
factory metres. Width includes source geometry; bounds use the static attach
pose with original separate-part translations.

| Measurement | RED | Silver | Patrol |
|---|---:|---:|---:|
|Width x height x length|2.145238 x1.681265 x4.094411|2.079652 x1.730841 x4.094415|2.120380 x1.714721 x4.515188|
|Attach wheelbase|2.527780|2.527780|2.973600|
|Front / rear track|1.622151 /1.746405|1.622151 /1.746406|1.646320 /1.677183|
|Original suspension radius|0.390497|0.390497|0.408248|
|Maximum wheel geometric radius around local X|0.395455|0.395454|0.413431|
|Original Rest Position|0.46|0.46|0.46|

Wheel geometry and physics radius are distinct original values. Four source
attachment positions, side rotations and original limits are preserved; no
visual body lowering, guessed wheel movement or MR physics adaptation occurs.
The original constructor changes suspension using game options; gravity-settled
runtime placement is **NOT TESTED**. Detached-part damage animation, collision
solver, shadow projection, livery/damage transitions, frontend substitutions
and lamp activation are retained metadata or unresolved behavior, not invented
working systems. The selected containers contain no separately identified
LOD/frontend mesh records; absence of such records here is not whole-game proof.

## Preview, UI and reproducibility

Final private evidence:
`.research-output/vehicles/paris-dakar-source/validated/`.
Each vehicle has `scene/scene.json`, full private resources, deterministic
`repeat/`, six `views-source/` and six `views-normalized/` images. The same
project opens with **Workshop → Source Garage → Reopen source scene**.
Coordinates, material diagnostics, texture provenance and component isolation
reuse the existing workspace. Evo2-only wheel-detail controls are disabled for
these scenes; native4Runner creation is gated off. No new MR bridge/compiler.

The source renderer's default no-cull inspection exposed internal backfaces
and caused misleading overlaps/black interior panels in initial diagnostics.
Final captures use explicit **CW culling** with original source triangles.
Paired CW/CCW diagnostics confirm exterior versus interior; no polygons were
deleted or normals guessed to hide the issue. Existing Evo2 default behavior
is unchanged. Specular/reflection shaders and dynamic lamp/alpha behavior are
not simulated. All original color/alpha samples remain immutable.

Reproduce one qualified scene and12 fixed views from the actual installation:

```powershell
python tools/paris_dakar_source_lab.py --source-root 'E:/RallyWorkshop_Sources/sources/Paris-Dakar Rally' --catalog PajeroSilver.tc --output '.research-output/vehicles/paris-dakar-source/owner-silver' --viewer '.research-output/rally-workshop/bin/mr-vehicle-previewer.exe'
```

Source-qualified three-vehicle validation, complete repeated generation,
source/normalized round-trip, material/part diagnostics and actual Tk opening:

```powershell
python tools/validate_paris_dakar_source.py --source-root 'E:/RallyWorkshop_Sources/sources/Paris-Dakar Rally' --output '.research-output/vehicles/paris-dakar-source/owner-validation' --viewer '.research-output/rally-workshop/bin/mr-vehicle-previewer.exe' --tk
```

Outputs must be fresh and outside original source/tool trees; hashes and
reparse/path-containment checks fail closed. Aggregate geometry, image, JSON
and sidecar budgets reuse the existing UVS validator. No untrusted game/tool
binary was executed. Only the known local previewer and Workshop were run.

## Validation and preservation

13 Paris-Dakar and12 Michelin focused synthetic tests pass. Actual source
validation separately checks three complete resource sets, exact triangle
goldens, original palette channels/mips, complete span consumption, deterministic
scene manifests, source/normalized positions and real Windows Tk/D3D9.
36 final GPU views plus three real Workshop screenshots were produced;
diagnostics additionally cover opposite culling, material IDs and isolation.
Synthetic tests are not substituted for actual proprietary-source results.

The complete available Windows suite passes1132 tests with2 pre-existing
optional-fixture skips. No new D3D8 gameplay test is implied.4610 prior protected
source/accepted files retain SHA256, size and mtime; original EXE, clean retail
Data.sma and installed proxy remain unchanged. Current proxy SHA256 is
`339174529605b6b4602715470ac67e0bf39d7f95197b0d07fe2dbd048a960ea1`.
Private original donor hashes/sizes/mtimes also remain exact.

## Historical result and next review gate

[Historical comparison](PARIS_DAKAR_PAJERO_COMPARISON.md) uses actual owner-local
MR images and original frontend artwork. Silver has a strong frontal visual
relationship to `mr4_paj.jpg`; exact shared geometry/pipeline, V60/V20 labels
and capture build remain **UNRESOLVED**. No texture identity was established.
[TC format](PARIS_DAKAR_TC_FORMAT.md) separates bytes, native static evidence,
interpreted coordinates and unresolved runtime behavior.

[Michelin report](MICHELIN_SOURCE_REPORT.md):38 decoded files, eight structural
XOBJs and20 original indexed TGAs. Wheel placement/assembly and alternate vertex
streams remain unresolved; no completed Michelin vehicle preview is claimed.

**Recommended next reviewed target: PajeroSilver.** Original geometry, palette
textures, UVs and source assembly are available, and it has the strongest
historical visual lead. Before any MR import, separately qualify source material
dispatch and runtime wheel pose/options, choose a documented MR authoring policy
and review owner source views. RED is also structurally recovered; Patrol only
validates generalization. Stop here: no CarID, native build, capacity experiment,
fleet, donor installation, push or publication.
