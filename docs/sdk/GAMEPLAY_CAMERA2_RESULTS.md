# Gameplay Camera 2.0

27 October 2026. `research/vehicles`, parent `ebcb28d9ad683d92aae94f9ba48426ffeef7b083`.
Original retail SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Original EXE, D3D8 DLL, archives and accepted Heritage candidate remain read-only.

## Five actual player views

`004B8170` increments manager+1DC, consulting the original setup counts (3/2),
then switches manager+1E0. Original x86 execution produces this exact cycle twice:

| Studio mode | Native manager type / index | Object | Original parameters | Editable |
|---|---|---|---|---|
| 0 | 0 / 0 | Follow, constructor0052C310 | FollowCamera0 | FOV; Dist Front, Back, Up |
| 1 | 0 / 1 | Same Follow class | FollowCamera1, pitch enabled | Same; pitch/history read-only |
| 2 | 0 / 2 | Same Follow class | FollowCamera2, Accel false | Same |
| 3 | 1 / 0 | Fixed, constructor0052BC30 | FixedCamera0, Type0 | FOV only |
| 4 | 1 / 1 | Same Fixed class | FixedCamera1, Type1 | FOV only |

These are five visible choices, **not five native classes**. Labels remain
source identifiers; subjective cockpit/bonnet names are not substituted for evidence.
Dispatcher004B82A0 also constructs special types2/3/4/6. Alternative cycling at
004B81E0 /004B8210 and look-back004B8690 are separate paths. No independent
replay/rear camera authoring is claimed. Rear view naturally inherits the selected
camera's FOV; its position/basis changes remain the original game's responsibility.

Constructor004B7620 selects Camera/Setup or Camera/SplitSetup according to the
renderer camera collection's active count. They have three Follow and two Fixed
records each. Per-CarID overrides explicitly apply to **normal AND split** for
the selected preset; independent split authoring is not exposed.

## FOV and position ownership

004B98E0 copies Follow record+24 FOV and +28 Accel separately from object geometry
fields;004B99C0 copies Fixed record+14 FOV. Dispatcher004B858D..004B8591 writes the
chosen degree scalar to the selected renderer-camera object+0. This is neither
a vehicle physics field nor a global renderer setting.004E3DD0 allocates four
renderer-camera records; it does not prove four-player gameplay support.

004F2350 returns storedFOV * min(1, viewportHeight/viewportWidth). This is the
original **linear** aspect rule, not a conventional horizontal-FOV conversion.
005614A0 converts it to radians and calls005D681F. The original helper constructs
a left-handed perspective matrix. CPU replay checks four landscape/portrait/split
viewport cases; X/Y scale errors are below2e-6. The Previewer uses an equivalent
FOV/aspect scale with its existing right-handed viewing convention. Final D3D8
view composition, clipping, interpolation and device presentation remain owner gates.

Fixed initializer0052BEC0 overwrites the XML's placeholder offsets:
forward = half sourceZ extent −.12; Type0 height = maxY −.05*Yextent;
Type1 height =.25*Yextent.0052C090 applies the current target frame each update.
Original initializer/update/matrix instructions are replayed for both types,
three yaw angles and the actual bounds of all five test vehicles. Arbitrary
Fixed position sliders would be misleading and are not offered.

Follow's first-frame flat rule remains the earlier qualified reconstruction.
Native pitch, acceleration, intersection and smoother helpers are preserved;
their evolving state is not replaced with a guessed preview simulation.

## Isolated authoring

Optional `mode_overrides` extends the existing version1 source-pinned profile:

```json
"mode_overrides": {
  "follow0": {"FOV": 78, "Dist Front": 5.775833333333333,
              "Dist Back": 4.2, "Dist Up": 0.65},
  "fixed0": {"FOV": 80}
}
```

Original copy CALLs004B83A0 /004B83F3 are wrapped. Original copies execute first;
only the private camera-object fields and their local FOV output are changed.
The existing exact model-key, canonical CarN, physical CarID and bounds gate is
reused. Each selected ID is additionally checked against its own model key,
including when another allowed model has identical bounds. Original source SHA
is checked at build/integrity validation; runtime uses key/bounds, not a claimed
per-frame SHA calculation. No owner/entity/model pointers are cached. Alternate
manager cycles (+1E6/+1E7), foreign names, missing owners, mismatches and unrelated
IDs pass through. Existing Follow extent hooks are retained.

SDK safety ranges: FOV20–140 degrees; Front .1–50, Back .1–30, Up −5–10 model
metres. These are conservative authoring bounds, **not measured engine limits**.
CarID0 remains preview-only pending missing-key qualification. Smoothing, pitch,
terrain/velocity, replay parameters and collision are not editable here.

## Live Studio

Open Game Camera Lab → choose mode → Open Live Preview. Numeric draft changes
reach the same running D3D9 window through a bounded, versioned48-byte IPC packet.
No scene reload or process restart is needed for mode/FOV/pose/aspect changes.
LMB changes Follow eye height/back; Ctrl+LMB changes forward target; wheel changes
FOV. G returns to independent free inspection; Shift+drag edits the camera draft
from the guide view. Feedback synchronizes numeric fields. Source Original/Donor
comparisons are read-only. Apply persists through Core history; Cancel discards
the draft. Save/reopen, selected-mode reset, whole-camera reset, Undo/Redo and
isolated Build retain existing semantics. Build does not implicitly apply a draft.

Owner feedback identified lower-frame clipping. Auto-frame is explicitly an
**unsaved Follow draft**: project the staged vehicle envelope, retain height,
prefer the current distance, then adjust the supported forward-look parameter
to leave10% NDC margin. Original remains exact and may retain its source framing.
The concrete Lancer correction changes DistFront14→5.775833; it is not a mesh,
physics or hidden renderer translation. A manual Frame car button is available.

An opaque neutral ground plane and one-metre grid sit beneath the staged rest-pose
geometry. The eye-height readout is relative to that **illustrative** floor, not
settled native suspension. This provides a height reference in the Fixed/bonnet
view. Guides/floor are excluded from model-fit bounds and surface picking; the
floor depth-tests against the vehicle. Live frusta use current FOV/aspect in free
inspection; their1.5m range is illustrative, not a native clip plane.

## Candidate and evidence

Private root `.research-output/vehicles/camera2/`:

- `t/b/candidate/Launch-SDK-Roster.cmd`: framed Lancer28 Follow0 and Fixed0 FOV
  experiment, accepted HeritageTrooper29 roster. Other modes remain source defaults.
- `t/a`: earlier native parameter experiment; not the final framing recommendation.
- Accepted unmodified reference remains `workshop-builds/2534912085f2/candidate`.
- Native payload129440→131378 bytes; the original payload prefix is identical.
  All313 immutable resources match the accepted reference. Fresh PlayerState is
  copied byte-for-byte from the root save; the owner's played reference save and
  its backup are reported separately, never treated as asset regressions.
- `native-delivered.json`:80 cases execute the delivered combined payload with
  original record-copy code; original dispatcher and projection also execute.
- `native-model-matrix.json`: five separately bound vehicles (Megane18, Subaru27,
  Lancer28, Pajero29, Trooper29),80 parameter cases plus six Fixed replays each.
  Pajero and Trooper are **not installed together**. Frozen Subaru is inspected
  and CPU-tested from copies, not rebuilt or changed.
- `model-matrix.json`:40 source mode/split reports for four projects plus five
  read-only Subaru mode reports;25 actual D3D9 captures.
- `windows-legacy/`: prior Lab/marker/history/viewer event regression.
- `windows-phase/`: actual live numeric/drag/wheel/mode/comparison/capture,
  no draft persistence, Apply/Save/reopen/history/reset and process close/reopen.
- Full suite and qualified module Windows regressions are recorded in the
  regression matrix; no D3D8 gameplay launch is part of these tests.

CLI shares the same Core: `workshop_vehicle.py PROJECT game-camera --mode 3`,
`set-camera-mode JSON_FIELDS --mode 0`, `export-game-camera --mode 0 --view modified`.
Use existing validate/build/undo/redo commands. `{}` removes that selected override.

## Owner D3D8 checklist

1. Launch the accepted reference and modified candidate separately at the same
   actual render resolution/aspect; leave root installation and saves intact.
2. Cycle all five views twice on Lancer. Only Follow0 and Fixed0 should change;
   source bounds/physics/handling/wheels/crew/glass/lamps/marker/audio stay intact.
3. Compare a stock car, Subaru and Trooper: their camera settings must remain stock.
4. Check rear look, race start, acceleration/braking/jumps/terrain, camera switching,
   vehicle switching, exit/Results/re-entry and split-screen. The new per-mode
   override intentionally applies to both normal and split; compare that scope.
5. Match static screenshots against source pose/FOV reports while recognizing
   the Previewer lacks native world, suspension settling, history and terrain.

Owner has now confirmed the separate Heritage Trooper geometry/wheels/physics,
brake lamps, glass, audio, UI art, finish and re-entry in retail. That acceptance
is preserved. **New Camera2.0 native behavior and D3D8 visual parity remain pending.**
