# Paris-Dakar Pajero Silver #271 — first native pilot

29 October 2026. **PASS: local authoring, deterministic native conversion,
Windows validation and private candidate packaging. D3D8 gameplay NOT TESTED.**
This is an adaptation of the original Paris-Dakar asset, not proof that a missing
Master Rallye prerelease model has been recovered. The owner authorized retail
MR Pajero as the donor. RED, Patrol, Michelin and all accepted projects remain
separate; no fleet or roster-capacity work was started.

## Qualified inputs and implementation

- Original catalog: `Data/PajeroSilver.tc`, SHA256
  `fe5b111f88309fa8167d9df8a996a8d478c912a2a189126d5534bad3f14a82ae`.
- Accepted Universal Vehicle Scene v1: SHA256
  `9d3edfe6b4a5187a44946784c6fb1f836eed1ec311c6f8c42f0bf388108342c9`.
  The scene, manifest and sidecars are copied verbatim into private pilot inputs.
  Its decoder, arrays, node names, transforms, unknowns and source evidence are
  unchanged. Only this exact scene is admitted by the native policy.
- Clean retail `Data.sma`: SHA256
  `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`.
  Every loose donor DX/DXT is compared with the exact SMA member before writing.
- `paris_dakar_silver_pilot.py` is a bounded source policy/orchestrator. Geometry
  uses `universal_scene_bridge.compile_scene`, then the existing scene DX writer,
  native-state authoring, import project, Physics Studio, Workshop and roster
  builder. There is no new TC decoder or independent DX compiler. The existing
  roster helper now takes an explicit runtime family; its 4Runner default stays
  unchanged. Source Garage offers Silver creation only for the qualified catalog;
  final admission additionally checks the entire immutable scene hash.

## Coordinates, stance and physics decisions

Source axes are +X right, +Y up, +Z front. The accepted normalization mirrors Z;
the normalized-to-MR proper Y half-turn yields native +X left, +Y up, +Z front.
The combined source-to-MR mirror reverses triangle winding exactly once; normals
use inverse transpose. Stored UVs and texture rows are preserved.

| Measurement / choice | Value |
| --- | --- |
| Numerical source body width / height / length | 2.07965195 / 1.73084103 / 4.094415 |
| Static axle wheelbase | 2.52778 |
| Front / rear track | 1.622151 / 1.746406 |
| Source Description radius | 0.390497 |
| Source visual radial bound | approximately 0.395454214 |
| Original static attachment Y | 0.58896 |
| Retail MR Pajero wheelbase / track / radius | 2.4 / 1.65 / 0.38 m |
| Retail MR Pajero physics dimensions L/W/H | 3.5 / 2 / 1.5 m |
| Authored common XYZ datum | -0.00113275 / -0.63896 / -0.0044 |
| Native hubs | X = +/- track/2, Y = -0.05, Z = +/-1.26389 |

Numerical scale **1 source unit = 1 MR metre is an explicit MR authoring choice**;
the original game's physical unit convention is not independently proven.
The entire body and all wheel positions receive the same origin rebase, retaining
their relative stance. It maps source attachment Y to native `-RideHeight` while
retaining retail Pajero front/rear RideHeight 0.05. No independent body lowering,
wheel raising, spring change or subtraction of source Rest Position 0.46 occurs.
MR symmetric axles remove only a recorded +/-0.00000025 m lateral residual.
The visual wheel radius exceeds the catalog radius by about 4.96 mm; this remains
visible in measurements, rather than being hidden by an arbitrary wheel scale.

Original `dakar.exe` SHA256
`94008b8708ddaf918397b56c2e194086ed9b088a7ec0e7e185effdebd51d1482`
was examined with REA/Ghidra. At 0x519d30, source suspension parsing adjusts
attachment height and limits using game-option globals; 0x51a160 constructs
original 0/pi side rotations. Static attachment values are therefore not proof
of gravity-settled running-game stance. The complete original suspension solver
and owner runtime options were not recovered in this bounded pilot.

Independent family **PDSilver** clones retail Pajero mass 1500, AWD, engine,
tyres, suspension and damping. Only measured dimensions, wheelbase, tracks and
catalog wheel radii override its base fields. Source mass 2150 and suspension
parameters are retained as provenance, not transferred between unlike solvers.
The existing collision tool affinely fits Pajero hull topology to conservative
opaque body/bonnet/bumper/backdoor bounds. Source crew shares a body draw; this is
not an independently rigged shell selection. Collision and settled stance need
owner driving tests. No speculative moving axles or collision mesh is invented.

## Materials, glass, lamps and original crew

All six used diffuse textures retain **every original RGBA sample**, including
palette alpha, with exact stored rows. Native DXT wrapping is deterministic.
No global alpha flattening, two-sided workaround or environment patch is used.

The source WinONE material (`r0001-mat-06`) has 38 triangles: **0–21 are headlamp
overlays**, 22–29 windshield, 30–33 source negative-X side glass, 34–37 source
positive-X side glass. The headlight overlays retain original alpha blending and
are excluded from glass damage and brakes. Flattening those overlays to opaque
in the first diagnostic build incorrectly hid the headlight artwork; that build
was rejected and corrected before final delivery. Final captures show the
underlying original optics. Native front/left/right intact/broken alternatives
reuse the original paired pane geometry; broken cracks are explicitly MR-authored.
No separately qualified rear pane exists, so rear glass damage is UNSUPPORTED.

The eight original rear lamp triangles (`r0001-mat-01`, LightsOFF) are partitioned
only inside two reviewed red-lens atlas rectangles. Original repeated V coordinates
are retained. Every cut carries barycentric provenance to original triangles;
the clear/orange surfaces stay ordinary. Native brake ON/OFF/glow uses the existing
controller and exact selected lens geometry, without enlarged spill surfaces.

REA material dispatch at 0x4c6e20 and helpers 0x47a900/0x47aab0 distinguish source
blend/test and cull policies. Indexed palette alpha is retained by the source
loader. Exact original thresholds, environment/reflection lighting and complete
render-pass behavior remain unresolved. MR diffuse/blend choices are adaptations,
not exact Paris-Dakar renderer fidelity. Source bump/reflection/animation fields
and original mip resources remain in the immutable source scene.

Original static source crew, cockpit, mirrors, livery, rear trim and equipment
are retained. No second retail crew is added. Independent crew fitment is
UNSUPPORTED because no qualified source rig/rigid-part mapping exists. Bonnet and
door source transforms are preserved in the selected static pose; original source
damage, animated equipment and part-detachment behavior are not claimed.

## Existing MR systems and isolated roster

- Physics/audio donor: original MR **Pajero**, stock audio profile **1**. No
  Paris-Dakar engine audio has been recovered or installed.
- Camera: Gameplay Camera 2.0 original/reset path, without invented source presets.
- Shadow: editable Auto Fit proposal; frontend: existing Auto Frame/presentation.
- Identity: `Paris-Dakar Pajero Silver #271`, Mitsubishi / Pajero Silver, generated
  original-vehicle artwork, editable Results `PAJERO SILVER 271`, silver marker.
- Four wheel resources preserve source side rotations. Proper Y half-turn
  compensation in left templates cancels the native positive-X instance rotation.
  Native rest-pose vertices, normals, UVs and winding reproduce source wheel parts
  within float32 tolerance. Per-slot runtime spin/steer remains an owner test.
- CarID29 is a **private alternative** within the qualified 30 entries. The
  heritage base roster is copied; its project28 stays selected. Trooper, Clio,
  Pajero85, 4Runner and other accepted projects/configurations are not overwritten.
  No capacity increase, unlock/save editing or original installation modification.

The candidate contains 299 sealed resources plus the separately mutable copied
local PlayerState file. Compared with the base runtime: 109 added and five changed
resource files, zero removals or stock model replacements. Changed existing files
are `vehicles.xml`, `Modifications.xml`, VehicleSelect XML, VehicleSelect carsheet
and RaceResults smallcarsheet. Exact before/after sizes and SHA256 values are in
the private conservation report. Generated overlays are scoped by the existing
addon compiler and registry; installed originals remain untouched.

## Validation and private delivery

Evidence root: `.research-output/vehicles/paris-dakar-silver-native/`.
Final project: `silver-final/workshop/workshop-project.json`.
Owner launcher: `silver-final/builds/source-fidelity/candidate/Launch-SDK-Roster.cmd`.
It uses the existing external sealed launcher against the unchanged original EXE.
Silver is registered in the normal private Workshop library without removing
previous entries. Open Source provenance to inspect the immutable scene.

- Focused policy/bridge/aperture/source/admission tests: **50 PASS**.
- Full Windows synthetic suite: **1139 tests, OK, two optional fixture skips**
  (J.1/J.2 private bundle and private final-pass vehicle fixture).
- Local conservation: repeated generic bridge/DX/DXT/state output byte equality;
  all six used RGBA arrays exact; all four native wheel transforms/UVs/winding;
  immutable source reopen; collision fit preserves render arrays/controllers;
  exact resource differences and no stock model replacement.
- Disposable Studio copy: surface edits, collision rebase, exact Undo/Redo/Restore,
  shadow/reset, frontend framing, Results/marker persistence, camera override/reset,
  save/reopen/validate; 67 original author/baseline files unchanged.
- Native launcher verify, environment verify and allocation self-test PASS;
  allocation self-test does **not** execute game code.
- Real Windows Tk Source Garage **Create → open → Validate** and provenance flow
  PASS, including a second independent authoring project, zero callback errors
  and retained Pajero AWD. D3D9 captures include six race and six frontend views, brake ON
  and additional actual GUI-flow wheel interior/exterior diagnostics.
- Protected originals/accepted-output audit checks 7599 files by hash, size and
  mtime. See private `preservation-validation.json` for final result.

The original source preview and neutral native D3D9 views use different model
coordinate frames and camera framing; a visually similar image does not prove
original-game renderer parity. Actual D3D8 spawn, animation, collision, damage,
finish/Results, menu return and re-entry remain **NOT TESTED**. Follow
[the owner checklist](PARIS_DAKAR_SILVER_OWNER_CHECKLIST.md) before acceptance.

## Reproduction

Run from this repository with owner-local input paths. Choose a **fresh** output:

```powershell
python tools/create_paris_dakar_silver_pilot.py `
  --scene .research-output/vehicles/paris-dakar-source/validated/PajeroSilver/scene/scene.json `
  --donor '../corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Pajero' `
  --retail-sma '../corpora/retail/Data.sma' `
  --retail-root '../corpora/retail/Data.sma_unpacked' `
  --base-roster .research-output/vehicles/heritage/roster `
  --output .research-output/vehicles/paris-dakar-silver-native/new-pilot
```

`--author-only` stops before runtime compilation. Conservation utility:
`tools/validate_paris_dakar_silver_pilot.py --pilot <built-pilot> --donor <Pajero> --output <fresh>`.
Studio utility: `tools/validate_source_garage_pilot.py --workshop <pilot/workshop> --output <fresh>`.
Actual creation UI harness: `tools/validate_universal_workshop_windows.py` with the
same scene/donor/retail/roster paths plus `--viewer <native-viewer> --output <fresh>`.

Source-only review archives are produced from the validated local commit, excluding
all donor geometry, textures, sounds, scenes, screenshots, executables and REA
scratch exports. Both full and changed-file archives retain the complete Master
Plan and exact v7.1 attachment. No push, publication or further importer work.
