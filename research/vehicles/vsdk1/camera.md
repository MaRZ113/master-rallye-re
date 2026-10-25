# V-SDK1 camera research: native follow extents and safe next adapter

## Outcome

The sedan camera is **not controlled by a single fixed global height**.
The native follow camera adds model-derived height and half-length to authored
camera distances. Lancer's full antenna-inclusive height is 2.01947 m, versus
Megane's 1.48964 m. Its race bounds also retain Navara's 2.61983 m half-length,
0.37203 m beyond its rendered half-length. Both differences enter the follow
camera independently of handling. This is an established native mechanism and
offline asset difference, not yet a complete gameplay diagnosis of the user's
particular selected camera, live target, terrain and renderer settings.

No camera hook, global camera XML edit, renderer modification or physics change
is included in the main combined roster. A per-CarID camera override is not
qualified yet. The safe concrete deliverable is a reusable read-only diagnostic
with original-x86 initializer replay, plus the narrow adapter plan below.

## Evidence identity and chain

REA Ghidra 12.1.4 opened original PC x86 `MRallye.exe`, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
No original binary was written. Compact evidence and original instruction dumps
are in `.research-output/vehicles/vsdk1/camera/`.

| Native component | Finding | Evidence |
|---|---|---|
| 004B7620 | Camera manager owns embedded geometry-intersection, acceleration, zoom and smoothing helpers; selects `Camera/Setup` or `Camera/SplitSetup` | REA `ev_3297f08aee2e737d8f4722effd09ee9019699c57bf5fbab938e34754308413e4` |
| 004B91E0 / 004B8C10 | Reads/writes shared follow records of 44 bytes and fixed records of 24 bytes | `ev_0bf1933de9526c1b61335c1fcde31ffbdd72d66c54554be957eb2c7a9cdbe62a`, `ev_4903c0d4f3705cead4ab0b36928c958b2c39189eac6bb7209bd26de843562682` |
| 004B98E0 | Copies selected follow parameters; explicitly sets `aiFollowCamera+3C` = true (`Use Model Extents`) | `ev_35a7f80e64a1b0fc48c5c0e333c3fdeef9fd2a37121b1c7a3501bcee7fb9f93a` |
| 0052C3E0 | Native serialized names confirm `DistFront`, `DistBack`, `DistUp`, pitch, smoothing and `Use Model Extents` | `ev_5a102e70958e0457ce55f0944a02db6f64eeabcd76f96c63a362bb04b04e08f8` |
| 0052C630..0052C6C2 | Extents initializer calls original model bounds getter 004F5BC0 three times, then stores derived length/height | exact bytes `ev_cf79e8f6613961c8da6c3ab737b4398230422b44b14d6c07f2371b62cfc49ec8` |
| 0052C6D0..0052CCFE | Follow updater reads target transform from argument+50, basis/position fields, and adds derived extent terms at 0052CB37 / 0052CB9F | same bounded original bytes, independent Capstone disassembly retained |
| 004B7DE0 | Update dispatches active camera/helper components against the resolved target and switches modes | `ev_3ab750ef065775853d5dc8032c54a150c90ecee0646c46c9d9fc340eb475a8ec` |

Ghidra decodes the two follow entry points but has not defined them as functions
in its default database. `inspect_native_instruction` confirms decoded entry
bytes and vtable references at 00691CD4 / 00691CD0. Therefore this report uses
the actual disassembly and execution replay, rather than fabricated decompiler
output for those entries. Existing General renderer camera research is reused
read-only; it is not evidence of a new in-game pass.

### Extents arithmetic, including the stack detail

Native loaded bounds are 44 bytes: centre XYZ, radius, radius squared, minimum
XYZ at +14..+1C, maximum XYZ at +20..+28. This is the already-qualified FIX1
layout, not the file marker layout.

With `Use Model Extents` enabled, original initializer yields:

```text
follow+40 = abs(maximum.z - minimum.z) * 0.5
follow+44 = abs(maximum.y - minimum.y)
```

At 0052C682 `[esp+10]` holds min Z. After the intervening `push edi`, the same
printed stack displacement at 0052C699 instead addresses min Y. Ignoring that
stack shift would produce an incorrect mixed-axis explanation. Twelve original
x86 replay cases over six real models confirm both values, enabled/disabled.
Only the model lookup and following update callback are stubbed. This is CPU
evidence, not execution of a complete live camera system.

## Current models compared under the same static rule

The actual emitted combined candidate-30 resources were inspected, together
with protected stock resources from `Data.sma_unpacked`. Private report:
`current-comparison.json` records paths, SHA256, full minima/maxima and replay.

| Model | Native half-length | Native height | Render half-length | Render height |
|---|---:|---:|---:|---:|
| Stock Navara race | 2.61983 | 1.62327 | 2.57494 | 1.61146 |
| Stock Megane race | 2.08582 | 1.48964 | 2.06486 | 1.48964 |
| Stock Pajero race | 2.18842 | 1.68474 | 2.15663 | 1.61603 |
| Lancer race | 2.61983 | 2.01947 | 2.24780 | 2.01947 |
| Lancer frontend | 2.14373 | 1.98476 | 2.14373 | 1.98476 |
| Subaru race | 2.55440 | 1.78054 | 2.55440 | 1.78054 |

Lancer's top three unique race vertices are within ~5.4 mm laterally near
Z=-0.42 m at Y=1.93628 m. Its 99th percentile vertex Y is only 1.32080 m.
This geometry is consistent with the thin roof antenna visible in source
previews; the mathematical fact is that a tiny upper feature drives the full
height term. Percentiles are diagnostic only: **the SDK does not discard that
feature or automatically replace camera extents with a percentile**.

The race length inflation is consistent with preserved donor collision bounds;
its height is not donor height. Simply rewriting the spatial footer or changing
physics would affect unrelated consumers and is not the proposed repair.
Likewise a uniform model translation cannot change these extent spans. Lowering
the visual body alone does not lower this automatic height term.

## Global parameters, modes and unresolved dependencies

Protected `DataGame/Cameras.xml` has shared `Camera/Setup` and split-screen
`Camera/SplitSetup`, without vehicle names or CarID keys. Single-screen follow
records 0/1/2 specify:

| Native key | Follow 0 | Follow 1 | Follow 2 |
|---|---:|---:|---:|
| Dist Front | 14 | 14 | 10 |
| Dist Back | 3.5 | 4 | 3.5 |
| Dist Up | .65 | .65 | .70 |
| UsePitchSystem | false | true | false |
| Pitch Limit deg | 50 | 80 | 50 |
| Smooth Camera Multi | .30 | .70 | .30 |
| Body Dir Multi | .30 | .30 | .30 |
| FOV | 90 | 90 | 90 |
| Accel | true | true | false |

All three use minimum rotation .1 / maximum 5 degrees. These are native defaults,
not empirically verified safe tuning ranges. `Dist Front` is a native parameter
name; it must not be relabelled a generic look-at offset without tracing it.
Fixed records independently expose type, forward/back, up/down, right/left,
invert-look, flatten-direction and FOV. Manager switch values also create
follow, fixed, track/marker/flyby producers; a UI mode-name mapping is not closed.

The accelerator helper exposes MaxDist/MinDist/SpeedMulti/DistMulti, while the
geometry intersector defaults to entity name `landscape`. Their construction
and invocation are proved; precise response curves and full terrain/obstacle
behavior have not been replayed. The follow updater consumes target transform
and its own history, pitch and body-direction controls. No direct dependency on
mass, CG or spring constants was found in this reviewed follow initialization
path. Physics can still influence target motion and body attitude indirectly.
Acceleration/braking/jumps/collisions therefore require controlled captures,
not a claim that a screenshot isolates one parameter.

General renderer research establishes final CameraFrame interpolation, CPU
visibility, current/previous poses and projection. Source FOV uses the stock
linear aspect rule: angle unchanged for portrait, otherwise angle*height/width.
FOV90 is not 90-degree vertical FOV at widescreen. The renderer's optional FOV
and free-camera controls may override presentation and must be held fixed in
comparisons. No renderer setting was changed here.

Frontend converges to a separate presentation camera (previous General research
observed source45); replay/track cameras have other producers. The current
follow-extents result must not be projected onto every replay/frontend mode.
No equivalent live stock/Lancer capture was taken in this pass.

## Proposed camera-profile contract and smallest safe implementation

Do not expose unverified generic target offsets or smoothing-in-seconds.
An initial schema should retain native meaning:

```json
{
  "profile_version": 1,
  "physical_car_id": 28,
  "policy": "native_follow_override",
  "presets": {
    "follow_0": {
      "dist_front": 14.0,
      "dist_back": 3.5,
      "dist_up": 0.65,
      "fov_source_degrees": 90.0,
      "smooth_camera_multi": 0.3,
      "body_dir_multi": 0.3,
      "use_pitch_system": false,
      "pitch_limit_degrees": 50.0,
      "accel": true
    }
  }
}
```

This is a **proposal**, not an accepted runtime schema. Future validation must
reject unknown fields, nonfinite values, unsupported modes and conflicting
profiles. Numeric bounds should first admit qualified stock presets; wider
authoring bounds must be explicit SDK safety policy, not claimed engine limits.
Omitted profile means exact stock passthrough. Reset means omit the override;
comparison uses two sealed candidates and original setup values.

There are two distinct possible scopes:

1. A small model-specific camera-only extent adapter can intercept only the
   three 0052C630 getter calls. Match canonical model resource plus all 44 source
   bounds bytes, return immutable camera-only extents, preserve getter flags,
   registers and source memory. This resembles the existing shadow-only adapter
   but must remain a separate callsite scope. Explicit height/length targets
   would be authored camera calibration, not recovered GT4 values. It supports
   stock/addon models by explicit opt-in, but **is not per-CarID isolation when
   two IDs share the same model**. No such wrapper was installed in this pass.
2. True per-CarID presets need a validated camera-manager target participant →
   current physical CarID binding, then instance-local parameter copy at mode
   creation/reconfiguration. The shared `Camera/Setup` broker object must not be
   mutated. Confirm target lifetime, switch/rear-view, split-screen, replay,
   teardown and replacement ownership before enabling any write. Model-only
   matching cannot satisfy this contract silently.

This owner/CarID binding and same-scene gameplay comparison are the remaining
gates before an isolated experimental camera candidate. They do not block the
main SDK roster. A future Camera Studio should author this qualified contract
and read diagnostic snapshots; no GUI is warranted yet.

## Reproduce and test

```powershell
# PYTHONPATH=src;tools;.;.research-output/vehicles/scale1/python-tools
python tools/vehicle_camera_diagnostics.py --model PRIVATE_CAR_DX --model PRIVATE_STOCK_CAR_DX --cameras PRIVATE_CAMERAS_XML --exe PRIVATE_ORIGINAL_EXE --output NEW_PRIVATE_REPORT.json
python -m unittest discover -s tests/synthetic -p test_vehicle_camera_diagnostics.py
```

Three fixture-independent tests pass (translation-invariant extents, invalid
bounds/executable rejection, setup inventory and duplicate/DTD rejection).
Twelve enabled/disabled original-initializer cases pass on six actual models.
Nothing writes game assets, physics, EXE, DLL or runtime memory.

For human comparison: use stock Megane, Navara/Pajero, Subaru and Lancer on the
same track/start position, same one-player setup, same camera index, display
aspect and renderer options. Capture stationary, acceleration, coast/brake,
one bump/jump and collision, then re-entry. Record selected camera, physical
CarID, target transform, native +40/+44 terms, current/previous pose and source
FOV. Frontend/replay must be separate cases. Only this closes whether the
qualified extent differences account for the entire perceived high camera.
