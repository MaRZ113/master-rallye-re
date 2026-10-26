# Game Camera Lab: exact-retail evidence and bounded reconstruction

26 October 2026. Target `MRallye.exe`, x86 PE, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Original executable and retail resources remain read-only. Ghidra 12.1.4 via
REA, original instruction/PE mappings and controlled Unicorn execution are
distinct evidence levels. Decompiler signatures are not original source/ABI.

## Sources and ownership

| Address / source | Observed role | Qualification |
|---|---|---|
| `DataGame/Cameras.xml`, Camera/Setup and Camera/SplitSetup | Shared follow arrays, 3 records each, separate FOV/Accel fields | Exact original archive, typed schema and member SHA recorded privately |
| 0052C310; vtable 00691CC0 | Follow object constructor, 0x74-byte allocation in manager | REA body/assembly; constructor defaults are not active XML presets |
| 0052C3E0 | Serializer names DistFront/Back/Up, Smooth, BodyDir, Pitch | REA original instruction references / decompiler cross-check |
| 004B98E0..004B99B7 | Follow-record copy, 0x2C stride; radians/cos conversions | REA complete body; RET 0x10, ECX receiver observed in assembly |
| 004B82A0..004B85BF | Mode-specific camera construction/reconfiguration, case0 follow | REA; other constructors do not imply qualified alternative-mode previews |
| 004B7DE0 | Target resolution, timer/reconfiguration, active-camera updates and mode transitions | REA static; full input timing/interaction not replayed |
| 004B7AFB..004B7B21; 004F59F0 | CarN target-name association | Existing V-SDK2 exact source; do not cache entity/Broker pointers |
| 0052C630..0052C6C2 | Model-bound initializer through target entity+50; writes follow terms | Original instructions + existing initializer replay |
| 0052C6D0..0052CCFE | Follow update; first-frame, pitch, smoothing and helper branches | Raw code + original CPU replay; Ghidra has no defined function here |
| 0052CC06; 0052CC35 | Smooth multiplier use; call 0052D1A0 on noninitial path | Verified instruction sites; full acceleration/velocity semantics NOT established |
| 0052CC69 → 004895F0 | Eye/target/up → basis/world matrix at renderer camera+88 | REA matrix writer plus original CPU execution; not a final view/projection matrix claim |
| 0052CC6E..0052CCB5 | Conditional basis-axis negation | Original assembly; final renderer convention/rear-view association not qualified |
| 004E3DD0 | Renderer camera-array access | Static call sites; typed service mock in CPU replay |

Fresh REA dossiers: constructor `ev_8f060ec6a7a6e74717385e24c5c95df479ec131f5c46caa44f883b04fb3511c7`,
serializer `ev_15286f2ff5088c76dbbac83f2c6fd726fc0290288e17b1f2400aaa8d47cef626`,
copy `ev_524e1fc5075da18b76d3d33e83e79c216c32f838d1073206f9ab0ec86687006a`,
mode construction `ev_a19ee02079457e6b5966a713ac8df51fdc23ee80e9fcb85ff85d2a11d9087f5c`,
manager update `ev_5101f1ab1fa8b30198b252b95e648cde44a443b05ba1814ab9d00d5765c386a8`,
matrix writer `ev_21615d7b33ac6b1075759e1ba7c8c15a5bb3f144c96398ba8ac345a958e178af`.
Complete raw camera range read:
`ev_294e1b8bbd67143c799d2fe2c990477bbbe19c00b3b4e1bdcffe434d7d613958`.
Private snapshots/evidence live only in ignored `vehicles_scratch/camera-lab/`.
REA session closed after export. Missing Ghidra function definition is an analysis
boundary, not proof that code is absent or permission to invent a decompilation.

## Follow object fields, not a general engine structure specification

| Offset | Observed meaning |
|---|---|
| +0C | Initial-update flag, reset by initializer, cleared at 0052CCF0 |
| +38 | Renderer camera-array index |
| +3C | Enable model-extent initializer |
| +40 | abs(stored maxZ-minZ)/2 |
| +44 | abs(stored maxY-minY) |
| +48 / +4C / +50 | Dist Front / Dist Back / Dist Up |
| +54 / +58 | Min / Max rotation converted degrees→radians |
| +5C / +60 | cos(Pitch Limit degrees), UsePitchSystem flag |
| +64 / +68 | Smooth Camera Multi / Body Dir Multi |
| +6C | Matrix-axis policy flag observed; no independently authored meaning |

FOV and Accel are separate copy outputs from source record+24/+28. They are not
per-CarID controls in the current adapter. History vectors/timers, orientation
limits, rear camera, replay and dynamic helpers are not exposed for authoring.

## Qualified static rule

Controlled frame: target entity+50 points to frame; +2C up, +3C forward,
+4C world origin. For flat upright forward F and origin P, first update with
pitch disabled and no dynamic helper/history correction:

```
target = P + F * DistFront
eye    = P - F * (DistBack + followHalfLength)
eye.y += DistUp + followHeightExtent
up     = (0,1,0)
```

This is checked against ORIGINAL 0052C6D0 instructions and 004895F0 matrix writer,
including their vector helpers. Only timer reference/due result and renderer
camera-array services are mocked. Original return/stack ABI, eye/target/up and
orthonormal basis/position agree for 16 cases (four extent pairs × origin,
translated origin, yaw90, yaw−35). Four actual imported/stock models are separately
CPU-replayed. No live engine process, terrain, speed or D3D device is emulated.

Measured source terms, metres (stored bounds, not direct camera controls):

| Vehicle | Half length | Height extent |
|---|---:|---:|
| Stock Megane | 2.085821 | 1.489636 |
| Subaru actual qualified race resource | 2.554397 | 1.780541 |
| Lancer current emitted race resource | 2.619833 | 2.019470 |
| GT4 Pajero current emitted race resource | 2.619833 | 1.793130 |

Lancer follow0 source DistBack=3.5 / DistUp=.65 gives static original eye
(0,2.669470,-6.119833); isolated custom inputs 2.25/1.50 give
(0,2.15,-5.75). Both look at (0,0,14). The source-bounds contribution helps
explain high imported-sedan framing; it does NOT prove the entire live problem
is inherited donor settings. Actual target origin, suspension, dynamic history
and camera-mode effects require matched gameplay comparison. No body/wheel/
collision/physics change is made to achieve the comparison.

## Projection and dynamic boundaries

The Previewer uses source FOV and its existing D3D9 perspective implementation,
with explicitly approximate linear aspect scaling. Native final D3D8 projection,
FOV overrides, clip planes and display behavior are not qualified. Illustrative
frustum uses aspect1.5/range1.5m and a diagnostic grid, not native clip planes.
Camera position/target markers are in the same model coordinates as the rest-pose
wheel assembly. World movement/suspension is not simulated. Native follow-array1
pitch=true is shown read-only; the static rule intentionally does not claim its
pitch/history behavior. No arbitrary speed slider is substituted for evidence.

Free Inspection, bookmarks and selection remain separate from Gameplay Preview.
G switches modes; mouse orbit/pan/zoom is locked in Gameplay Preview. Reset clears
only this CarID's override, including inherited roster-profile references.

## Safe authoring and ABI

Existing V-SDK2 getter hooks only at 0052C652/0052C65E/0052C677. Require matching
CarN participant→physical CarID, canonical family model key, exact source model
SHA and all original bound bytes. Immutable camera-only bounds are returned;
source bounds and unrelated IDs sharing the model pass through. No global XML,
physical collision or actor transform mutation. No cached owner pointer. CarID0,
noncanonical names/slots, absent broker or model mismatch fail to passthrough.
Delivered combined candidate passes 18 original-initializer/adapter CPU cases,
including register/stack/x87 checks. Live mode switching/rear/split/replay and
owner teardown remain gameplay gates; no new camera runtime mechanism was added.

## Reproduction

Use `tools/validate_game_camera_native.py --exe PRIVATE_EXE --output PRIVATE_JSON`
with Unicorn available. `tools/validate_game_camera_windows.py` takes a qualified
private Workshop `--reference`, current `--viewer` and fresh `--output`. It tests
actual GUI actions and GPU/event paths, never launches the game. Camera Lab Core
methods `camera_lab_inspect`/`camera_lab_export` share exact source staging with
the GUI. Read-only Subaru inspection uses current frozen resources and exact
repeated frontend wheel transforms; it does not turn a family view into an
editable registered addon or change its frozen baseline.
