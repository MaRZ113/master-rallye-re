# Physics & Camera Studio + Vehicle Identity & Presentation

26 October 2026. `research/vehicles`. Implemented in shared SDK Core and the
existing Windows Rally Workshop. **Offline/Windows qualified; new D3D8 gameplay
and earlier Audio/Classic owner listening/comparison gates remain pending.**

## Open and use

Launch `Rally-Workshop.cmd`, open a qualified project, then **Vehicle Studios**.
The private Lancer demonstration is
`.research-output/vehicles/pcstudio/win-release/project`;
`Open-Physics-Camera-Studio.cmd` in the phase evidence folder opens it directly.
The existing main interface, viewport and Audio/Material/Paint/Crew panels stay
in place. F1/Help includes the new searchable offline topic.

| Workspace | Working functionality / native boundary |
| --- | --- |
| Physics | Typed grouped source/current/reference tree, search, numbers/vectors/bools, source hashes, schema guards, compatible donor-group copying, reset/history/reopen/build. Lancer has 173 displayed rows; 33 retail families pass the existing source schema. Counts/damage remain read-only; unknown units are explicitly unqualified |
| Camera | Exact runtime model qualification, CarID/family/SHA binding, follow half-length and height, before/after side extent diagram, reset/history/build. Extents are not direct camera position/distance. Unsupported FOV, smoothing, focus, replay and CarID0 remain unavailable |
| Details | Manufacturer, model, combined and Results display strings, description; ASCII validation and conservative SDK budgets. Internal identity, ID, class, family and resource namespaces are preserved. Stock labels remain read-only |
| Aliases | Native filename plus friendly metadata, search both, inspect original texture, source-hash compatibility, undo and visual-version transfer. No resource rename or automatic semantic classifier |
| Vehicle art | Actual DX/DXT sources; existing role-specific MR presentation cameras; frontend or explicitly assembled race rest pose; bounded yaw/pitch/padding; generate both or one; compare original/generated; explicit Apply; exact canonical compiler output on reopen |
| Shared actions | Save, Undo, Redo, scoped Reset, Restore all, Validate, Build. CLI `tools/workshop_vehicle.py` calls the same service as GUI |

### Implementation

`workshop/vehicle_authoring.py` composes the established typed physics compiler,
verified retail cloning, exact runtime resource transforms, camera binder,
manifest validator and UI compiler. It does not contain a replacement native
parser, camera patcher or bank writer. `vehicle_ui.py` supplies the modeless
workspace. Native hook/DSP/launcher source is unchanged.

The UI renderer now accepts selected role/model/camera settings. The extracted
`preview_transform` is the existing Previewer transform math, reused for four
qualified race-wheel instances, normals and reflected winding. Combined geometry
budgets are checked. Race art uses presentation anchors, not simulated settled
suspension or automatic physics fitment. Rendering remains a diffuse approximation.

The generated 512×320 source is pinned separately from its 128×128/32×16 reviewed
image. Native compilation applies `mr-native-v1` exactly once. Apply verifies all
render-input geometry/texture hashes, image dimensions, provenance and canonical
composition. Editing a source before Apply requires regeneration. Existing bank
records are preserved; stock-frame replacement remains unsupported.

New visual versions start from original author data and replay physics/details
and compatible aliases as separate layers. Old camera hashes/art are reported
for requalification, not silently rebound. Audio presets retain their established
independent transfer. Native geometry, collision, hubs and suspension are not
adjusted by camera/name/alias/art edits.

## Controlled candidates and exact differences

Private root: `.research-output/vehicles/pcstudio/`.

| Candidate | Deliberate change | Game resource-root differences from accepted Source Fidelity |
| --- | --- | --- |
| `iso/physics/candidate` | Lancer mass 1320 → 1386 kg (+5% demonstration, not a new handling recommendation) | Only `DataGame/vehicles.xml`; parsed difference is exactly `LancerEvo4 / Chassis/TotalMass`. All other families/fields unchanged |
| `iso/camera/candidate` | CarID28 follow extents 2.2 / 1.4 m | Zero resource changes; existing external source-guarded camera adapter only |
| Windows combined build, recorded in `win-release/windows-validation.json` | Same mass/extents, explicit display labels, two correct shared-atlas aliases, reviewed art | Exactly `vehicles.xml`, `VehicleSelect/carsheet_033_000.dxt`, `RaceResults/smallcarsheet_031_000.dxt`; no other resource differences |

The combined build is opened through its recorded `Launch-SDK-Roster.cmd`.
Names are compiled as native literals; aliases/description remain author metadata.
DX/DXT vehicle appearance, crew, wheels, damage, brakes, all WAVs and donor
physics families stay unchanged. UI bank layout/stock records, reference indices,
dimensions and checksums pass the existing roster validator. Both stock/addon
Material builds and stock Restore-to-zero-overrides were repeated.

## Validation evidence

- `tests-release.log`: **862 tests in 47.458 s, OK, one optional fixture skip**;
  eight new generated-fixture tests cover typing, reject cases, identities,
  history, hash guards, aliases and original author baselines.
- `win-release/windows-validation.json`: real Windows Tk controls/workers,
  original/current/ref comparison, typed RPM and mass edits, reference copy/Undo,
  camera/edit/Undo/Redo, names, aliases, both generated frames, explicit Apply,
  Save/reopen, reset/history, Help, Validate and actual isolated Build.
- `iso/isolated-validation.json`: independent physics/camera builds and sealed
  roster validators; camera original x86 replay has 18 target/mismatch/fallback
  cases, preserving bounds memory, registers, stack and x87 state.
- `native-display-and-isolation.json`: 22 emitted literal display-path checks,
  Results, ID/class maps, stock fallbacks, AI audio lookup/register ABI. Typed
  Broker/string/audio stubs are explicit; not gameplay proof.
- `cross-module-art.json`: customized four-layer preset survives RPM edit;
  audio edits preserve vehicle state; deterministic PNG, independent role
  regeneration, race-wheel provenance and Restore-all/Undo.
- `version-transfer.json`: real new Source Fidelity/Classic versions retain
  customized four-layer preset, physics/names, compatible aliases and original
  Restore defaults; camera/art conflicts retained.
- `reg`, `audio-reg`, `paint-reg`, `style-reg`, `reference-reg`: actual Windows
  Material/Binding/reflection/addon+stock builds, Audio import/auditions/presets,
  Paint/Crew/history, Classic generation/navigation/approval gate and local stock
  material browser. `classic-qualified`: deterministic conversion, protected
  collision/glass/lights, native damage replay and 30 D3D9 diagnostic views.
- `zoom-reg`: four textures × seven zooms × two windows = 56 captures; channels,
  checkerboard, cursor zoom, 1:1, alpha and original BGRA/PNG equality.
- `native-audio-*`: original engine/voice lifecycle, two interleaved owners,
  RX/RW page protection, drive/coast/neutral/gain, stock passthrough, re-entry and
  three optional voice-allocation failures. DirectSound/device remains mocked.
- `preservation.json`: all 369 Source Fidelity + 367 Classic accepted resource
  hashes, previous five audio candidates, original EXE/DLL/retail archive and
  installed Data.sma match their prior pins. No native renderer, physics tuning,
  capacity expansion, Randomizer work or original-resource writes.

Private captures are evidence, not source-distribution assets. A source-only
archive is produced from canonical committed Git blobs with per-entry hashes,
CRC checks and Python syntax validation. Its manifest records the exact commit.

## Reproduce

Install Workshop optional dependencies, provide your own verified source project,
retail SMA/unpacked data and existing qualified roster settings. Open the project
and use the controls above; no JSON/XML editing is necessary. CLI examples:

```text
python tools/workshop_vehicle.py <Workshop-project> physics --reference Megane2
python tools/workshop_vehicle.py <Workshop-project> camera
python tools/workshop_vehicle.py <Workshop-project> generate-art --model complete.dx
python tools/workshop_vehicle.py <Workshop-project> apply-art <reviewed-generation.json>
python tools/workshop_vehicle.py <Workshop-project> build <fresh-isolated-output>
```

`validate_workshop_vehicle.py` exercises the qualified Lancer pilot on actual
Windows; its private reference and output paths are explicit arguments. The
synthetic tests need no MR/GT assets.

## Owner gameplay checklist

1. Compare physics-only with accepted baseline: acceleration/reverse, steering,
   grip, braking, suspension, collisions; mass example should affect only Lancer.
2. Compare camera-only on Lancer and stock/other addons. Check all normal follow
   modes, acceleration/jumps, exit/re-entry; replay controls are not authored.
3. In combined candidate inspect Vehicle Select names/art and Results label/icon.
   Check text width, bank alignment, AI participants, finish/Results/re-entry.
4. Check original wheels/crew/glass/reflections/brake lights/damage and all four
   audio layers. Compare Audio/Classic separately using their existing candidates.
5. Return to the accepted baseline or Undo/Reset and build a fresh private copy.

Actual D3D8 behavior, camera dynamics, AI/device lifetime and listening are
**PENDING OWNER**, not implied by CPU replay, D3D9 captures or package checks.
Audio Import 2.0 and the new optional GT Lab adapter proceed as a separate phase;
no Heritage Garage, Blender Bridge, Fleet Builder or new vehicle begins here.
