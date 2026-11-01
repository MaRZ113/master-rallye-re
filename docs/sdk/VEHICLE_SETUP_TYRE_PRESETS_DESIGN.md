# Future Vehicle Setup Extension — tyre presets (research only)

V-DEF4.1 implements no tyre menu, runtime switching, frontend screen or service
park. The TOMCAT active candidate uses the unchanged retail Wildcat harddirt set.

## Original representation and existing boundary

Read-only retail Data.sma/vehicles.xml inspection finds tarmac, harddirt, gravel,
grass and mud prefixes. Each has five indexed records0..4 and12 coefficient
fields, including PeakMu, CorneringCoeff/Gradient, InflationStiffness/Damping,
LongitudinalStiffness, CamberStiffness, ScaleFactor, PneumaticTrailCoeff and
Wet/Soft/IceRating. These table indices are original solver data; they are not
five recovered player-selectable tyre grades or a validated wear progression.

Vehicles select prefixes separately through Suspension/Front/TyreType and
Suspension/Rear/TyreType. The typed SDK already validates those references and
can clone owned tyre families without changing global defaults. V-PHYS1 maps
the suspension reader49e970 and instance writer496d20; the original reader's
TyreType references were revisited at49f98d/49f998/49f9a2. This establishes the
configuration input boundary, not complete live tyre object lifetime/ownership.

Existing native publication44ed50/44f334 and wheel construction440770 provide
the useful pre-creation seam. Do not change a shared family after some actors
have initialized or assume that editing XML updates already-instantiated tyres.

## Proposed future architecture

* Add a versioned per-vehicle setup manifest listing only qualified presets and
  immutable source prefixes. Keep visual tyre meshes and driving coefficients
  separate. An independent front/rear choice should initially be constrained to
  coherent approved pairs rather than arbitrary mixed tables.
* Persist the player's selected preset by stable addon identity, with an explicit
  fallback when a package/preset disappears. Stage a per-participant choice before
  named parameters are copied to Vehicles/CarN and before tyre construction.
* Reuse the native reader/instance publication path with isolated participant
  parameters. A future service park can select the next stage's preset through
  this same boundary; it must not mutate a running solver.
* Keep AI policy explicit: donor/default or a deterministic event/surface preset
  selected before every AI instance. Avoid changing shared XML for one player's
  choice. Preserve native DriverID and roster/save identities.
* Evaluate a pre-race Workshop/runtime setup dialog first. A native frontend menu
  needs separately qualified widget ownership, navigation/localization, event
  sequencing, rollback and save compatibility; no spare safe screen is assumed.

## Required future qualification

Trace the selected prefix through coefficient lookup, native object creation,
cache/reference ownership and destruction; identify exactly when arrays are
copied versus referenced. Prove per-instance isolation and both single/split
player paths. Verify existing player setup overlays do not reapply an old prefix.
Qualify new-competition, stage/restart and saved-game resume separately, including
missing packages, preset schema changes and service-park timing. Confirm HUD/setup
labels and ensure AI receives valid values. Gameplay A/B tests must establish
wear/traction behavior; a plausible prefix name is not a physical tyre model.
