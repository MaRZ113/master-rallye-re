# V-DEF4.1 — TOMCAT, marker policies and native addon AI

## Result and owner boundary

The owner accepts Forester30, retail-Newrav-physics RAV4 31, TOMCAT32 visual
restoration and the 33-record 8/12/13 order. The old TOMCAT hybrid handling was
rejected. This revision is a new **offline-qualified candidate, owner test
pending**. No game was launched during implementation.

Private launch:
`.research-output/vehicles/v-def4-1/delivery-final/32/workshop/builds/first/candidate/Launch-SDK-Roster.cmd`.
Editable copies: `delivery-final/Open-30-Workshop.cmd`, `Open-31-Workshop.cmd`,
`Open-32-Workshop.cmd` under that same milestone directory.

All physical registrations, ordering, drivers/fallback labels, frontend stats,
accepted Forester/RAV4 physics, original models and native effects are retained.
No new vehicle, CarID, DLL loader, participant capacity or frontend setup screen.

## TOMCAT physics

The existing family-clone compiler copies retail **Wildcat → DefTomcat**, with
zero overrides: all147 vehicle fields and26 driving setup fields compare equal
after only the namespace rename. Engine/whole torque curve, drivetrain, tyres,
mass, suspension and damage are a coherent retail set. The two tyre selectors
remain the original `harddirt` references; no global tyre coefficients are edited.
The Wildcat source family and all other families are unchanged.

The new profile differs from the rejected hybrid in96 vehicle fields and zero
setup fields. Exact before/after attributes are in private `qualification-final.json`.
For example, total mass becomes1600kg instead of1200kg, retail Length3.5m
replaces the old4.5m setting, and CG is the retail0/.25/.35 vector. These are
requested full-donor values, not geometry measurements or hand tuning.

All121 original8.4.1 physics records remain inactive, with the original XML hash
`bd3efca271e27f4d00cc4f5846c4aa0bf74836dac223bc64339d28a05a65f4f7`.
The old accepted hybrid project is also preserved separately.

| Measurement | Original visual rest assembly | Active retail physics | Difference / boundary |
|---|---:|---:|---|
| Wheelbase |2.809745m|2.770000m|Visual +.039745m |
| Track |about1.640126m|1.660000m|Visual −.019874m |
| Maximum wheel radial bound |.390506m|.380000m|Visual +.010506m; not a fitted contact radius |
| Static hub height |−.095536m|−.100000m initialization datum|Source rest versus native initialization, not settled suspension |
| car.dx all-state render bounds |±1.028100; −.240302..1.446335; −1.998597..1.821514m|Retail dimensional fields retained|Includes existing native effects; not a body-only envelope or collision/solver dimensions |

Race/complete/wheel DX, collision, hub transforms, animation/controller records,
glass, ON cores and glow halos remain byte-identical to the owner-tested model.
Wheel/contact appearance, wear and handling require the new D3D8 owner test.

## Independent artwork roles

The read-only inventory found no SmallCarSheet in the available original8.4.1
tree and20 SmallCarSheet textures in9.3.1. The matching blue frame6 is
isometric; no source-qualified flat TOMCAT image was identified.
Original9.3.1 blue Wildcat frame6 is authentic artwork, but is not a flat HUD
profile. No missing original side-view image is claimed.

* `vehicle_select_art` / CarSheet: exact historical8.4.1 frame6, unchanged.
* `smallcarsheet`: **RECONSTRUCTED**, existing `mr-native-v2` renderer,
  azimuth−90°, elevation0°, orthographic, padding12, native32×16 compilation.
* Original isometric pixels remain in the prior accepted build, pinned source
  inputs, the new author's `heritage-art/original-isometric-smallcarsheet.png`,
  and private `delivery-final/32/heritage-private.zip` (original DXT/bank/pixels).

Each manifest role has its own policy, provenance and rendering parameters.
The generic restoration service no longer requires generated roles to share
one camera/render recipe. It reuses the normal Workshop art compiler.
Private current comparison: `previews-final/tomcat-hud.png`.

## Historical and automatic marker colours

| Vehicle | Original evidence | Selected policy |
|---|---|---|
| Forester30 |PS2 original Forester ID8: RGBA .91796875/.29296875/.36328125/1; words3f6b0000/3e960000/3eba0000/3f800000|HISTORICAL; qualified Demo/PS2 family association, explicitly cross-platform |
| Retired Demo RAV4 31 |Original PC registration is unresolved/absent in the later named table. PS2 Newrav13 is another variant.|UNKNOWN original; AUTO_DOMINANT from original RAV4 body materials |
| Early TOMCAT32 |PC841 registration stride36 has no RGBA vector. Later PS2 Wildcat15 colour is not proven for early841.|UNKNOWN original; AUTO_DOMINANT from original TOMCAT body materials |

Forester's native floats are copied exactly, not renormalized through byte RGB.
PS2 Wildcat15's .46875/.6484375/.828125/1 and Newrav13's
.72265625/.14453125/.171875/1 remain independently recovered values, not proof
for TOMCAT or retired RAV4. PC931's shorter record is not a retail RGBA layout.

`addon_sdk/marker_colour.py` samples seven deterministic barycentric UV0 taps per
triangle, weighted by its actual3D area. The manifests select exterior material
references; the general fallback uses opaque-material/name and normal heuristics.
Glass, wheels, crew, lamps, non-intact/ON states and auxiliary material groups
are excluded. Unused atlas regions receive no weight. Alpha below128 is excluded;
black RGB is not transparency. Dominant swatches use deterministic OKLab bins;
the average uses weighted linear-light RGB. Several livery swatches remain visible.

These are paint suggestions, not exact semantic segmentation or rendered lighting.
Paint/decals can share one atlas and seven taps cannot resolve every tiny marking.
Confidence and exclusions are explicit. An explicit texture fallback is labelled
LOW confidence; absent reliable evidence is an error rather than invented paint.

Workshop adds HISTORICAL/AUTO_DOMINANT/AUTO_AVERAGE/MANUAL, recalculate, dominant,
average and alternative swatches, HEX/RGBA, optional bounded hue-preserving contrast
lift, verified-history reset and the existing real HUD image tint preview.
Manual colour/alpha typing or choosing a swatch enters MANUAL. Recalculate alone
does not overwrite a choice. Automatic modes refresh when their pinned source
inputs change; manual values survive rebuilds. Reset/history/reopen retain policy
and evidence. `race-marker.json`, the working restoration manifest and the normal
`race_colour_rgba` preserve selection and derivation separately.

The native writer is unchanged. Initializer emulation verifies exact record bytes;
six additional original-x86 replays verify record-vector publication for30/31/32
on ordinary and competition paths. Registry/Broker calls are mocked. Existing
Race/CarN/Colour HUD consumption is reused and the shared marker texture is exact.
Private colour/swatches comparison: `previews-final/marker-comparison.png`.

## Native AI eligibility

| Class / restored vehicles | Quick Race | Rallye Cup | Master Rallye | Invitation |
|---|---|---|---|---|
| T1 addon mechanism |Enabled per manifest|Enabled per manifest|Enabled per manifest|Not applicable to ordinary T3-only Invitation |
| T2 Forester30 / RAV4 31 |Enabled|Enabled|Enabled|Preserved T3 restriction |
| T3 ordinary TOMCAT32 |Enabled|Enabled|Enabled|Enabled |

Challenge remains authored/event-specific. Practice has no independently qualified
opponent-generation owner. Neither is converted into an arbitrary addon pool.
No race participant limits or special/bonus stock eligibility are changed.

Source: immutable retail EXE
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
REA/Ghidra12.1.4 and independent original-byte disassembly. Existing H.2 owner
captures already prove Cup stage reuse and Master Rallye save/fresh-process resume
for the prior ID26 extension. They are precedents, not new TOMCAT gameplay proof.

The common native extension chains existing T1/T2 source loops and adds four
T3 loop-tail seams:4581f8 (Quick),451f4e (Master),45ad89 (ordinary Cup arm),45acbb
(forced ordinary-T3 Cup/Invitation arm). Each9-byte preimage is verified.
Original increment/counter/branch behavior, player exclusions and vector insertion
are preserved. Ordinary arms continue at their original gated special additions;
the forced arm keeps its original special-vehicle exclusions.

Cup and Invitation have separate settings despite their shared generator.
Original singleton4ada50/getter4abe90 reads Race/Type:6 Cup,8 Invitation. Full
registers/flags are saved around those native calls. The original4ae620 getter
is **Frontend/RallyeCup/Cup**, not Race/Type; its value5 selects the special
ordinary-T3 arm and must not be confused with race mode5.

The new paths pass physical CarIDs through original exclusion bodies, chooser,
shuffle, class/DriverID publication and Results. Custom menu indices are never
AI IDs. Workshop exposes per-mode flags. Explicit runtime-class/AI declarations
in the common roster builder permit a qualified T3 policy even while the asset
author uses its existing technical T2 compiler slot; standalone T2 Invitation
eligibility is not falsely enabled. The current configured roster owns class
availability, overriding stale heritage metadata. No second compiler or registry
is introduced.

39 actual original-loop/exclusion cases pass for the three-vehicle candidate.
A noninstalled T1-assignment test exercises the same common mechanism in42 cases.
Source-free tests also toggle Cup-only/Invitation-only/both and reject unrelated
runtime types while clobbering getter registers. Native calls/container insertion
are mocked; live AI, Results and newly created save/resume remain owner tests.

Master resume452fe0 (2454bytes), Master stage452370 (542bytes), Cup stage45b170
(607bytes) remain original. Participant IDs and storage layouts are not rewritten.
The existing build-time active-championship guard remains; use disposable state.

## Compatibility, tests and preservation

Randomizer was inspected read-only. Declared v13 operations show no byte overlap.
F3 still conflicts at Challenge consumers450111 and45ec38 (two bytes each in this
33-record layout, feature mask1). There are no new T3-tail overlaps in these
examined plans. Nonoverlap is not runtime coexistence or semantic compatibility:
class randomization/pool replacement can alter policy independently. No Randomizer
source, installed proxy or hook was modified; no competing DLL was installed.

The exact resource comparison changes only vehicles.xml and TOMCAT's
smallcarsheet_035_000.dxt; the other412 indexed resources match V-DEF4 exactly.
All1160 protected original/accepted-build pins are unchanged. Full Windows
checkpoint:1353 tests, no failures/errors,2 existing optional fixture skips.
Late policy/material ownership/reset refinements have an additional focused run;
89 tests PASS; see current provenance. Actual Windows Tk marker controls, swatches,
RGBA Apply, preview, Undo/Redo/Restore are exercised on an independent copy.

Current private reports: `qualification-final.json`, `determinism-final.json`,
`focused-release.json`, `full-windows.json`, `protected-after.json`,
`persistence-consumers.json`, `randomizer-comparison-final.json` under
`.research-output/vehicles/v-def4-1`. Preflights never launch the game.

## Owner checklist and rollback

1. Launch the final private CMD. Confirm30/31/32 and their accepted adjacency,
   CarSheets, names and stats. TOMCAT's race miniature must now be flat side-view.
2. Drive TOMCAT over bumps, steer/brake and compare tyre wear/handling to retail
   Wildcat. Inspect contacts through suspension travel; report any visible offset.
   Forester and RAV4 handling must stay unchanged.
3. Check all three marker tints, glass/breakage and rear ON/core/halo states.
4. Start fresh class-matched Quick Races, Cups and Master Rallyes; repeat draws
   to observe eligible addons naturally. In Invitation check ordinary T3 TOMCAT,
   not T2 Forester/RAV4. No addon should duplicate a current human player's CarID.
5. Finish, check AI/player Results identities, return/re-enter and advance a Cup
   stage. In disposable candidate state save a new Master Rallye, close the game,
   relaunch and resume; participants and progress must persist correctly.
6. Test any selected Randomizer configuration separately; known F3 Challenge
   conflicts remain uncomposed. Do not copy trial saves back into accepted builds.

Rollback is launching the previous accepted CMD. No installed file needs repair.
Stop after this candidate; tyre presets are a design note, not implemented UI.
