# Evo2 Toyota 4Runner — qualified source scene pilot

28 October 2026. Branch `research/vehicles`; parent
`f2714b1d50c5af18bdc4081010317fe3e4632922`. The owner accepted Source Garage
phase 1 and authorized this one adapter. This checkpoint supersedes the audit's
historical implementation stop gate for this vehicle only.

**Implemented:** read-only POD2/SMF/TRK/classic-TIFF source adapter, versioned
Universal Vehicle Scene, assembled original body/four original wheels and real
Workshop Tk/D3D9 preview. **L0 PASS; L1 WARN; L2 WARN (assembled textured preview
inspected); original-game rendering and MR gameplay NOT TESTED.** Unknown source
semantics remain in the scene and UI. No MR compilation or roster work begins.

## Exact qualified selection

Local source root: `E:/RallyWorkshop_Sources/sources/4x4 Evo 2`.
Catalog: **TRUCK/T4RSR52.TRK**, Toyota 4Runner SR5 Sport Package 2WD, 2000.
The installed executable/hooks are not evidence of pristine publisher assets.
Only this exact hash set is admitted; another installation requires separate
qualification rather than silently accepting a similar filename.

| Resource | Bytes | SHA256 |
|---|---:|---|
| `4x42.exe` | 2776064 | `ab8286e6bce8a1bf3769acddfeb0a79df2e5d43c72f462a89aa90f477951ec75` |
| `TRUCK.POD` | 144691121 | `5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41` |
| `TRUCK/T4RSR52.TRK` | 6674 | `d2ff6c5914e8102116e56704dac800442fed3adfbf42326c6b3311517e8bbcb4` |
| `MODELS/4RUNNERSR5.SMF` | 171308 | `a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e` |

Every selected member also records POD offset, size, SHA256, original snapshot
path and stored checksum (checksum semantics NOT TESTED). There are 22 original
member snapshots, 14 textures including bump maps, 43 meshes, 38 scene nodes,
2701 unique stored vertices and 2773 triangles. Body: 33 named objects,
2089 vertices/1967 triangles. No donor binary is committed or packaged.

## Assembly and measurements

The original SMF grammar is flat; it provides no recovered parent matrices.
Object order/names, source-visible values and geometry are preserved. The body
root is explicitly derived. No invented skeleton is presented as source data.
Native stock BODY-mask evidence selects 11 body parts at body detail 2:
Body, Cockpit, GlassI, GlassE, MirrorL, MirrorR, RfRack, UndBody, WiperLT,
WiperRR and WiperRT. Optional parts remain stored and inspectable. Axler/Light*
have separate unqualified auxiliary passes; displaying every stored object
together is a diagnostic, not an original complete equipment configuration.

All six `MODELS/4RUNTIRE{08,12,16}{L,R}.SMF` resources are retained. These are
native detail slots, not wheel diameters. Native loader/index evidence selects
distinct L/R geometry, without a guessed half-turn or MR wheel replacement.
Default inspection detail 16 uses 162 vertices/227 triangles per side; detail
12 uses 110/144 and detail 08 uses 34/32. All share an approximately 1.27526 ft
outer radius and 0.869422 ft width. Four instances reuse these original meshes.

| Wheel record | Original X/Y/Z (ft) | Normalized X/Y/Z (m) |
|---|---|---|
| `faxle.rtire.static_bpos` | 2.47, -0.6, 4.79 | 0.752856, -0.182880, -1.459992 |
| `faxle.ltire.static_bpos` | -2.47, -0.6, 4.79 | -0.752856, -0.182880, -1.459992 |
| `raxle.rtire.static_bpos` | 2.455, -0.6, -4.09 | 0.748284, -0.182880, 1.246632 |
| `raxle.ltire.static_bpos` | -2.455, -0.6, -4.09 | -0.748284, -0.182880, 1.246632 |

Front track: 4.94 ft / 1.505712 m; rear: 4.91 ft / 1.496568 m. Static hub
wheelbase is **8.88 ft / 2.706624 m**, while catalog wheelbase is **8.78 ft /
2.676144 m**. The 0.1 ft discrepancy is preserved and reported, not corrected.

Independent original TRK labels, light headings, anatomical mesh extents and
exact-build native wheel code establish the static interpretation: X right,
Y up, Z front, feet; anatomically left-handed. Normalized frame is right-handed,
Y up, front -Z, metres: `diag(0.3048, 0.3048, -0.3048, 1)`. Original vertices,
normals, UVs and triangle indices are unchanged. Reflected-basis winding changes
exist only in disposable preview draws. Ten existing body triangle/normal sign
inconsistencies are retained. Scene normalization/inverse error is below
`8.9e-16` source units; float32 D3D9 staging error is below `1.78e-7` m.

This is the native high-body-detail, zero-steering/spin/axle-angle inspection
pose using literal static_bpos translations. The visible high stance is not
qualified as gravity-settled suspension in the running game. The native 1.05
field is used in a low-body-detail axle branch, not a general scaling factor.
See [original evidence and addresses](EVO2_SOURCE_SEMANTICS.md). Community
Blender axis/scale choices were leads, not the proof for this interpretation.

## TIFF, materials and source rendering boundaries

The body TIFF retains both 8-bit stored samples, its complete original TIFF
and original 16-bit palette. ExtraSamples=0 means **unspecified**, not alpha.
The old audit's Pillow-derived opaque RGBA did not expose that second channel;
the historical smoke report now has an explicit erratum. The bounded first-IFD
decoder also preserves the bump texture's four channels and reports malformed
next-IFD pointers rather than walking them. Every raw sample/palette sidecar
has a size/hash bound to its original resource and manifest.

Neutral preview uses palette/RGB diffuse and default opaque coverage. Raw
transparent/reflective fields, material strings and bump references survive.
Glass opacity 0.35 is available as an explicitly interpreted comparison;
material-ID colors and source-visible/all-object diagnostics are separate
choices. None changes the original scene. Reflections, bump shading, native
lighting, source alpha policy, nine catalog color transforms, animations,
dynamic axle/lamp/damage passes and settled suspension remain unresolved or
unsupported. A texture-mapped D3D9 image does not establish original renderer
fidelity. No original Evo2 executable was executed.

## Use in Rally Workshop

Run `.research-output/rally-workshop/Launch-Rally-Workshop.cmd`, open **Source
Garage**, select the existing source root, then **Inspect / Create source
scene**. The target catalog is fixed to the qualified 4Runner. Reopen also
accepts the private scene below. The window provides a body/wheel object tree,
original/normalized coordinates, measurements, source visibility, wheel detail,
material diagnostics, interactive native 3D and six fixed orthographic views.
It does not select or mutate an MR authoring project. Preview choices persist
separately from the immutable neutral scene.

Reproducible CLI, from the repository with installed Python:

```powershell
python tools/evo2_source_scene.py inspect --source-root 'E:/RallyWorkshop_Sources/sources/4x4 Evo 2'
python tools/evo2_source_scene.py create --source-root 'E:/RallyWorkshop_Sources/sources/4x4 Evo 2' --output 'E:/RallyWorkshop_Sources/research/my-new-4runner-scene'
python tools/evo2_source_scene.py validate --scene 'E:/RallyWorkshop_Sources/research/evo2-pilot-20261028/scene-final/scene.json'
python tools/evo2_source_scene.py preview --scene 'E:/RallyWorkshop_Sources/research/evo2-pilot-20261028/scene-final/scene.json' --output 'E:/RallyWorkshop_Sources/research/my-new-4runner-preview' --capture-views
```

Choose fresh output directories. Source root/configured donor roots, tools,
linked/reparse paths, aliases, traversal and existing output are rejected.
`create --config PATH` can use an explicit external roots configuration; no
large donor installation needs copying. Existing default root configuration is
`research/vehicles/source-garage/roots.example.json`.

## Deterministic private deliverable and actual Windows evidence

Private scene:
`E:/RallyWorkshop_Sources/research/evo2-pilot-20261028/scene-final/scene.json`.
Independent `scene-final-repeat` generation matches all **59 files byte for
byte**, total 7822135 bytes. These private files contain donor assets and must
not be added to distributable archives.

- Scene SHA256: `246cae8bbe646640b50b0a9e228a2f0c7ec49e13c7d13837ba756cb68d05ad3d`.
- Manifest SHA256: `403e00e62c80d932998a92dde59f55abebbf326fc999e6c754a430a25dfd2844`.
- Scene metadata pins all three parser/scene implementation files. The manifest
  binds the scene and every non-manifest file without circular self-hashing.

Private evidence under `.research-output/vehicles/source-garage-evo2/`:

| Evidence | Result / limit |
|---|---|
| `focused-final.log` | 40 new focused tests PASS: corruption, missing resources, geometry/UV bounds, transforms, TIFF channels, allocation/output limits, immutability, determinism, paths, unknown semantics and reopen |
| `full-regression-final.log` | 1057 tests in 62.698s PASS, 2 existing optional private-fixture skips |
| `workshop-build.log` | Native D3D9 viewer and Workshop packaging PASS |
| `old-viewer-regression/validation.json` | Existing MR viewer GPU handedness, culling, texture-row and transparency/depth smoke PASS; no gameplay claim |
| `windows-delivery/validation.json` | Actual Tk Inspect/Create/Capture/Reopen PASS, 19 draws, 41 tree rows; original neutral input unchanged; MR app.project remains None |
| `windows-delivery/six-views/` | Front, rear, left, right, top, isometric D3D9 PNGs; source-basis and explicit-glass comparison folders alongside |
| `windows-delivery/source-garage-ui.png` | Real Workshop window and textured assembled preview |
| `determinism-final.json` | 59/59 files byte-identical across independent outputs |
| `preservation-final.json` | 2432/2432 original-MR/accepted-project files identical; donor POD/EXE hashes unchanged |
| `review/archive-manifest.json` | Post-commit source-only/changed-file archive revision, sizes, hashes and member verification |

Default 16-wheel preview uses 648 instanced wheel vertices; switching to original
08 uses 136. Material opacity interpretation leaves geometry unchanged. Viewer
binary SHA256: `ef27c2a89060eac16b22c7f96127fb2b37792c8e3e7b2edf0629affa234e7c53`.
Final front/rear/side/top/isometric captures were visually inspected, with the
static-pose and material limits above. GPU evidence qualifies this neutral
assembly preview only.

## Preservation, code provenance and review stop

POD/SMF parsing promotes our repository's prior bounded research implementation;
TRK/TIFF/UVS and preview integration are authored here. No third-party
implementation is vendored. Prior community tool/license findings remain in
DONOR_TOOL_AUDIT.md; no legacy binary was blindly executed. Existing GT/Heritage
conversion logic is reused only through the existing viewer boundary, not
replaced. The adapter has no MR CarID, physics, audio, camera, roster or compiler.

The complete v6.7 attachment and all repository-only history are retained;
v6.3–v6.5 are restored in full. See
[Master Plan reconciliation](MASTER_PLAN_RECONCILIATION.md). The attached text
is documentary input; the current owner's bounded pilot request controls scope.

Paris-Dakar PajeroRED/PajeroSilver identifiers and Michelin RAV4 ID25 /
Car25A.PDO, Megane F2 ID6 / Car06A.PDO remain high-priority research tracks.
Pajero identity/shared-MR provenance and Michelin inner geometry remain unproven.
No parallel format campaign was started. Accepted Lancer, Subaru, Pajero,
Trooper/Heritage and Clio projects, isolated CarID29 alternatives, the 30-entry
roster boundary and original MR files are preserved. No push/publication/release.
**Stop here for review before any MR conversion or additional donor adapter.**


## Later hardening checkpoint — 30 October2026

Original pilot results above remain historical. The common UVS contract now validates raw streams, colors and optional secondary UV data; the shared bridge has explicit loss policies and bounded semantic ownership/partition operations. Evo2's accepted native source-baseline resources reproduce exactly. Original TIFF secondary-sample, shader/color output, auxiliary dynamic passes and settlement limitations remain visible; no accepted4Runner change. Current outcomes and native/reference boundaries: SOURCE_GARAGE_QUALIFICATION_MATRIX.md.
