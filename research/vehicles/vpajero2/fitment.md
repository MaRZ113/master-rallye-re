# V-PAJERO2: source-supported fitment controls

Status: two isolated combined-30 candidates pass offline validation and launcher
preflights. No gameplay qualification is claimed. Materials/performance controls
retain the previous physics; these fitment controls retain the previous 128-pixel
texture policy, so the effects can be tested independently.

## Cause: donor geometry parameters, not an assumed universal sag

Pajero `mits0038` was correctly assembled in the frontend from qualified GT4
source hubs, but its initial independent race physics family cloned Navara
without any overrides or ride reference. The two assemblies therefore differ.

| Quantity | GT4 source in MR convention | Current Navara-derived race setup |
|---|---:|---:|
| Wheelbase | 2.500 m | 2.800 m |
| Front track | 1.400 m | 1.700 m |
| Rear track | 1.380 m | 1.700 m |
| Front/rear hub Y | +0.1452 m | -0.0500 m |
| Tyre radius | 0.3652 m | 0.3800 m |
| Fresh Vehicle Setup height | source rest frame | 50 / 50 mm |

Source authority is the existing original GT4 Beta CHASSIS/RACINGMODIFY/
SUSPENSION/tyre row chain and traced normal-four wheel constructor, preserved
in `vsdk1/third/build-02/conversion-report.json` and `preview-profile.json`.
No hub was inferred from wheel-arch appearance, bounding-box centres or a
different GT version. GT4 source Z is converted by the existing shared adapter;
the table uses the emitted MR preview-profile sign convention.

Native unloaded attachment rule is the previously qualified
`004407FC..004408C0`: X = side*track/2, Y = -RideHeight, Z = axle*wheelbase/2.
At fresh 50 mm setup this gives errors of:

- Y: -195.2 mm on every wheel.
- X: 150 mm outboard front / 160 mm outboard rear.
- Z: 150 mm outward on each axle.
- Physical radius: 14.8 mm larger than actual converted wheel envelope.

Maximum 3D rest-hub mismatch is 293.60 mm. The existing native gravity-preload
force diagnostic has zero symmetric jounce for this donor, so applying a generic
`mass*g/springRate` sag correction would misdiagnose this known initialization
difference. Loaded suspension, terrain, pitch and tyre contacts still require
the user's gameplay test.

## A — minimal ride-datum control

Private launcher:
`.research-output/vehicles/vpajero2/candidate-ride-datum/Launch-SDK-Roster.cmd`

Editable project/profile:
`author-ride-datum/project/physics-profile.json` and
`ride-datum-physics.json` under the same private phase directory.

Adds only:

```json
"ride_height_reference_binding": "registry_name",
"ride_height_reference_m": {"Front": -0.1952, "Rear": -0.1952}
```

This value is derived from this car's source hub Y and the **unchanged fresh
50 mm setup**, not copied from Lancer. With native Y=-RideHeight,
the additive reference is currentHubY-sourceHubY = -.05-.1452 = -.1952 m.
At default 50/50 mm the published physical RideHeight becomes -.1452 m and
unloaded hub Y becomes +.1452 m. The menu remains 50/50 mm. Do not compare this
against Lancer's different zero-mm datum or silently reuse a prior save setup.

All donor dimensions, mass, CG, inertia, rates, damping, travel, steering,
drivetrain, brakes, tyre definitions and collision resources remain unchanged.
The controlled original-native spring, drivetrain, engine and control test
results are identical to the baseline. Ride reference changes the stance and
collision world clearance; these checks do not promise identical whole-race
handling. No new runtime hook or visual mesh translation was added.

This control deliberately leaves X/Z errors and the 14.8 mm radius mismatch.
Maximum residual rest-hub difference is 219.32 mm. It isolates the high stance
correction while keeping the donor's physical wheelbase/tracks/radii.

## B — optional source-dimension calibration

Private launcher:
`.research-output/vehicles/vpajero2/candidate-source-dimensions/Launch-SDK-Roster.cmd`

Editable project/profile:
`author-source-dimensions/project/physics-profile.json` and
`source-dimensions-physics.json` under the private phase directory.

Retains A's datum and independently changes exactly five `SdkPajero85` values:

```json
"Dimensions/WheelBase": 2.5,
"Dimensions/TrackWidthFront": 1.4,
"Dimensions/TrackWidthRear": 1.38,
"Dimensions/WheelRadiusFront": 0.3652,
"Dimensions/WheelRadiusRear": 0.3652
```

These are qualified source dimensions, not arbitrary per-wheel offsets. This
is explicitly a **physical geometry change**, which may change turn response,
weight transfer/contact placement and effective tyre gearing. It is not merged
into the default handling-preserving control. All mass, force, drivetrain and
control coefficients are retained, and their native helper tests remain equal.
There is no claim that unchanged coefficients mean identical handling.

Unloaded hubs match source within floating-point precision (~1e-16 m), and
physical radius matches the converted mesh within ~2e-9 m. The upright
zero-jounce body-origin clearance becomes .3652-.1452 = .2200 m, also the source
GT4 rest ride height. This is geometric consistency, not a reproduction of GT4
physics or proof of settled MR ride height.

## Collision, visual and setup separation

The retained Navara tag101 collision AABB remains:
X[-1.03259,1.02955], Y[.00457,1.55408], Z[-2.86299,2.37668] m.
Pajero render bounds are X±.98535, Y[-.04020,1.75293],
Z[-2.01489,2.06689] m. The donor hull reaches ~848 mm past the rear rendered
extent and ~310 mm past the front. This is independently recorded; no automatic
decorative-bound hull fit was applied to conceal it.

At zero jounce on a constructed flat contact plane, body-origin clearance is:

| Control | Origin height | Hull bottom | Visual tyre bottom |
|---|---:|---:|---:|
| Baseline | .4300 m | .43457 m | .01480 m |
| A datum only | .2348 m | .23937 m | .01480 m |
| B source dimensions | .2200 m | .22457 m | ~0 m |

These estimates are in the body model frame and exclude actual terrain/contact
integration. Suspension travel stays -100/+300 mm. Full travel/setup endpoints
are not claimed clipping-free. Body mesh, embedded source brakes, wheel meshes,
orientation, frontend assembly, UVs and materials are byte-identical. This phase
does not introduce a new render-only hub offset system or rebuild body-owned
brakes as dynamic unsprung attachments; such mechanics can require their own
future qualification if their source/native mismatch remains visible.

## Reusable diagnostics and preview outputs

`tools/diagnose_vehicle_fitment.py` now derives an **unapplied** source-rest
datum delta from four matched source/native hub rows. It rejects asymmetric,
ambiguous or excessive declarations. It also reports zero-jounce plane/body/
collision clearance and physical-versus-visual tyre bottom discrepancy.
It respects the existing effective setup, saved state and V-PHYS3 registry-name
binding; it never automatically tunes suspension or writes an asset.

New `tools/render_vehicle_fitment_overlay.py` produces a source-pinned side/top
SVG with source/native hub markers, physical/visual tyre circles and retained
collision AABB. Body triangles are a position-only backdrop, with explicit
alpha/contact/settling limitations. Five fixture-independent tests pass,
including mathematical sign/reapplication, ambiguity guards, source pinning,
deterministic valid SVG and explicit diagnostic boundaries.

Private `preview/` contains:

- `overlay-baseline.svg`, `overlay-ride-datum.svg`, `overlay-source-dimensions.svg`.
- Native fixed-function viewer scenes and setup/profile sidecars.
- `baseline-side-preset.bmp`, `ride-datum-side-preset.bmp`,
  `source-dimensions-side-preset.bmp`: inspected native viewer preset-3 captures.

The viewer captures show the lower stance and source-dimension axle alignment;
they are static attachment previews, not screenshots of gameplay equilibrium.
Earlier captures without the `-preset` suffix had unsuitable camera framing and
are not the accepted comparison images.

## Validation / exact preservation

- Both author builds pass (87 game resources each), and each combined roster
  still contains the frozen Subaru, Lancer and independent CarID29 Pajero.
- A preserves **364/364 combined baseline resources byte-for-byte**. Only
  source-bound native ride-reference/profile metadata changes.
- B preserves **363/364**; only `DataGame/vehicles.xml` changes, and parsed
  comparison finds exactly the five declared dimensions in `SdkPajero85`.
- No new resources, altered stock families, Subaru/Lancer assets, UI frames,
  audio samples, geometry, collision, textures or material resources.
- Original registry→publication ride-reference chain passes 30 cases.
- Original initialization/spring/drivetrain/engine/control replays pass for
  baseline/A/B. Force/drivetrain/engine/control outputs compare equal.
- Both complete launchers pass `--verify`, `--verify-launch-environment` and
  `--self-test-native-allocation`. No game was launched.
- Exact evidence: `preservation.json`, `roster-preservation.json`,
  `force-preservation.json`, `native-ride-reference.json`, `forces-*.json`,
  `fitment-*.json` and candidate `validation.json` in the private phase folder.

## Human test order

Use a fresh candidate save and **50/50 mm** Vehicle Setup for Pajero. Start with
A on the same flat start, wait for settling, then inspect both sides/front/rear.
Compare baseline → A; only then compare B as an explicitly different physical
geometry calibration. Try 20/80 mm height values, steering, braking, bump/droop,
jump/landing, collision/damage, AI Pajero and repeated race entry. Record exact
launcher and setup values. Check source brakes against wheels dynamically.

Retain the separate material/performance controls for timing/appearance tests;
do not ascribe their texture changes to these fitment controls. Original EXE,
graphics DLL and Randomizer remain untouched; no commit, push or distribution.
