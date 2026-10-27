# Vehicle Presentation Polish — 27 October 2026

## Delivered scope

Gameplay Camera 2.0 was completed first (`3919a7e`, ledger `fc3c97d`). This
separate phase edits fixed Results names and the large VehicleSelect model.
Accepted Heritage Trooper gameplay, alternative Pajero roster, frozen Subaru,
Lancer materials/physics/audio, PERF2 and the existing capacity limits remain intact.

### Functionality matrix

| Feature | Implemented scope | Boundary |
|---|---|---|
| Driver / Results Name | Existing fixed `results.display_name`, 64 printable ASCII; immediate row with actual32×16 resource, Apply/history/Restore | No DriverID, AI behavior, frontend model name or human/network name change; row font/layout illustrative |
| Frontend Presentation | Dedicated Vehicle Details tab and editor; original/modified/read-only NewRav; continuous owned D3D9 preview, manual vertical draft, Apply/reset/history/save/build | Addons with unique qualified namespaces only; stock reference read-only |
| Auto Frame | Match lowest source geometry to original NewRav baseline at4:3 | Vertical-only, no scale matching; no automatic geometry or suspension edit |
| Clipping and panel guides | Source vertex projection/full viewport envelope, source matrix and FOV; illustrative panel rectangle in editor/viewer | Panel rectangle is NOT a recovered native scissor; widescreen proxy/device effects pending |
| Wheel baseline | Existing exact repeated-wheel proof, source topology/UV correspondence | Frontend rest pose, not suspension or physical ground contact |
| Native adjustment | Only selected complete-resource private camera target.y | Resource/scene/source-bound, not a direct live CarID getter; D3D8 pending |
| Unsupported | Frontend distance/FOV/scale/rotation authoring, replay, stock framing build | Read-only / not advertised |

## Original source evidence

Retail EXE SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
`VehicleSelect.xml` original SHA256
`ec7fd6372fe5008b1039eb8e09890ef3b37396dad1581568af439cbb611b58e1`.
Private REA snapshot and original instruction dumps are under
`vehicles_scratch/presentation/`, ignored, not included as asset baggage.

- `0044C4C0` gaFrontendCarMoverAI reads `Frontend/VehicleSelect/CarModel`,
  loads `Vehicles/<family>/complete` through `004F5B70`; recovered path has no
  model-bound auto-centering. Spinner is separate and retained.
- Shipped CarModel row matrix has XZ `.89/-.45/.45/.89`, translation `(8,-2,189)`.
- `0052A6D0` aiStaticCamera update uses eye `(10,-1,200.30)` and entity position
  plus target offset `(-1.22,2.18,0)`. Native stored source angle45 uses the
  linear min(1,H/W) aspect rule; source FOV is not vertical45.
- Original matrix-writer call `0052A7BC -> 004895F0` is the single new CALL hook.
  Wrapper preserves flags/registers, adds no x87 work, keeps all source arguments,
  and changes only the already computed local target.y before the original writer.
  Original update recomputes the source target every frame, so no cached global
  pose or stale-owner cleanup is introduced.
- Gate: exact `CarModel` entity, original translation/eye/target/up, full canonical
  complete-resource key (ASCII case/slashes only), all44 native bounds bytes.
  Offline source SHA and unique roster CarID/family are additionally required.
  This is resource-scoped runtime ownership; it is not falsely described as a
  runtime CarID lookup. Changed scene/pose/resource/bounds fail closed.
- `0047C840` ordinary AI Results path and existing native `0047CC81` string
  consumer remain the name mechanism. Delivered payload resolves `HERITAGE CREW`
  for CarID29 with tested DriverIDs0/7/29 and unchanged competitor record.

## Measurements and diagnosis

Same source scene, source45,4:3, all used complete vertices:

| Model | Lowest model Y (m) | Original bottom NDC | bottom pixel at640×480 |
|---|---:|---:|---:|
| Heritage Trooper | -0.384573 | -0.803996 | 432.96 |
| Stock NewRav | -0.003857 | -0.671229 | 401.09 |
| Lancer | -0.138218 | -0.717810 | 412.27 |

The shared source camera exposes differing frontend model origins/proportions.
Trooper sits ~31.86px lower than NewRav. This is not evidence of a physics ride
height defect. Auto Frame selects +0.453632m private-target correction, matching
NewRav's lower screen baseline without moving model vertices or wheel hubs.
The value is an aim correction, not a measured suspension displacement.
Trooper wheel baseline is independently qualified by exact mirrored/reindexed
positions, UV and topology in3 wheel parts,7 body translations; max error
8.94e-8m. NewRav is a reference family, not a newly qualified stock editing ID.
The real source matrix is applied only to the private preview scene, including
its slight XZ scale and inverse-transpose normals; DX/DXT stay unchanged.

## Isolated candidates and preservation

Private output root: `.research-output/vehicles/presentation/`.

- `t/n/candidate/Launch-SDK-Roster.cmd`: Trooper fixed Results name only,
  `HERITAGE CREW`.
- `t/f/candidate/Launch-SDK-Roster.cmd`: same name +0.453632m frontend correction.
- Accepted owner-tested Heritage baseline remains
  `.research-output/workshop-builds/2534912085f2/candidate`.
- Separate camera candidate remains `.research-output/vehicles/camera2/t/b/candidate`.
  Do not confuse these independently qualified experiments.

Both presentation builds have313 identical immutable resource files. No geometry,
textures, UI atlases/XML, wheels, physics, lighting, glass, crew, audio or shadow
resource changes. Fresh `PlayerState.xml` matches the root save exactly; the
owner-played baseline save/backup differences are listed separately.
Name-only payload129440B; framing payload129984B with the entire name-only prefix
preserved. Repeated same-config derivations produce identical metadata/native
payload and image bytes. Original EXE, graphics DLL and corpora/retail SMA match their protected hashes.
The root Data.sma now matches the original retail hash03c2b52d..., whereas the
prior Camera2 observation recorded7cc2be10.... Attribution of that intervening
change is not established. This phase issued no root archive write/restore
command; it does not falsely claim an unchanged root archive across those two
observations. All313 candidate resource comparisons remain exact. See
preservation.json for both observations.

## Validation and reproduction

- `presentation/phase-tests-final-state.log`: 923 tests /2 pre-existing optional private-fixture skips;62.872s PASS.
- `windows-delivery/validation.json`: actual Tk and D3D9, draft/persistence/history/reset,
  native32×16 icon, same process live updates, read-only stock reference,
  unchanged resource bytes and owned viewer cleanup.
- `native-delivered.json`: original updater plus delivered emitted x86, positive
  selection/case-slash variants and rejected foreign scene/name/model/bounds/
  pose/null cases; stack/nonvolatile registers/FPU depth preserved.
- `results-native.json`: delivered string consumer with unchanged DriverID/CarID.
- `candidate-differences.json`, `n-validation.json`, `f-validation.json`:
  exact ownership, deterministic builds and frozen base verification.
- `regressions/`: Audio, Paint/Crew, stock materials, texture25–400%, binding/stock,
  Physics/Camera/vehicle identity/art; native audio multi-owner/failure cases. Camera2 five-mode live regression also
  passes; native-camera-composition.json replays both adapters in one derived
  payload without generating another runtime.
- `frontend-comparison.png`: real D3D9 source-scene captures, Trooper A/B,
  NewRav and Lancer at the same aspect. Private; no retail assets in source archive.

CLI shares the same Core:
```
python tools/workshop_vehicle.py PROJECT results-name "HERITAGE CREW"
python tools/workshop_vehicle.py PROJECT frontend
python tools/workshop_vehicle.py PROJECT auto-frame-frontend
python tools/workshop_vehicle.py PROJECT set-frontend 0.453632
python tools/workshop_vehicle.py PROJECT export-frontend --view original
python tools/workshop_vehicle.py PROJECT export-frontend --view "stock NewRav"
python tools/workshop_vehicle.py PROJECT restore --section frontend
```
Auto Frame CLI returns an unsaved draft. Source hashes must be requalified for a
new appearance version; incompatible inherited frontend edits are reported as
conflicts. No second lossy model conversion is performed.

## Owner gameplay checklist — PENDING

1. Compare name-only and framing launchers against accepted Trooper; verify
   large rotating3D model only moves vertically as intended and stays within
   the Vehicle Select panel through rotation and vehicle switching.
2. Select NewRav/other stock cars and Lancer; their presentation must remain
   unchanged. Check4:3 and usual widescreen/proxy settings separately.
3. Finish with Trooper as ordinary AI participant; check `HERITAGE CREW` and
   unchanged small icon. Human/network branches intentionally retain native names.
4. Enter/re-enter races, brake/crack glass/damage; wheels, physics, camera,
   lights/audio and race model must match accepted baseline.
5. Camera2 gameplay FOV needs independent verification. The locally inspected
   graphics INI has an existing global GameplayFOV override; account for that
   when comparing native FOV. This phase does not change the graphics DLL/INI.

Offline rendering/CPU tests do not establish actual D3D8 visual or lifecycle parity.
Stop here for owner review; no further fleet imports or capacity expansion.


### Final local entrypoints and retired test runtimes

`Open-Presentation-Workshop.cmd` opens a private library with the updated Trooper,
Lancer camera experiment and stock reference project. Main `Rally-Workshop.cmd`
also uses the updated source and rebuilt Previewer. `Launch-Presentation.cmd`
and `Launch-Results-Name-Only.cmd` are shortcuts to the two isolated candidates.

`framing-margins.json` records640×480 vertex envelopes, viewport/panel margins
(the panel is illustrative). `wheel-baselines.json` qualifies Trooper's wheel
baseline; exact repeated-wheel proof is unavailable for NewRav/Lancer, so their
reported lower envelopes are explicitly all-used-geometry rather than inferred
wheel ownership. No fitment changes were made to force those proofs.

Six explicitly verified temporary runtime leaves were moved to
`.research-output/runtime-quarantine/2026-10-27/presentation/`,2,326,491,527B.
Nothing was deleted. Same-volume movement frees0 physical bytes; the owner may
remove that quarantine later. Sources/projects/reports/launchers, accepted
Heritage/Pajero/Subaru and the final Camera2B/name/framing candidates remain.
`runtime-moves.json` records old/new paths. Recreate retired regression candidates
from their retained source configuration rather than launching their old paths.
