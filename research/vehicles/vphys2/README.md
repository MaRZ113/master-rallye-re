# V-PHYS2 — independent handling and controlled fitment

Two private candidates are ready for **human gameplay evaluation**, not gameplay
qualification. Worktree/branch: `master-rallye-re-vehicles` / `research/vehicles`.
Original EXE/DLL, Subaru, V6 visual source and SCALE29/30 packages are preserved.

## Launch and compare

Private root: `.research-output/vehicles/vphys2/`.

1. **`candidate-fitment-260/Launch-Physics.cmd`** — test this first. It keeps
   Navara handling, changes only independent Lancer dimension/radius/ride setup,
   and uses the user-approved **2.60 m MR wheelbase**. Donor collision unchanged.
2. **`candidate-handling-260/Launch-Physics.cmd`** — same wheel fitment and menu
   reference, independent Evo IV handling plus explicit core-shell collision fit.
3. Controls: `candidate-fitment` and `candidate-handling-02` retain the **2.51 m**
   nominal GT4 wheelbase. V-PHYS1 `final-fitment` remains unchanged.

Use each package's own fresh save tree. Do not copy V-PHYS1 PlayerState into V2.
Both final packages start with zero Lancer player deltas and no private saved
Lancer setup. After testing, saves legitimately override profile defaults.
Reset setup before comparing; a previously saved -150 mm is now an *additional*
lowering of the new reference, not the old equivalent stance.

## Why V-PHYS1 looked high at 0 mm

Native menu code `0044C780` establishes the ride fader as `[-.15,+.15]` metres.
`004847C0` displays `RideHeightReal * 1000`; `0044E490` saves **Real minus base**.
`0044ED50` adds that saved difference back before publishing participant CarN.
These are absolute menu values, not a zero-centred delta around arbitrary base.

The tested V-PHYS1 save contains front/rear **+0.18535 m** deltas. Against its
base `-.18535`, that means effective **0**, exactly the reported 0 mm. The
static source-anchor screenshot had used base-only data, so it did not describe
that actual effective setup. This is a specific saved-state/configuration
explanation; it does not prove the whole dynamic equilibrium is solved.

| Case | Menu mm | Saved delta m | Physical RideHeight m | Native attachment Y m |
|---|---:|---:|---:|---:|
| V-PHYS1 base only | -185.35 (outside fader) | 0 | -.18535 | +.18535 |
| Observed V-PHYS1 saved setup | 0 | +.18535 | 0 | 0 |
| V-PHYS1 selected -150 | -150 | +.03535 | -.15 | +.15 |
| V-PHYS2 neutral | 0 | 0 | -.15 | +.15 |
| V-PHYS2 lower endpoint | -150 | -.15 | -.30 | +.30 |
| V-PHYS2 upper endpoint | +150 | +.15 | 0 | 0 |

`ride_height_reference_m` explicitly rebases the physical initialization. It is
not a model translation, spring-arm trick, tyre resize or permanent saved edit.
The exact-family adapter at `0044F33E` applies the offset to the temporary
parameter block after native player deltas, before unchanged `004938C0`.
Named base/menu values remain zero. Stock and foreign families pass unchanged.
Original solver, wheel constructor, native deformation and damage bridge remain.
This is **one additional process-memory call redirection**, in the existing
sealed bounded extension, not an on-disk EXE patch or capacity expansion.

## Longitudinal wheel fitment

User identified front/back misalignment in the first V2 preview. Explicit
upper-edge samples from frozen V6 geometry give approximate circular centres:

| Arch | Z m | Y m | Radius m | Maximum radial residual |
|---|---:|---:|---:|---:|
| Front | +1.28754 | .14210 | .44069 | 3.17 mm |
| Rear | -1.32186 | .10890 | .45055 | 1.17 mm |

These **are not recovered axle transforms**: arch edges need not be circular
or exactly concentric with a wheel. They do expose why a symmetric +/-1.255 m
placement can look too close together. Their separation is 2.60940 m and their
common centre is -.01716 m. The source nominal wheelbase remains **2.510 m**.

With explicit user approval the final test profiles use MR `WheelBase=2.60`,
moving front/rear hubs +/-45 mm, through the original parameter only. Maximum
longitudinal difference from these approximate centres falls from **66.9 mm to
21.9 mm**. This is a **manual adaptation to the imported shell**, not a factory
Evo IV specification or a newly recovered GT4 measurement. Native symmetric
half-wheelbase cannot remove the remaining common-centre asymmetry. No separate
wheel offset, mesh translation or source-body edit was added. Compare the 2.51
controls in game before accepting the adaptation.

## Independent handling and collision

See [provenance.md](provenance.md) for source data versus manual settings.
The initial handling profile uses 1230 kg, independent gyration radii/CG,
45 kg unsprung corners, 36/33 kN/m springs, 2800/2500 damping, .20/.12 m travel,
native AWD, 7000 rpm limit, a six-knot source-informed torque curve, independent
brakes/LSD/steering and a manual five-forward MR gearbox. These values require
human tuning. No AYC, boost simulation, GT4 tyre solver or modern suspension
system is invented. Shared MR tyre/surface data remain unchanged.

Handling collision uses the existing validated scale/translation writers over
the donor tag101. The profile pins the exact car.dx hash and selects structural
draws; full render bounds (including antenna) are never an automatic target.
Topology, adjacency, descriptors, tag102 and all render attributes are retained;
areas and marker1339 bounds are rebuilt and validated. This remains an affine
Navara hull approximation, not reconstructed GT4 collision. Its changed contact
and damage locations require actual obstacle/grounding tests.

## Validation and limitations

- **656 synthetic tests**, no failures/errors, one existing private-fixture skip.
- V6 with no physics sidecar reproduces all **86** generated game resources.
- Final structural/resource regressions compare **228 immutable resources**:
  fitment retains 227 byte-identical; handling retains 226. Only Lancer XML and,
  for handling, its declared collision bytes differ. Menu/wheel meshes, all
  textures, UI, materials, crew and reflection/brake geometry are unchanged.
- Original x86 replay covers wheel/chassis initialization; 12 symmetric contact,
  compression/velocity/droop cases; 15 family/setup cases; three drive modes;
  14 engine torque/coast/rev-cut cases; brake and front-steer routing.
- Native spring code contains a gravity preload. At arm ratio one, zero jounce
  already supplies its configured corner load. `m*g/K` is **not** the settled
  suspension displacement here. See [native-map.md](native-map.md).
- Damage replay retains coherent native XYZ/RGB and coverage ownership (91
  losses without the established adapter, zero with it, no split coincident
  position groups). This does not test real collision impacts on a track.
- Frozen V6, Subaru and SCALE29/30 sealed launchers verify. No new capacity
  configuration is combined with physics. Source V6 assets remain reproducible.
- Original EXE SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
  d3d8 SHA256 `eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.

Preview captures are original DX/DXT renders with native parameter-derived
attachment frames, **not a suspension simulator or runtime telemetry**. Whole
vehicle pitch/roll, tyre deflection, contact settling, jumps and landings are
not solved. The new publication adapter itself remains gameplay-unqualified.
Approximate arch centring and the tested -150 mm observation are starting
evidence, not guarantees of ideal loaded stance or full-range clearance.

### Human test checklist

Use a flat start and standard small roster, with setup 0/0 mm. Inspect both
sides after settling, then front/rear wheel centres, toe/camber and steering.
Compare 2.51/2.60 with identical sliders. Try small +/-30 mm adjustments first;
the native endpoints are available but must not be assumed free of clipping.
Test progressive acceleration, automatic/manual shifts, reverse, straight and
turning braking, handbrake, bumps, full droop, jumps and landings. Check contact
at nose/sills/roof, coherent damage, then finish/Results/re-entry twice. Compare
stock Navara to detect unwanted shared changes. Recheck crew, reflection on/off
and native brake lights after an impact. Report package, slider values, whether
setup was saved, and flat-ground versus moving/jumping conditions.

Reproduction and editable workflow: [workflow.md](workflow.md).
Private evidence, previews and source-only archive live under the private root.
No commits, pushes, publication or Randomizer work were performed.
