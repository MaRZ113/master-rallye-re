# V-PHYS1 — independent physics and suspension foundation

Status: **initial Lancer candidate ready for human testing; offline qualified**.
Repository/branch: `master-rallye-re-vehicles` / `research/vehicles`.
Visual references remain frozen: Subaru V-MESH4.13 and Lancer V-LANCER6.
No game launch, EXE/DLL replacement, capacity expansion or Randomizer changes.

## Result

- Optional `physics-profile.json` now feeds the ordinary addon project build
  and existing external runtime compositor. Edits are typed, source-pinned and
  restricted to the addon's independent named family.
- A reproducible Lancer revision changes **one resource, vehicles.xml**, with
  seven declared field edits. All other 227 immutable resources match V6;
  every model/texture, collision, crew, UI resource, native patch operation,
  identity plan and native damage payload remains byte-identical.
- Controlled A/B/C packages isolate donor behavior, horizontal/radius fit and
  vertical attachment fit. No source reconstruction or mesh offsets were used.
- The SDK Previewer can now derive wheel attachment frames from generated MR
  physics XML. This is explicitly a static attachment diagnostic, not a solver.

## Evidence-based data path

Original retail EXE SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

1. `DataGame/Game.xml` loads named vehicle data. `vehicles.xml` contains base
   dimensions/chassis/engine/suspension/damage values plus shared tyre tables.
   `Modifications.xml` contains separate Player1/Player2 setup deltas.
2. `0044ED50` resolves selected absolute CarID through its registry record,
   obtains the family and calls `00493E30` / `00493770` for
   `Vehicles/<family>`. Native type IDs, absolute CarIDs, class-local indices
   and participant indices are separate concepts.
3. Optional human setup is resolved by `0044E400` / `00493FD0`. Thirteen
   setup deltas are added directly to their base fields in `0044ED50`.
   They are **not normalized frontend slider values**. Saved player setup can
   override initial defaults on subsequent sessions.
4. `004938C0` / `00493600` publish `Vehicles/CarN` for participant N. Group
   writers correspond to the readers in `parameter-map.json`.
5. Physical construction is independently traced through `0043F020` →
   `0043E4C0` → `00493A40` → `00442D40`. It reads the participant namespace,
   creates the chassis/controller and four 0x188-byte wheel records, and
   registers collision through `0043A800`. The old `004BC590` spline observer
   alone is not used as proof of this physical constructor.

Classes T1/T2/T3 select registration/list placement; physics values are named
per family and copied per participant. There is no new per-class physics-table
patch in this work. The runtime remains the established ID26/T1 + ID27/T2 path.
Separate SCALE29/30 experiments remain frozen; they are not combined here.
Thirty-five XML families in the inventory do not imply 35 selectable cars.

## Parameter map and units

`parameter-map.json` inventories 149 distinct field paths across 35 named XML
families, types, group readers/writers and component-wise stock min/max values.
It includes XML-only families. Stock ranges are observations, **not native
clamps, safe tuning bounds or exhaustive solver qualification**.

| Fields | Verified relation / consumer | Unit and qualification boundary |
| --- | --- | --- |
| Dimensions/* | Reader `0049B0C0`; wheel initializer `00440770` | Model/world length units, metre-consistent with source conversion. Track/base directly generate anchors; Length/Width/Height are not render bounds or automatic hull fitting |
| WheelBase / TrackWidthFront,Rear | Anchor Z = ±base/2; X = ±track/2 at `004407FC..004408C0` | Exact native instruction and CPU replay proof |
| WheelRadiusFront,Rear | Copied to wheel +0x3C; also read by `0042D0D0` drivetrain/speed path | Physical radius, independent of wheel.dx vertex radius |
| RideHeight | Anchor Y = **−RideHeight**, front +0x110 / rear +0x17C in parameter block | Signed model-origin datum. Not a ground-clearance measurement or guaranteed settled hub Y |
| TotalMass / UnsprungMass | `0043A370`: sprung mass = TotalMass − 2×(front + rear unsprung masses) | Mass units consistent with kg; reject nonpositive sprung mass |
| CentreOfGravity | `0043A4A0` transfers XYZ; `00440770` also uses its longitudinal component for corner masses | Model-relative XYZ, not a visual mesh translation. Initial corner-mass distribution divides CG.z by **Dimensions/Length**, not wheelbase |
| MomentOfInertia, UseCuboidMOI | `0043A390` → chassis inertia setup | With flag false: each diagonal = sprung mass × input component². Input is a gyration-radius-like quantity, not an already computed inertia tensor |
| ToeIn / Camber and jounce derivatives | `00440770` multiplies source angles by ~π/180, mirrors signs by wheel side | Base angles are degrees; native wheel fields are radians. Full derivative/solver response not yet replayed |
| SpringRate / DamperRate / arm ratios / travel | `0049E970`, `004A01D0` → initializer +0x60/+0x68, ratios +0x64/+0x6C, bounce/droop +0x4C/+0x50 | Rate units are SI-consistent N/m and N·s/m, not independently calibrated force-law units in this phase. Native copy and sensitivity verified; road response/settling remains human testing |
| Steering/* | Reader `0049C950`, controller construction `004445A0`, front-wheel control | MaxSteer/SteerOffset and speed-dependent steering are real fields; full speed curve and limits remain unqualified |
| Engine/*, gears, torque curve | Reader `0049CEF0`; engine setup `0043C350` | RevLimit/IdleRevs multiply by 0.10471967 (RPM→rad/s); shift thresholds multiply by rev limit ×0.01. TorqueEntry axes are source curve coordinates, not assumed RPM/N·m. Existing array sizes are preserved |
| Brakes / drivetrain | Chassis brake torques enter wheel +0x114/+0x118; engine bias/LSD/diff through `0043C350` and helpers | DriveType accepts existing 0/1/2 values; internal remap observed. No unsupported differential or modern tyre model is invented |
| TyreType / Vehicles/Tyres/* | String is loaded; shared tyre/surface construction through `00441B20`/`00441B80`; Surface.xml defines global surface types/friction | Private per-addon compound-table routing is not qualified. Only existing tyre prefixes are admitted; shared tyre tables and Surface.xml are never edited by a profile |
| DamageParams/* | Group reader `004A1A30` and existing damage/controller paths | Vehicle damage settings are independent from the DX contact hull and rendered deformation/coverage mechanism |

Two useful engine limitations were verified rather than corrected speculatively:

- `UseCuboidMOI=True` at `0043A390` computes products
  `sprung_mass × (L×H, L×W, W×H) / 12`, rather than a textbook squared-sum box
  tensor. Instructions and isolated CPU replay agree. Lancer keeps false.
- The wheel initializer unconditionally copies the **front** suspension
  application-point offsets into all four wheel records. Rear values are
  loaded into the parameter block, but are not used by that initializer.
  This is not a claim that every possible later consumer ignores them.

`0043F890` performs two substep sequences with constant float bits 0x3C888889
(~1/60). Outer scheduling/real-time frequency and complete contact integration
were not qualified; no live solver hooks or timing changes were introduced.

## Lancer cause and controlled changes

The source-qualified V6 rest assembly already puts hubs at
X=±0.745, Y=0.18535, Z=±1.255, and its wheel's radial envelope is 0.32535.
Navara initialization places attachments at ±0.85, −0.05, ±1.4 with radius 0.38.
This explains an initial 3D attachment mismatch of ~0.296 m. It is not a reversed
wheel mesh or an error to conceal by moving the shared spinning wheel model.

| Parameter | V6 donor | V-PHYS1 fitment |
| --- | ---: | ---: |
| WheelBase | 2.80 | 2.51 |
| TrackWidthFront / Rear | 1.70 / 1.70 | 1.49 / 1.49 |
| WheelRadiusFront / Rear | 0.38 / 0.38 | 0.32535 / 0.32535 |
| RideHeightFront / Rear | 0.05 / 0.05 | −0.18535 / −0.18535 |

Negative ride-height data is an explicit conversion between source model origin
and native attachment coordinates. It is outside the observed stock range
[0, 0.15], but the exact initializer accepts it without clamping. No assertion
of full-solver stability or settled ground clearance follows from that fact.
The CPU-replayed anchors agree with source rest hubs to float32 precision.
Nominal visual and physical radius differ by less than 0.1 µm; polygonal vertical
tyre extrema are slightly smaller than the radial envelope, as expected.

Mass, CG, inertia, springs/dampers, travel, toe/camber, engine/gearing, brakes and
tyre selection remain donor-derived. This is a fitment foundation, not a balanced
or authentic GT4 Lancer handling setup. Radius changes can affect effective
gearing/braking even though torque and gearbox fields are unchanged.

Collision is still the V6 Navara tag101 hull: AABB approximately
X=[−1.0326,1.0296], Y=[0.0046,1.5541], Z=[−2.8630,2.3767]. It is visibly broader
than parts of the Lancer and may cause early side/front/rear contacts. It does
not supply the mismatched wheel anchors. No automatic fit to render bounds was
performed: antennas, spoiler and wheels make that unjustified. Existing SDK
translation/positive scale operations from re-blend remain available, with the
same imported-scene collision-preservation boundary. Contact-hull fitting and
full dynamic suspension/contact qualification remain explicit follow-up work.

## Validation

- 651 synthetic tests: no errors/failures, one existing private-fixture skip.
- Eleven one-variable native initialization/chassis checks: dimensions, radius,
  ride-height sign, rates/travel, mass and both inertia branches.
- Exact native wheel-prefix replay for Navara, Pajero and all A/B/C profiles.
- Independent profile tests cover typed values, hash/identity/name failures,
  invalid mass/dimensions/curves, array-count rejection, two isolated families,
  additive player defaults and runtime recomposition.
- V6 without a profile reproduces all 86 generated game resources byte-for-byte.
- Final rebuild workflow reproduces the independently built C game resources.
- Final C changes only declared Lancer XML values; 228 immutable resources checked,
  227 identical. Native code/payload, identity, damage ownership and UI unchanged.
- Thirty-six native damage replay impacts retain the V6 result: XYZ/RGB native,
  no split coincident positions, coverage alpha losses 91→0 with the same bridge.
- Frozen V6, Subaru, SCALE29 and SCALE30 pass their existing sealed launcher checks.
- Installed EXE and graphics DLL hashes unchanged; all candidates pass verification,
  launch-environment and private allocation preflight. No game was launched.

Private evidence: `.research-output/vehicles/vphys1/`; Ghidra fallback project and
exports use ignored dot-free `scratch/phys1`. REA supplied original-byte/function
evidence; the fallback defined missing wheel-function boundaries in a temporary
analysis database. Decompiled C is not original source.

## Candidate / gameplay procedure

1. Optional A control: `candidate-control/Launch-V-PHYS1-control.cmd`.
   This reproduces donor behavior in the independent family.
2. Optional B isolation: `candidate-dimensions/Launch-V-PHYS1-dimensions.cmd`.
   Five dimension/radius edits, donor vertical datum retained.
3. Main C: **`final-fitment/Launch-Physics.cmd`**. Seven declared edits.

Use a normal small-roster race first, independently from SCALE experiments.
On flat ground inspect front/side/rear immediately and after settling. Check
wheel rotation/steering, full compression/droop on bumps, body-ground clearance,
braking, reverse and race re-entry. Compare stock Navara in the same package.
Check Lancer materials/crew/brake lights and coherent deformation after an impact.
Report which candidate, whether stationary or moving, and whether a setup was
saved. Existing Player1/Player2 setup deltas are a separate influence; do not mix
save files between these controlled trees. Original/frozen saves are untouched.

`previews/fitment-comparison.png` shows only static native attachment data.
It is not a gameplay screenshot or a simulation of spring sag.
Editable format and one-command rebuild: see `profiles.md`.

Source-only handoff: `.research-output/vehicles/vphys1/handoff/V-PHYS1-source.zip`
and its SHA256 file index. It contains this phase's source/configuration/docs/tests,
not extracted GT/retail assets, decompiler exports or runtime packages. It requires
the existing SDK checkout. No commits, push or publication were performed.
