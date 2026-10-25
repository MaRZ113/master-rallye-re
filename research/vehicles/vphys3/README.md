# V-PHYS3 — qualified ride-reference binding

Status: **ready for human gameplay validation**, not a completed race test.
Repository `master-rallye-re-vehicles`, branch `research/vehicles`.

## Cause and correction

The user confirmed that the screenshot was taken with V-PHYS2
`candidate-fitment-260`, at menu0/0mm. That control retains donor handling;
it is distinct from `candidate-handling-260`. This phase preserves both as
separate comparisons rather than assuming the same driving calibration.

The existing -0.15m ride reference did **not** activate in the race:
V-PHYS2 compared `Vehicles/LancerEvo4` with the bare native registry name
`LancerEvo4`. The `Vehicles/` prefix is added later by a different reader.
The original reference test supplied an invented prefixed name and missed
this error. Its arithmetic/ABI checks were valid, its runtime naming premise
was not. See [trace.md](trace.md) for original addresses and evidence.

V-PHYS3 adds explicit `ride_height_reference_binding: "registry_name"`.
The adapter matches the exact component including its terminator; it retains
the existing -0.15m correction, applied once after native player setup and
before participant publication. **No further -150mm is added.** Menu base and
initial player deltas remain0. Engine, AWD, gears, steering, brakes, mass,
springs, damping, wheel meshes, orientation, UI, crew and materials are unchanged
relative to each respective V-PHYS2 control. Collision declarations are unchanged.

Omission of the new binding reproduces the historical V-PHYS2 payload exactly
for frozen-package integrity. It is not recommended for new ride-reference
profiles. Preview/fitment tools now expose that legacy reference as inactive,
instead of silently rendering the intended correction as if it had executed.

## Native and geometric boundaries

At native publication, 0mm now gives physical RideHeight=-.15m, attachment
Y=+.15m. Native -150/+150mm endpoints map to physical -.30/0m respectively.
The existing solver, contact projection, gravity preload, jounce clamp and
wheel render transform are retained. Spring equilibrium is not approximated
as ordinary `m*g/K` sag. Wheel world attachment subtracts the body CG before
rotation; this is not justification for a visual body translation.

The2.60m adaptation remains the user-approved symmetric native WheelBase,
not a recovered factory dimension. The2.51m Handling control differs only in
that parameter. Arch circles remain geometric diagnostics, not source axles.
No individual longitudinal wheel offsets are added. The previous residual
arch asymmetry remains deferred rather than disguised.

For Handling260 at neutral, the fitted collision lower bound is+.02393m in
model coordinates. With an upright zero-jounce wheel/ground construction,
body-origin clearance is radius.32535 minus attachment.15 =.17535m, placing
that hull bound about.19928m above the plane. This is a static consistency
check only; real collision/contact, pitch, settling and landings are untested.
Full bump/droop and setup endpoints are not promised free of tyre/body clipping.

## Private candidates and recommended order

Under `.research-output/vehicles/vphys3/`:

- `candidate-fitment-260/Launch-Physics.cmd`: **first comparison**, preserving
  the actual `candidate-fitment-260` last launched by the user; only binding fixed.
- `candidate-handling-260/Launch-Physics.cmd`: independent V-PHYS2 Evo handling,
  unchanged except the binding correction.
- `candidate-handling-251/Launch-Physics.cmd`: equivalent corrected setup,
  nominal2.51m control; compare against Handling260, not the donor control.

Under `.research-output/vehicles/vaudio1/`, separately validated audio-only
controls retain the corresponding V-PHYS2 physics. Combined candidates add
the same single audio resource to the corrected V-PHYS3 profile. Names and
recommended launcher are listed in [the audio report](../vaudio1/README.md).

Use fresh candidate saves; do not copy old PlayerState files. Start at0/0mm
on a flat start, wait for settling and inspect both sides. Compare small
±30mm adjustments before endpoints, then bumps/full droop, steering, jumps,
landing, braking and reverse. Check coherent damage, crew, brake lights,
reflections on/off, Results and two race re-entries. Report the exact launcher,
setup values and stationary versus moving/jumping condition.

## Offline evidence

- 30 native registry→caller→adapter cases reproduce the old namespace failure
  and corrected match, including stock, prefixed and longer-name rejection.
  String-copy allocation is an explicit ABI stub; original field addressing
  and adapter instructions execute unchanged in Unicorn.
- Original force/drivetrain/engine/control replays and exact resource scope
  checks pass. Corrected Fitment260 retains all228 V-PHYS2 game resources
  byte-for-byte; corrected Handling260 likewise retains its own228 resources.
- V-LANCER6 rebuild reproduces all86 generated game resources. Frozen Subaru,
  LancerV6, SCALE29/30 and V-PHYS2 launchers verify.
- Full synthetic suite:674 tests, no failures/errors, one existing skipped
  private fixture. Final detailed counts and hashes are in validation-summary.json.
- Static Previewer captures compare the **actual legacy binding outcome**
  against corrected attachment frames. They do not simulate loaded suspension.

No original EXE/DLL writes, capacity changes, Randomizer edits, commits or
publication. Original hashes remain the qualified V-PHYS2 identities.

## Reproduce / reuse

```powershell
python tools/build_vehicle_physics_candidate.py `
 --project .research-output/vehicles/vlancer6/candidate-04/project `
 --profile research/vehicles/vphys3/fitment-260-physics.json `
 --output .research-output/vehicles/vphys3/my-new-fitment

python tools/validate_vehicle_fitment_binding.py --exe ../MRallye.exe `
 --profile research/vehicles/vphys3/fitment-260-physics.json `
 --output .research-output/vehicles/vphys3/my-binding-check.json
```

For another imported car, retain its explicit runtime family and chosen datum;
do not copy Lancer dimensions or offsets. Use the shared profile and builder,
exact original build admission and existing independent family allocation.
Optional native replay requires the existing Unicorn environment; ordinary
profile compilation does not depend on GT data or bundled proprietary assets.
