# V-PAJERO2 — reflection continuity and headlamp diagnosis

**Status:** final source-fidelity material assets are `build-r3/assets`, with
reflection continuity, approved lamp keepout, explicit dark housing fallback
and recovered original race taillights. Actual Previewer captures inspected on
both sides. Native gameplay remains for the user to qualify. The reflection-only
`build-01` and separate negative alpha-test/culling diagnostics remain available.

Private outputs: `.research-output/vehicles/vpajero2/materials/`.
Original GT4 Beta `mits0038`, Subaru, Lancer, physics, fitment, crew, UI and
audio are not edited by this work.

## Reflection transition: cause and correction

Original opaque exterior base group is menu shape 5 / race shape 4. Exact
oriented source triangles have corresponding GS environment draws. Several
packets combine solid body islands with cutout regions in one texture. The
conservative original converter declined the **whole packet** when coverage
could not be proved for its full UV footprint. Adjacent packets which happened
to be wholly opaque received reflection, causing the observed hard boundary
near the Nikon side panel and number area.

The new editable profile selects exterior packets 13–33 in menu shape 5 and
15–35 in race shape 4. Existing shared `prepare_paint` proves complete,
unambiguous source environment correspondence, partitions the existing
triangles by coverage and uses the already qualified explicit reflection-alpha
floor 129 only for residual cutouts. No numeric `MatN` classification, vehicle
branch, painted-colour heuristic, new surface, changed UV or automatic
reflection assignment is used. Separate decals, glass, wheel rubber, lights
and cockpit layers retain their own source material behavior.

| Explicit exterior selection | Before | After |
| --- | ---: | ---: |
| Race reflected triangle area | 5.8205 m² | 11.4076 m² |
| Race unreflected triangle area | 5.5871 m² | 0 |
| Race neighboring reflection mismatches | 20 | 0 |
| Menu neighboring reflection mismatches | 25 | 0 |

Areas describe selected geometry, not measured game reflection intensity.
Source GS generated environment is represented by the existing MR helper
approximation; cutout coverage and reflection share MR's alpha channel.
The revised DX retains exactly the same oriented positions/normals/UVs/colours
and 2179/7256 race/menu triangles. Splitting duplicates 65/61 vertices and adds
11 draws per body model. `wheel.dx` and source hub profiles are byte-identical.

## Reusable diagnostic

`addon_sdk/reflection_continuity.py` and
`tools/audit_vehicle_reflection_continuity.py` inspect **actual converted DX**
for shared-edge neighboring draws with different environment flags. Optional
editable eligible draw indices restrict the comparison to previously qualified
paint. Without a selection, glass/trim boundaries are deliberately reported as
suspicions, never automatically repaired.

The tool can export an opaque diagnostic family: green = reflected eligible
surface, red = unreflected eligible surface, blue = outside selection. These
colours intentionally replace source artwork and alpha; they are **coverage
diagnostics, not material-fidelity renders**.

```text
python tools/audit_vehicle_reflection_continuity.py <car.dx> --eligible-draws <indices.json> --coverage-dir <new-debug-family> --output <audit.json>
```

Private `reflection-continuity.json`, `before-coverage.png` and
`after-coverage.png` reproduce the measured boundary change. Beauty captures
`beauty-after.png` and `beauty-no-reflections.png` were inspected separately.

## Headlamp: verified cause in converted geometry

The supplied intact-game screenshot shows one angular black wedge in the near
lamp. The same wedge is reproduced at the **whole-car 35° camera**, even though
a close-up camera aimed directly at the lamp can hide it. Culling NONE and an
isolated binary-alpha→cutout experiment do **not** remove it.

The original lamp pair, source shape 12, contains 8 consistently wound fan
triangles per lamp. The centre is recessed approximately 107 mm behind the
rim. It is source-alpha blended, depth-writing, uses a 64×64 texture with only
zero/unity alpha, and has no partial vertex alpha.

The actual occluder is **menu shape 17 / race shape 19**, the black wheelwell
liner. Its two longitudinal side planes physically overlap the concave lamp
interiors. This is original decoded source geometry, not an added backing or
an inverted lamp triangle. The liner's source region-clamp top row is genuinely
opaque black; the texture sampler is not inventing this value.

A diagnostic CPU ray through full-car capture pixel (400,480) hits the black
liner at distance 4.2767 before the visible lamp fan at 4.3106. Culling NONE
still shows the wedge. The source renderer may have additional behavior not
recovered here; **this does not prove the original GT4 game shows the defect**.

## Approved keepout adaptation

Shared `addon_sdk/visibility_keepout.py` takes explicit original-source hash,
target source shape/packet, protected source shape/packet, and explanatory role.
It derives a closed AABB for each connected protected lamp component and
subtracts only the intersecting wheelwell polygons. The bounds are not inflated
or guessed. Nonintersecting geometry is retained, and new boundary vertices
interpolate source UVs/normals/colour. Unknown morph interpolation is rejected.

The editable `headlamp-keepout-profile.json` selects the known source liner and
lamp pair independently for menu and race. It is **an intentional diagnostic MR
adaptation**, not a claim to reproduce missing GT4 runtime semantics.

`build-keepout/assets/` preserves every lamp and every non-liner triangle,
all material flags, every DXT byte, collision, wheel resources and hub profile
relative to the reflection candidate. Four intersecting liner triangles are
re-tessellated into twenty outside-volume triangles, adding 16 triangles per
model. The black wedge disappears in `beauty-keepout.png` versus
`beauty-after.png` at the exact same camera. Race and opposite-side captures
are also provided. Review and actual MR testing are still required.

The earlier `build-ab` binary-alpha→cutout option changes exactly one alpha-test
flag byte per body DX and no geometry or texture. It is retained as **negative
diagnostic evidence**, not presented as the fix.

## Evidence and boundaries

- `build-01/`: default reflection-only source-fidelity assets.
- `source-profile.json`: editable reflection selections.
- `validation.json`: deterministic shared GT4 rebuild and DX/DXT checks PASS.
- `material-regression.json`: exact oriented triangle and collision checks;
  isolated cutout experiment changes only one flag byte per model.
- `build-keepout/`, `headlamp-keepout-profile.json`: separate adaptation.
- `keepout-regression.json`: all non-target geometry, lamps, textures,
  materials, wheels, hubs and collision preserved.
- `keepout-validation.json`: deterministic reconstructed-source build checks.
- 39 focused synthetic tests pass: adjacency selection, binary-alpha admission
  and rejection, source-hash guards, closed-volume clipping, outside-region
  preservation, attribute interpolation, deterministic output and existing
  GT4 material/reconstruction regressions.

Texture-resolution selection and native loading optimization are separate
parent tasks. These builds use source-fidelity textures; a parent quality-aware
Balanced step can be applied to a copied candidate without altering geometry.
Previewer observations establish the conversion defect and the isolated repair
effect, not native FPS, actual gameplay reflection parity or damage qualification.

## Missing lamp surround: explicit MR housing approximation

Aperture glass (menu shape13 / race shape15) is wider than the round lens bowl.
The recovered source contains no opaque rectangular housing at its outer
corners. Independent source ray checks at X±0.65,Y0.75 intersect translucent
aperture glass, transparent body texels and no lens; X±0.55,Y0.65 does intersect
opaque lens. Both sides are symmetric. Disabling culling does not close this
opening. This is separate from the wheelwell wedge above.

The editable `source_housings` rule pairs each source aperture component with
its lens component, derives their union bounds, and adds a dark open-front
five-face enclosure: **20 triangles total**, no arbitrary expansion or offset.
Glass, lens geometry, artwork and UVs remain unchanged. This is an intentional
MR occlusion approximation, not recovered GT4 geometry. Source-hash pinning,
unique selectors, component correspondence and non-morph admission fail closed.
Private `r2-front.png` and `r2-front-opposite.png` show the same byte-identical
assets as final r3: both lamps retain their lens and have black corner backing.

## Race rear lights: original Beta VM callback correction

The old race build omitted original source shape24 (12 corner-lamp triangles)
after treating preceding VM callbacks as unresolved spatial transforms. Those
callbacks actually set a scalar morph/tween weight, so their persistence cannot
move a following non-morph shape. Shape25 remains an accounted generated
environment effect; no synthetic rear lamp was invented.

Evidence is from the immutable decoded Beta ELF SHA256
`962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0`:

- ModelSet interpreter `0x002F73F8`, opcodes0x59/0x5A, dispatch virtual slot+0x14.
- CarModel vtable `0x006C15B8`, slot+0x14→`0x002F3AC0`.
- Dispatch table `0x006F6430`, indices1–4→`0x002F3B10`.
- `0x002F3B10` calls scalar clamp/setter `0x002F8540`, then `0x005A4648`.
- Original words at0x005A4648: `3C027000 34422000 03E00008 E44C0C30`.
  Rabbitizer R5900 independently decodes the final delay slot as
  `swc1 f12,0xc30(v0)`, writing the scalar to0x70002C30, not a spatial matrix.

Ghidra12.1.4 Emotion Engine exports and original-word Rabbitizer cross-checks:
`scratch/vpajero2/tween-callbacks.txt`, `tween-rabbitizer.txt`. These are static
binary facts; no GT4 runtime execution or GS parity is claimed.

Reusable reconstruction opt-in `vm_tween_callback_profile` requires that exact
engine hash, context `GT4Beta.CarModel.callback_vtable_006C15B8`, explicit admitted
indices1–4 and evidence text. Unknown callbacks, other handler contexts, actual
matrix commands and unresolved morph weights remain rejected. Source command
provenance is retained. Existing profiles without the opt-in preserve legacy
behavior. This is deliberately not assumed for other GT4 releases or VM types.

`r2-rear.png` / `r2-rear-opposite.png` visually confirm both original lower
corner-lamp assemblies in race, in addition to the existing upper red lights.
This restores visible source surfaces; native brake-state qualification is
not newly claimed for Pajero.

### Frozen Lancer/Subaru regression boundary

A direct reconstruction comparison with and without the new opt-in produces
114 menu /116 race Lancer source draws with **zero changed qualification**.
`lancer-callback-impact.json` records both original source hashes and comparisons.
The frozen Lancer profile/assets are untouched. The separate GT3 Subaru pipeline
is unaffected. Parent-level roster/package integrity checks cover installed
frozen resources; this material task does not rebuild or modify their packages.

## Front mudflaps

Race source22/23 both use the same genuine32×32 black-rubber texture binding,
valid mirrored UVs and complete morph endpoints. An isolated two-draw conversion
(`frontflaps-only`, `flaps.png`) shows textured rubber on both sides; their source
RGB is intentionally very dark. Rear flaps20/21 use a different grey-rubber
texture. No missing reference or evidence for a UV flip/texture replacement has
been found. Keep the source behavior pending an exact marked problem surface;
do not claim the reported one-side appearance fully resolved.

## Final source-fidelity build and regression

Final `build-r3` was regenerated with the final explicit VM-context metadata:

| Resource | Vertices | Triangles | Draws | SHA256 prefix |
| --- | ---: | ---: | ---: | --- |
| complete.dx | 8763 |7292 |226 |79e12ca8126f6715 |
| car.dx |3184 |2227 |119 |9f6f2f352dc6a43a |
| wheel.dx |1192 |1076 |24 |51a7f705a2f94056 |

`r3-validation.json` is PASS_OFFLINE_WITH_DOCUMENTED_TRANSLATION_LIMITATIONS;
its independent rebuild reproduces final bytes. `r3-reflection-continuity.json`
retains zero mismatched exterior neighbors and zero unreflected selected area.
`r3-regression.json` proves every existing keepout-build oriented triangle and
all position/normal/UV/colour attributes survive exactly. Only20 housing triangles
are added per model and12 restored original taillamp triangles in race. Collision
suffixes, wheel bytes and every existing DXT are identical. One1×1 white texture
supports the opaque black vertex-coloured housing. No fitment/physics/UI/audio
is altered. Full-source textures remain available for parent quality-aware
normalization; these Previewer captures are not native FPS measurements.
