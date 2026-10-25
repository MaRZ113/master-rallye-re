# Optional native unsprung mechanical instances

The original retail engine exposes a non-spinning wheel transform and a
separate wheel-spin interpolation layer. V-FIT4 can therefore attach selected
mechanics through native scene instances without modifying suspension,
steering, drivetrain parameters, or the existing rotating wheel mesh.

This is an optional generated process-extension prototype for executable
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Original EXE/DLL/assets are not edited. Controlled native checks pass; a live
race, repeated race transitions, real loading/rendering and gameplay remain
human qualification gates.

## Original binary chain

REA/Ghidra12.1.4 evidence was collected from the hash-verified original x86 PE.
Original instruction bytes, PE mappings and native vtable words were also
checked independently with Capstone. Pseudocode is decompiler output, not
original source.

| Original VA | Observed role |
|---|---|
| 0043F22C -> 0043ED00 | Binds native physics wheel to actual scene-wheel entity; parameters are car-name key pointer, wheel index, scene entity pointer |
| 0043ED98 | Stores existing scene-wheel name key at physics wheel+180h |
| 0043ED8E..0043EDCE | Allocates1Ch native wheel interpolator, constructs448570(wheel pointer), installs through4F5CE0 |
| 00441270..004418E9 | Constructs wheel world pose including clamped jounce, steering/toe and camber, plus positive-side Y half turn |
| 004418E9..00441921 | Resolves scene-wheel name, constructs Broker transform key through4F54C0, publishes64-byte pose through4D8390/4DDEC0 |
| 00446EF0 | Wheel camber150h = base154h + coefficient158h * bounded jounce |
| 004485E0 | Calls generic5090F0 interpolation, then adds interpolated spin from wheel120h/12Ch |
| 00690170 | Wheel interpolator vtable:448590 deleting destructor,4485E0 evaluator |
| 00690178 | Native base interpolator vtable:4485C0 deleting destructor,5090F0 evaluator |
| 004F5290 / 004F5350 | Transform controller constructor/init; its+C key identifies Physics/<entity name>/Transform |
| 004F5440 | Reads its Broker key and copies64-byte matrix into entity+50h state at+1Ch |
| 004F5670 / 004F59F0 | Allocates/initializes/registers native scene entity and sets indexed name |
| 004F5B70 | Sets extensionless model key in scene state |
| 004F5950 | Owns transform controller at slot0, invokes native init |
| 00522480 -> 004F60F0 | Scene teardown clears native registered entities |
| 004F5780 / 004F5AF0 | Entity/state destruction deletes owned controllers/interpolator/model instance and unlinks lists |

The matrix published by441270 is not the spinning wheel render matrix. Its
spin accumulator128h changes, but pose construction uses steering140h/144h
and camber150h. The added spin belongs to4485E0. This separation is confirmed
by executing the original instructions with varied spin angle/speed while
holding the unsprung pose constant.

## Model-key guard

Original4B6F9F loads string006E6A78: **`vehicles/`**, then appends the actual
family name.4B7100 appends006B1974: **`/wheel`**, without `.dx`.
4D0580 ->4D4460/4D4B30 interns keys using case-sensitive byte comparison.
Comparing a newly interned `Vehicles/.../wheel` ID would silently miss the
original lowercase prefix.

The adapter therefore obtains the actual wheel model-key string through
4D0570 and compares bounded ASCII case/slash-folded **whole strings** against
`vehicles/<runtime_family>/wheel`. Prefixes, longer families, `.dx`, and added
path segments do not match. Native resource keys remain explicit profile data;
lowercase `vehicles/<family>/mechanicsN` follows the original path builder.

## Extension and ownership

`tools/vehicle_mechanics_native.py:append_mechanics` appends code to the
existing bounded SDK process allocation and patches only the exact original
call at43F22C. Its native input profile is:

```json
{
  "runtime_family": "LancerEvo4",
  "resource_keys": [
    "vehicles/LancerEvo4/mechanics0",
    "vehicles/LancerEvo4/mechanics1",
    "vehicles/LancerEvo4/mechanics2",
    "vehicles/LancerEvo4/mechanics3"
  ]
}
```

The wrapper calls original43ED00 exactly once, preserving its arguments,
returned EAX/flags, stack contract and callee-saved registers. It acts only on
the explicitly selected source wheel resource. The scene name identifies the
actual participant; no physical CarID or runtime-family/participant-number
equivalence is assumed.

One auxiliary entity named `<actual wheel name>/SDKMechanics` is created by
the native entity constructor/name/model path. An existing name bypasses a
duplicate callback. The normal transform controller is installed through the
native ownership setter; its key is then bound to the existing wheel's
`Physics/<wheel name>/Transform` key via the same4F54C0 constructor used by the
publisher. The original physics wheel name/registration is not redirected.

The adapter uses the observed1Ch interpolator allocation and native448570
constructor, then selects its native base dispatch00690178. The base evaluator
5090F0 retains pose interpolation and omits4485E0's spin extension. Its native
deleting destructor owns/free the allocation. No process-lifetime static
interpolator or new matrix simulation is introduced.

Each explicit allocation failure destroys already-owned state through native
4F5780 and the native free entry. Native scene manager teardown owns successful
entities and components. These ownership paths are replayed in a controlled
harness; real allocator behavior and repeated live scene teardown remain
runtime qualification requirements.

## Resource compilation and damage

`addon_sdk.mechanical_attachments.build_mechanical_resources` requires a
hash-pinned four-group selection and a qualified stock brake template. It
returns `car.dx` with those12 ordinary leaves removed plus `mechanics0.dx`
through `mechanics3.dx`. Normals, UVs, RGBA, indices and materials are retained.
Each auxiliary geometry uses `source position - source hub`, with the inverse
proper Y half turn on the positive side. This compensates the original native
wheel rest basis; the caliper's original side/orientation and rotor's intended
37.34 mm outboard plane survive. Runtime hub position comes from native physics.

`verify_mechanical_resources` compares every retained body draw's complete
ordered vertex/triangle attributes, textures, material words and flags, native
control words and logical blight cases; body collision bytes are identical.
It also validates the exact expected auxiliary inverse basis and all auxiliary
attributes. Mutating an auxiliary colour byte is rejected by the synthetic
test.

The remaining body retains native CPU deformation/darkening/coverage policy.
The unsprung mechanics become independent visual instances analogous to native
wheels. They no longer deform as part of the body surface. This ownership
change is explicit and appropriate for wheel-mounted mechanical parts; it is
not a promise of original GT4 damage behavior or PS2 visual parity.

The observed V6 output retains107 body draws /3587 vertices and extracts48
mechanical vertices into four resources. `complete.dx`, `wheel.dx`, original
textures, physics, audio and UI are not rewritten by this helper. Auxiliary
models and their process extension must be admitted together; do not use the
body with removed mechanics without its attachment extension.

## Verification evidence

- Seven synthetic tests pass, including exact extraction attributes and a
  negative corrupted-attribute case.
- Original441270 pose replay covers18 spin/speed variants across both sides,
  positive/negative jounce, steering and camber. Equal unsprung inputs give
  byte-identical poses for different spin states.
- Original4F5440 copy executes against a checked Broker-key getter boundary,
  followed by original5090F0 at fractions0/.5/1 for18 interpolation cases.
  Matrix copies, fixed orientation, translation interpolation and native stack
  returns pass.
- Controlled original constructors/setters/destructors/scene clear execute
  for two scene cycles, duplicate callbacks, source-family case/slash variants,
  foreign and near-match model paths, and all four explicit allocation-failure
  points. Native-owned allocations return to the pre-scene baseline.

Heap allocation/free and name/Broker index services are explicit ABI stubs in
the lifecycle harness. The original wheel-registration call is counted through
a boundary stub there. These checks do not establish live model loading,
render timing, the real allocator, actual race transitions or gameplay.

Private evidence is stored in `.research-output/vehicles/vfit4/`:
`native-evidence.json`(33 REA records), `native-instruction-evidence.json`
(12 original instruction regions and vtables), `native-mechanics-lifecycle.json`,
and `dynamic-resources/mechanics-resources.json` with exact attribute audit.
The dynamic body SHA256 is
`04c77769ca1fd600ac3c0d49968fec23a83bcb8c4db1df81d602bb4c67bd7a90`.
The static control remains separately documented in `brakes.md`.
