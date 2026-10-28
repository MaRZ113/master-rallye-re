# 4Runner — stance, donor and material decisions

28 October 2026, v6.8 native-pilot preparation. These are measured source and
clean-retail comparisons, followed by explicit MR authoring decisions. They do
not establish settled Evo2 suspension, source-renderer parity or MR gameplay.
The immutable neutral source scene remains the restoration baseline.

## Inputs and evidence

The source is the qualified user-local Evo2 Toyota 4Runner SR5 Sport Package
2WD (2000), `TRUCK/T4RSR52.TRK`, not a claim of publisher-original installation
authenticity. Exact source identities and native static semantics are in
[EVO2_SOURCE_SEMANTICS.md](EVO2_SOURCE_SEMANTICS.md). In particular:

| Input | SHA256 |
|---|---|
| Original Evo2 `TRUCK.POD` | `5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41` |
| Original Evo2 `4x42.exe`, static analysis only | `ab8286e6bce8a1bf3769acddfeb0a79df2e5d43c72f462a89aa90f477951ec75` |
| `TRUCK/T4RSR52.TRK` | `d2ff6c5914e8102116e56704dac800442fed3adfbf42326c6b3311517e8bbcb4` |
| `MODELS/4RUNNERSR5.SMF` | `a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e` |
| Clean retail MR `Data.sma` | `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f` |
| Clean retail `DataGame/vehicles.xml` inside that archive | `a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0` |

MR measurements read members directly from the verified clean archive at
`D:/Game/Master Rallye/corpora/retail/Data.sma`, through the existing read-only
SMA reader and DX parser. Unpacked paths are convenient references, not an
independent authority over archive bytes. Five car/wheel/complete triplets
were parsed, plus six original SUV physics families. Retail Trooper has
configuration rows but no matching model members in this archive; no retail
Trooper geometry was invented or substituted from the accepted Demo project.

Private reproducible measurement data are in
`.research-output/vehicles/evo2-native-v68/stance/`: `source-vs-stock.json`
contains every resource hash, used-vertex bounds, selected configuration fields
and original static-attachment calculations; `derived-comparison.json` contains
the arithmetic below; `mr-anatomical-axes.json` contains original labeled draw
indices and their coordinate ranges. No proprietary asset bytes are included
in this document.

## Coordinate and origin decisions

The source TRK identifies right wheels at positive X, left at negative X,
front at positive Z, with Y upward and original light-position comments in
feet. The neutral scene preserves those values and derives right/up/front
as +X/+Y/-Z in metres.

The MR anatomical side is independently evidenced by original mesh labels,
not assumed from a graphics API. All five inspected retail SUV `car.dx` files
place `screenleft` entirely at positive X and `screenright` entirely at
negative X. For Terrano, original draw26 `screenleft` has X
`[0.689951599, 0.810051322]`; draw28 `screenright` has X
`[-0.810051322, -0.689951420]`. Original Newrav `screenfront` has mean Z
`+0.477598000`, while `screenrear` has mean Z `-0.636086792`.

Consequently MR left/right/front/up correspond to +X/-X/+Z/+Y. The UVS-to-MR
basis change is the proper 180-degree Y rotation `(-x, y, -z)`; raw Evo2 feet
map to MR metres as `(-x, y, z) * 0.3048`. Do not swap left/right wheel
identities after this conversion or apply a second mirror to make them look
symmetrical. Raw-to-MR includes one handedness reflection; its face winding
must be accounted for once by the bridge, while preserving source indices.

The raw front/rear hub Z values are `4.79/-4.09 ft`. Their midpoint is
`+0.35 ft = +0.106680 m`, whereas MR's qualified native attachment formula
uses symmetric `+/-WheelBase/2` longitudinal positions. The deliberate native
authoring datum is therefore **Z minus 0.106680 m after basis conversion**.
Apply this shared origin rebase to the complete assembly: body, embedded
frontend wheels, collision and all associated spatial profiles. The wheel
model itself stays hub-local. This changes the coordinate origin without
changing distances between any source body point and its hub. Record the
inverse in the authoring profile and retain the original scene untouched.

Do not apply a vertical body shift, wheel enlargement, or an automatic 1.05
factor. Native Evo2 evidence restricts the latter to its low-body-detail
branch; the selected high-detail2 static inspection does not use it.

## Measured stance and stock comparisons

All numbers below are metres. Physics columns come from original MR config;
4Runner values come from original geometry/TRK, not an equilibrium solver.

| Quantity | Evo2 4Runner | MR Terrano | MR Pajero | MR Landcruiser | MR Chevyblazer | MR Newrav |
|---|---:|---:|---:|---:|---:|---:|
| Literal/source or configured wheelbase | 2.706624 | 2.650000 | 2.400000 | 2.450000 | 2.750000 | 2.450000 |
| Front track | 1.505712 | 1.600000 | 1.650000 | 1.500000 | 1.700000 | 1.600000 |
| Rear track | 1.496568 | 1.600000 | 1.650000 | 1.500000 | 1.700000 | 1.600000 |
| Geometry radial tyre extent | 0.388704 | 0.390506 | 0.390506 | 0.390506 | 0.390506 | 0.390506 |
| MR configured tyre radius | — | 0.380000 | 0.380000 | 0.380000 | 0.380000 | 0.380000 |
| Hub below body-frame Y0 | 0.182880 | 0.000000 | 0.050000 | 0.100000 | 0.000000 | 0.000000 |
| Body/visible-stock width including mirrors | 1.831622 | 2.086228 | 2.036561 | 2.056011 | 2.107704 | 1.942616 |
| Body/visible-stock longitudinal extent | 4.657344 | 4.304961 | 4.313255 | 4.493164 | 4.613719 | 3.976564 |
| Highest body point above front hub | 1.611484 | 1.605954 | 1.484110 | 1.651697 | 1.652539 | 1.372198 |

The 4Runner body column uses the eleven native stock BODY-mask components,
including its roof rack. MR car columns include each original car's actual
draw-used vertices and their shipped equipment; these are reference envelopes,
not equivalent topology or catalog vehicle dimensions. MR `Dimensions/Length`,
`Width` and `Height` are physics parameters and must not be reported as measured
mesh extents. Source catalog wheelbase 8.78 ft converts to 2.676144 m and differs
from literal hubs 8.88 ft / 2.706624 m by 30.48 mm; preserve that warning and use the
literal hubs for this Source Fidelity assembly.

Source high-detail tyre width is 0.265000 m. Its vertical mesh extent is
0.388699m from the local hub; the marginally larger 0.388704 m radial extent
includes vertex discretization. The source tyre is only 1.802 mm smaller in
radial extent than the measured retail SUV wheel mesh. There is no evidence
for resizing it to a visually guessed wheel-arch gap.

The source stock body spans Y `[0,1.428604]`; source hubs lie at Y`-0.182880`.
Its lowest tyre plane is therefore Y `-0.571579` in that source body frame.
This gives a 2.000183 m highest-point-to-tyre-plane diagnostic envelope. Terrano's
analogous body roof-to-hub distance is only 5.530 mm lower than the 4Runner's.
The different underbody minima and arch shapes prevent interpreting a bounding
box difference as suspension sag or real-world ground clearance. In particular,
the source BODY-pass minimum excludes its separately rendered axle/light
systems. No source-runtime side image with a verified matching build and
settled pose was identified in this bounded local inspection. Owner neutral
screenshots and earlier MR gameplay images do not supply that missing Evo2
equilibrium measurement.

## Selected MR donor and reversible initialization

**Use clean retail Terrano as the physics baseline**, as coordinated with the
native-pipeline work. It is a supported four-wheel SUV family, its 2.65 m
wheelbase is 56.624 mm shorter than source, and its 1.60 m tracks require less
change than the 1.70 m Chevyblazer. Chevyblazer's wheelbase is 13.248 mm closer,
but that alone does not justify choosing the wider reference. Landcruiser
matches track more closely but is 256.624 mm shorter in wheelbase. These are
separate comparisons, not an unexplained compatibility score.

Clone Terrano to an independent runtime family; retain its 1500 kg mass,
35/33 kN/m front/rear spring rates, damping, gearing and other defaults initially.
They are **MR donor behavior**, not recovered Evo2 handling; the explicit
source-backed RWD adaptation below is separate. Do not import
a source dry-weight number without qualified units and consumer semantics.
Preserve accepted Heritage Trooper owner gameplay status and its separate
CarID29 roster; this donor choice does not modify that project.

The bounded Source Fidelity initialization, as delivered, is:

| Independent MR field | Value | Purpose |
|---|---:|---|
| `Dimensions/WheelBase` | 2.706624 | Literal source front/rear separation |
| `Dimensions/TrackWidthFront` | 1.505712 | Literal front hub separation |
| `Dimensions/TrackWidthRear` | 1.496568 | Literal rear hub separation |
| `Dimensions/WheelRadiusFront/Rear` | 0.388704 | Original high-detail tyre radial extent, rounded for the author profile |
| Per-family `ride_height_reference_m`, Front/Rear | 0.182880 | Preserve source static hub Y using the existing native reference publisher; retain Terrano XML/menu base RideHeight0 |
| `Engine/DriveType` | 1 (MR RWD) | Original TRK faxle.torque_pct0 / raxle.torque_pct1, mapped through the qualified MR enum; not the Evo2 drive_type enum |
| Assembly origin offset, native MR | `[0,0,-0.106680]` | Shared longitudinal datum rebase only |

Resulting MR hubs, ordered front-right/front-left/rear-right/rear-left, are
`[-0.752856,-0.182880,+1.353312]`,
`[+0.752856,-0.182880,+1.353312]`,
`[-0.748284,-0.182880,-1.353312]`,
`[+0.748284,-0.182880,-1.353312]`.

The geometry radius comparison gives approximately0.388704068m; the tiny
author-profile rounding is separate from source geometry and does not change
the original mesh. The ride reference is a family-bound native initialization
offset, not an overwrite of the donor menu RideHeight parameter. The final
RWD correction changes only the new family's Engine/DriveType0→1; mass,
spring/damper, gearing and other donor families remain unchanged. See
`pilot-delivery/rwd-correction-proof.json` under the native pilot evidence root.

The existing `addon_sdk.physics_model.wheel_attachments` records the native
relation `X=+/-track/2, Y=-RideHeight, Z=+/-WheelBase/2` at
`004407FC..004408C0`. Those are unloaded attachment data. Its qualified
`suspension_summary` is an upright symmetric force-branch estimate, with no
terrain/contact/full equilibrium integration. Terrano's arm ratios 1 give
zero estimated jounce in that limited branch; this cannot prove the candidate
will settle at those hubs in a race. Actual spawn, pitch, tyre contact,
steering and suspension travel remain owner D3D8 gates. Any subsequent
vertical stance tuning must be an explicit versioned MR-only edit with
before/after evidence and Restore, never a correction baked into the source.

Collision must use the same basis/datum and fit the selected body envelope.
Do not blindly clone Terrano collision geometry or reinterpret its common
3.5/2.0/1.5 physics dimensions as the original 4Runner hull. Any SDK-generated
collision or crew fitment is new MR authoring and must be labeled accordingly.

## Material and feature dispositions

| Source evidence | Initial MR disposition | Qualification boundary |
|---|---|---|
| Body material references original body TIFF, raw reflective 1 / transparent 0 | Original diffuse/UVs with qualified MR paint/reflection services | Reflection is an MR approximation; original bump shader is unsupported |
| `GlassE` and `GlassI` are distinct stock meshes with raw transparent 1; GlassE also reflective 1 | Keep their identity; explicit MR glass authoring may assign bounded native glass/damage roles | Raw source flags do not recover opacity, broken textures or damage zones automatically |
| Body indexed TIFF has 8+8 stored samples and unspecified extra sample 0 | Preserve both samples and 16-bit palette; neutral diffuse cache uses explicit opaque coverage | Unspecified sample is not alpha, tint mask or permission to erase geometry |
| Bump TIFF has four samples with no ExtraSamples tag | Preserve whole original and all raw channels; omit unsupported bump mapping | Fourth sample is not inferred alpha or native MR reflection strength |
| Original `Tire` material transparent 0 / reflective 0, separate rim `Wheel` reflective 1 | Tyres opaque, no environment pass; rim reflection only through qualified MR controls | Source wheel diffuse/UVs preserved; no generated replacement tyre/rim required |
| All six 08/12/16 L/R wheel resources are distinct source records | Preserve all; select 16 L/R as explicit inspection/native-pilot detail | Detail suffix is not wheel diameter or proof of original graphics defaults |
| Native BODY stock mask selects 11 components, including `RfRack` | Preserve that stock selection; retain other nodes as source records | Axle/light auxiliary passes are unsupported, not absent original geometry |
| Original light meshes and source lamp records exist | Preserve provenance; only explicit qualified MR brake/lamp authorship may enable effects | No automatic mapping from an object name to rear-brake state or rotor glow |
| Nine original color records | Retain exact records; one immutable source diffuse appearance initially | No synthetic recoloring is labeled as an original source colorway |
| No qualified original MR crew/collision/damage data in this cross-game scene | Optional explicit SDK enhancements only | Never report these as original Evo2 source behavior |

Keep diffuse pixel content, original UV associations and unknown material fields
visible in the source provenance. The source glass currently looks dark under
the deliberate opaque neutral cache. That is a known preview interpretation,
not a recovered original shader and not evidence that the glass geometry is
wrong. MR material edits belong to the separate Source Fidelity authoring
profile, with source/target A/B capture and exact Restore. A Classic recipe,
bulk colorway conversion and other vehicles remain outside this pilot.

### Pane selection is narrower than a material or object name

Original `GlassI` includes interior door surfaces down to Y1.32438ft and
headliner surfaces, not only transparent panes. For example its triangles28–37
have predominantly downward roof normals; `GlassE` triangles58–69 include
predominantly upward roof surfaces. Assigning constant translucent alpha to
both whole objects would make some opaque interior/roof geometry transparent.
Their unspecified source texture channel cannot resolve that policy by itself.
Use explicitly inspected pane triangle selections and preserve the remainder
with an opaque interpretation. Front windshield candidates are source
`GlassI` triangles7–18 and `GlassE` triangles16–31, with inward/outward source
normals respectively; final source-qualified selection belongs in the hashed
native-state recipe. Side pane/frame boundaries require the same inspection.
The selected GlassI/E geometry reaches only aboutZ-0.746ft, while the tail is
aroundZ-7ft; these objects do not establish a rear-window pane. Do not invent
a breakable rear zone merely to populate every MR label.

### Exact side-specific rolling wheel route

The pre-existing auxiliary mechanics API cannot substitute the source wheels:
it calls the original wheel registration, adds separate instances, and
deliberately excludes wheel spin through its generic interpolator. Reusing it
would leave a normal wheel plus a nonspinning auxiliary wheel.

The bounded `tools/vehicle_wheels_native.py` selector instead changes the model
key on the **same original wheel render state before original registration**.
Static Ghidra analysis of the exact clean retail executable confirms:

- Original callsite `0043F22C` passes vehicle key, native wheel index and the
  existing wheel entity to `0043ED00`.
- Native model setter `004F5B70` changes state+0C, disposes any old cached model
  through its deleting destructor and clears state+74.
- Original registration publishes the same wheel scene name to its physics
  wheel record and installs `00448570` with spin-interpolator vtable00690170.
  The selector does not add an entity, alter physics or substitute a controller.

Four extensionless resource keys use native +Xfront/-Xfront/+Xrear/-Xrear order,
which corresponds to source left/right/left/right after the qualified basis
conversion. Each emitted wheel-local resource must include the inverse of the
native side rest rotation; native +X applies a proper180-degree Y rotation.
That compensation is a derived authoring transform, not a source mirror or hub
adjustment. Preserve both distinct original sides and all six source variants.

If an accepted Lancer auxiliary-mechanics wrapper already occupies the same
callsite, the selector admits it only after rebuilding its generated payload
from the pinned prefix and family report and comparing the exact bytes/entry.
The selector delegates to that verified wrapper; disjoint family guards preserve
Lancer mechanics and still call the original registration once. Unknown hooks
and overlapping replacement/mechanics families fail closed. The build manifest
must record the final composed callsite replacement and retain both bindings.

Six source-only synthetic tests pass for native-order routing, ABI/return
preservation, profile/path/index guards, bounded output, exact delegate
verification and failure cases. Controlled replay of the original native model
setter, key constructor, registration and interpolator ownership passes16
replacement cases across two cycles, four wheels, standalone/chained routes.
Original allocation failure and cached-model invalidation are exercised. The
existing Lancer mechanics validator also passes with the new selector around
it: duplicate callbacks, two scene clears and four allocation failures retain
their prior behavior. Name interning, allocator/free and cached-model destructor
sentinels are typed services in this replay. Actual source-file loading,
renderer timing, wheel rolling and repeated races remain owner D3D8 checks.

Private evidence: `.research-output/vehicles/evo2-native-v68/native-wheels-replay.json`;
REA static snapshot: ignored `scratch/evo2-native-wheels/rea-snapshot.json`.
Reproduce the controlled test with `tools/validate_vehicle_wheels_native.py`
using the pinned clean retail executable and a fresh private JSON output path.

## Verification boundary and v6.8 history retention

This investigation performed read-only archive/config/model measurements and
arithmetic checks. It did not execute either original game, run a new physics
simulation, change accepted projects or qualify the final native build.
Native candidate validation, D3D9 A/B captures and owner D3D8 tests are tracked
by the implementation results, not upgraded by this decision document.

The supplied complete v6.8 attachment is 303112 bytes, SHA256
`3de8dd7460d54f95f31e57d84504a8787fa13b4669f060d187266ae4b9805058`.
Its first 295599 bytes exactly equal the preceding current `MASTER_PLAN.md`
(SHA256 `9cf6c55df77b3a2eb8e5918193dc72e0274ac5d59748963df74d27e3167c0885`)
at baseline `c5bd91fc5dcb81e6e10c44ebbd9c0a6073b129ed`. The new 7513 bytes are
an appended v6.8 checkpoint; the historical leading v6.7 heading is intentional.
Both [MASTER_PLAN.md](MASTER_PLAN.md) and
[the retained v6.8 attachment](retained/master_rallye_vehicle_sdk_master_plan_v6_8.md)
were written byte-for-byte from that attachment. The old complete master and
the retained v6.7 attachment each occur exactly once as their respective
prefixes. No history text was summarized, duplicated or replaced. Verification
is private at
`.research-output/vehicles/evo2-native-v68/master-plan-v68-reconciliation.json`.
The current owner request authorizes the one native Source Fidelity candidate;
historical stop gates do not cancel that newer approval. Gameplay remains
pending until owner evidence exists for this exact 4Runner candidate.
