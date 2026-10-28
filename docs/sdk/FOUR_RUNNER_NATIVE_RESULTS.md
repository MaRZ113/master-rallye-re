Current owner review: optional Visual Polish kit rejected in D3D8. Stable preserves accepted glass/lower lamps; new candidates await owner testing. This report is historical. See FOUR_RUNNER_STABILIZATION_RESULTS.md.

---

Owner update: previous pilot now confirms D3D8 loads/drives/body deformation/breakable glass. New visual variants and finish/re-entry remain pending. See FOUR_RUNNER_VISUAL_POLISH_RESULTS.md.

---

# Toyota 4Runner — first Universal Scene to MR pilot

28 October 2026. `research/vehicles`, parent
`c5bd91fc5dcb81e6e10c44ebbd9c0a6073b129ed`.
**One Source Fidelity addon and an isolated owner-testable native candidate are
implemented. D3D8 gameplay is NOT TESTED / PENDING OWNER.** No fleet, Classic
4Runner, other donor adapter, Blender Bridge or roster expansion is included.

## Inputs, source preservation and bridge

The accepted source adapter and Universal Vehicle Scene v1 are unchanged.
Qualified catalog: `TRUCK/T4RSR52.TRK`, Toyota 4Runner SR5 Sport Package 2WD
(2000), body `MODELS/4RUNNERSR5.SMF`. Original private scene:
`E:/RallyWorkshop_Sources/research/evo2-pilot-20261028/scene-final/scene.json`,
SHA256 `246cae8bbe646640b50b0a9e228a2f0c7ec49e13c7d13837ba756cb68d05ad3d`.
Manifest SHA256:
`403e00e62c80d932998a92dde59f55abebbf326fc999e6c754a430a25dfd2844`.
Exact source POD/EXE/catalog/body identities remain those recorded in
[EVO2_SOURCE_ADAPTER_RESULTS.md](EVO2_SOURCE_ADAPTER_RESULTS.md).

The pilot copies the manifest-bound 59-file neutral project into its private
inputs without re-parsing screenshots or inventing OBJ geometry. Original
object/material IDs, flat source order, all six L/R wheel-detail resources,
four hub records, original TIFF samples/palettes and unresolved fields survive.
Only the selected stock body configuration and wheel detail16 are converted;
retained optional equipment/other wheel details are not silently deleted from
the source or represented as qualified MR runtime LOD switching.

`universal_scene_bridge.compile_scene(scene_path, profile, references=None)`
is independent of Evo2, CarID, physics, sound and roster allocation. Profile
schema: `universal-scene-mr-profile/1`. Explicit scene hash, body node IDs,
wheel node slots, basis/authoring transforms, texture-row/UV policies and
material decisions are required. It composes parents, normalizes separately,
uses inverse-transpose normals and determinant-aware winding, retains stable
source-to-draw/vertex/triangle/material maps and records inverse transforms.
Unknown semantics never select geometry edits or material roles automatically.

The result contains body, complete, canonical wheel and all per-slot original
wheel SceneParts, bounded native textures and a provenance report. The existing
`scene_dx_writer`, native-state authoring, crew fitment, addon import/project
compiler and roster builder perform native serialization/integration. There
is no second Evo2 DX compiler. `source_garage_pilot.create_pilot` orchestrates
the one qualified vehicle/profile; another source can reuse the generic bridge
with its own separately reviewed material/fit profile.

Private `source-baseline/assets` contains ten deterministic diffuse-only MR
resources before MR enhancements. It is a separate immutable reference, not
the source game renderer. Workshop verifies its exact file set and hashes,
the neutral scene/manifest/sidecars, the conversion report, author inputs and
the normal immutable editable-project baseline. Edits operate on private
working resources; Undo/Redo/Restore never overwrite either source baseline.

## Stance, axes and native wheel assembly

See [measured decisions](FOUR_RUNNER_STANCE_AND_MATERIAL_DECISIONS.md).
Original source X is anatomical right, Y up, Z front, feet. Exact clean retail
MR screenleft/screenright labels independently show MR X is anatomical left;
MR front is +Z. Normalized UVS to MR is the proper Y half-turn `(-x,y,-z)`.
Raw source to MR is `(-x,y,z)*0.3048`, followed by one documented **whole
assembly Z translation of -0.10668 m**. Body and hubs share this reversible
datum. There is no vertical body shift, raised hub or global1.05 multiplier.

| Measurement | Preserved source / explicit MR adaptation |
|---|---|
| Static axle spacing | 2.706624 m (8.88 ft), distinct from catalog2.676144 m (8.78 ft) |
| Front / rear track | 1.505712 / 1.496568 m |
| Source wheel outer radius | approximately0.388704 m; tyre side-specific original geometry retained |
| MR source hub Y | -0.18288 m; per-family native ride reference+0.18288, donor menu/base ride setting retained |
| Selected body render bounds | X approximately[-0.915811,+0.915811], Y[0,1.428604], Z[-2.435352,+2.221992] m |
| Selected roof-to-hub distance | 1.611484 m versus retail Terrano1.605954 m; no evidence for visual lowering |
| Body-only SourceBaseline | 1098 used vertices,11 draws,1128 triangles |
| Complete SourceBaseline | 1746 vertices,19 draws,2036 triangles including four original wheel instances |

The stock class comparison covers five clean original SUV model triplets and
six physics families. Terrano is the closest conservative narrow-track SUV
donor among these references. Source static hub positions are not recovered
Evo2 gravity settlement; MR reference attachments and contact dynamics remain
different evidence levels. A bounded local owner screenshot search found no
qualified original Evo2 running-game reference to settle that question.

One shared rolling-wheel resource cannot preserve the original left/right
textures:11997/16384 source RGBA pixels differ. The small geometric discrepancy
under a proper half-turn is below0.53 micrometres, but no geometry/texture
equivalence is silently assumed. Four `wheel-source0..3.dx` resources in native
front-left/front-right/rear-left/rear-right order retain each original side.
Positive-X instances use the inverse proper native Y half-turn in their local
resource, not a negative-scale mirror. Actual serialized rest geometry agrees
with the source bridge within1.60e-8 m; normals within3.85e-8 and UVs within
3.94e-8. Textures, vertex colors and oriented triangle order match.

The optional, exact-retail `vehicle_wheels_native` selector changes the model
key on each existing native wheel entity before original registration. It
retains native steering/spin interpolators and ownership/destruction, adds no
auxiliary wheel entity and does not render duplicate non-spinning wheels.
Family/index/key guards and four sealed resource hashes are required. Existing
Lancer mechanics are preserved through a byte-verified delegate chain; the
single callsite has one final patch operation. Original EXE bytes stay on disk.

Original x86 setter, registration, spin-controller constructor and lifecycle
code executed in a controlled CPU harness:16 replacement cases across two
cycles, standalone and mechanics-composed routes, plus allocation failures.
The pre-existing mechanics replay also passed through the composed chain.
This qualifies the bounded code route and ABI, **not** real D3D8 asset loading,
animated wheel appearance or repeated gameplay races.

## MR materials and systems

| System | Implemented choice / qualification boundary |
|---|---|
| Body, plastic, decals, accessories | Original diffuse RGB/UVs and ordinary opaque MR culling; roof rack retained. No global two-sided rendering or transparency workaround |
| Tyres/rims | Original side-specific geometry/textures, opaque materials and visible original inner faces; no MR wheel substitution |
| Windows | Only explicitly selected front/side pane triangles use authored vertex alpha89/255; GlassI/E roof/headliner/lower-door geometry remains opaque |
| Glass damage | Qualified MR front/left/right native cases with separately authored crack texture/planar broken UVs. Rear damage UNSUPPORTED: no separate rear pane is qualified in GlassI/E; Body atlas geometry needs further review |
| Rear brake illumination | Six Body triangles177,178,179,323,324,325 matched to exact source auxiliary rear-lens footprint and red UVs; native OFF/ON plus same-lens glow. Front lamps, tyres and other body surfaces excluded |
| Headlamps/mirrors | Source diffuse presentation retained. No unsupported source lamp animation, headlight effect or mirror reflection invented |
| Reflections/bump/extra TIFF sample | Original resources retained; source semantics unresolved. Extra sample is not alpha. Native reflection controls remain available as explicit MR authoring; no GT-specific source shader rules forced |
| Physics | Independent `Evo2FourRunner` clone of clean retail Terrano; measured wheelbase/tracks/radii and native ride reference. Donor1500kg mass, springs/dampers/engine/tyre behavior retained |
| Drivetrain | Explicit MR RWD `Engine/DriveType=1`, from original TRK front torque0/rear torque1 records. Raw Evo2 drive_type enum is not treated as MR enum |
| Body physics dimensions | Terrano3.5/2.0/1.5m configuration values retained as donor solver parameters, distinct from measured render extents; collision hull fitted separately to selected structural body, with conservative guarded affine fit |
| Camera | Existing Gameplay Camera2.0 source-qualified five-mode inspection, overrides and reset; no fabricated Evo2 camera recovery |
| Audio | Explicit MR Navara tuning profile7; no original Evo2 recording/recovery claim |
| Crew | Clean retail Navara driver/co-driver pair, independently recorded rigid fit and editable Crew Studio definitions; no original Evo2 crew claim |
| Shadow | Existing Shadow Studio Auto Fit proposal; editable/resettable. No terrain-projection or original source shadow parity claim |
| Identity/frontend | TOYOTA /4RUNNER SR5; Results TOYOTA4RUNNER; generated vehicle art, independent marker color and frontend Auto Frame+0.678503m. This offset belongs to frontend presentation only |

Native intact/OFF state serialization preserves the authored original surface
attributes; alternate damage/lamp cases are separate. Unsupported source
animations, nine source color transforms, dynamic axle/light passes, reflections,
bump and settled suspension remain documented unknowns. Ten source triangle /
normal inconsistencies are retained rather than silently repaired.

The collision/Shadow/Frontend integration exposed an existing combined-workflow
gap: appearance edits changed whole-model hashes although the structural shell
was unchanged. A bounded rebase now verifies the original full hash, exact
selected core positions and collision bytes before updating only the derived
pin. Shadow compares effective collision-fitted models. Real surface/crew edits
now cooperate with collision, Shadow Auto Fit and frontend while preserving
hash guards and reversibility. MSVC launcher builds use short owned temporary
CMake scratch to avoid MAX_PATH failures in normal nested Workshop outputs.

## Delivered private project and isolated candidate

Evidence root: `.research-output/vehicles/cross-game-4runner/`.
Final delivery: **`pilot-delivery/`**. `pilot-final` is retained failed long-path
build evidence; `pilot-final2` is the prior validated AWD-donor iteration,
superseded by the source-backed RWD delivery. Do not launch those as final.

- `pilot-delivery/workshop`: owner-editable Source Fidelity project.
- `pilot-delivery/author/project`: independent SDK author project.
- `pilot-delivery/inputs/source-scene`: immutable source copy and original sidecars.
- `pilot-delivery/source-baseline/assets`: immutable diffuse-only MR comparison.
- `pilot-delivery/builds/source-fidelity/candidate/Launch-SDK-Roster.cmd`:
  isolated owner-test launcher; no installed assets replaced.
- `Open-4Runner-Workshop.cmd` / `Launch-4Runner-Candidate.cmd`: convenience links
  generated after validation, opening the final project/candidate only.

The30-entry alternative roster retains Mercedes26, Subaru27 and frozen Lancer28;
Toyota independently occupies29/T2 local9. Pajero, Heritage Trooper and Clio29
projects/builds/reservations are preserved. The owner's accepted Trooper gameplay
is not rolled back by old historical pending notes. Only one29 alternative is
selected here; no31st slot is claimed. The native candidate is an independent
sealed resource tree and private runtime patch allocation over the original EXE.

Create through Workshop: reopen the neutral scene in **Source Garage → Create
MR Source Fidelity**, provide clean retail Data.sma, its unpacked root, Terrano
model directory and a qualified base roster. Creation writes fresh private
authoring and Workshop trees, copying the roster for an independent29 alternative.
Use the existing Validate/Build controls. **Source provenance** verifies and
opens original identities, hashes, coordinate/measurement evidence and unknowns.
Help topic `universal-source` describes safe editing and owner qualification.

CLI uses the same orchestrator:

```powershell
python tools/create_source_garage_pilot.py --help
python tools/validate_source_garage_pilot.py --workshop '<private Workshop folder>' --output '<fresh validation folder>'
python tools/validate_universal_workshop_windows.py --help
```

## Available validation and exact evidence

| Evidence | Result / boundary |
|---|---|
| Complete Windows synthetic/CPU suite | `full-windows-delivery.log`; final exact count in REGRESSION_MATRIX.md; two pre-existing optional private-fixture skips |
| Focused new tests | Generic scene conversion, winding/normals/UVs, source/material decisions, per-wheel routing/sealed resource guards, profile budgets, source baseline/provenance and pilot/rebase/RWD guards |
| Native wheel code replay | `../evo2-native-v68/native-wheels-replay.json`; original-x86 lifecycle, standalone/chained guards and existing mechanics regression PASS |
| Deterministic geometry/textures | `determinism/validation.json`;10/10 SourceBaseline and21/21 enhanced DX/DXT byte-identical |
| Actual serialized four-wheel mapping | `pilot-delivery/wheel-resource-equivalence.json`; original side textures and rest-basis geometry PASS |
| Final RWD-only change | `pilot-delivery/rwd-correction-proof.json`; all31 DX/DXT match prior iteration, only one sealed runtime XML resource changes one field in the new family; clean Terrano/other families unchanged |
| Real Windows creation/UI/GPU | `windows-delivery/validation.json`; source dialog → create/open → Validate → provenance, RWD field, body/frontend/six views and eight wheel outside/inside captures |
| Studio edit persistence | `studio-delivery/validation.json`; surface and crew exact Undo/Redo, collision+Shadow+frontend, Camera2 reset, Results/marker/reopen, Restore;63 original author/baseline files unchanged |
| Source/native comparison | `comparison/` before diffuse-only MR captures, `windows-delivery/` after MR adaptation; visually inspected, not source-game/D3D8 parity |
| Geometry/material records | `geometry-and-material-validation.json`; exact model hashes, bounds, draw counts and alpha flags; static controller alternatives counted separately |
| Resource differences / accepted addons | `resource-differences.json`; exact added/removed/changed rows against Heritage alternative; all model/textures for accepted26–28 identical |
| Original preservation | `preservation-final.json`; all2493 protected files unchanged: prior accepted projects/original MR files, original59-file neutral project and donor POD/EXE |
| Native launcher | `pilot-delivery/pilot-report.json`;304 resources,260 operations, verify/environment/native-allocation preflights PASS; game_launched=false |
| Source-only handoff | `review/archive-manifest.json` after local commit; committed text only, hashes/ZIP CRC/Python AST checked; excludes proprietary model/texture/audio/native binaries and private previews |

Final D3D9 captures show the recognizable source body, opaque sidewalls and
inner wheel faces, intact front/side glass, MR crew and rear-only brake ON/OFF.
The high source stance remains visible. The following are **still owner checks**:
actual selection/art and large frontend, spawn/animation/culling, wheel stance
and contacts, glass damage, brakes, audio/camera, collisions/AI, finish/Results,
menu return and race re-entry. See [short checklist](FOUR_RUNNER_OWNER_CHECKLIST.md).

No original donor installation, MRallye.exe, clean retail Data.sma, installed
d3d8.dll, accepted project or unrelated Randomizer file is modified. No push,
publication or release. **Stop after this one owner-testable Source Fidelity
pilot; gameplay acceptance remains pending the owner's real D3D8 test.**
