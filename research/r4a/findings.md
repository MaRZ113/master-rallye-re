# Phase R4A findings

## Result

R4A maps three distinct runtime roles without executable analysis:

- `complete.dx`: assembled presentation resource, normally with embedded wheels;
- `car.dx`: race body/chassis resource with crew, collision-hull-associated
  structure, and normally switchable glass/light groups;
- `wheel.dx`: separately instantiated race visual wheel template.

The authoritative swap observations are preserved in
`docs/vehicle-runtime-roles.md`. The supported conclusion remains that the
race runtime expects the structure represented by `car.dx`; collision data is
not claimed to reside wholly in that file.

## Corpus evidence

- 26 vehicle folders, 78 DX files, 78 parsed/validated, zero failures.
- All 26 have `car.dx` and `complete.dx`; 25 have `wheel.dx`; megane also has
  `sus.dx`; Ufo has no wheel resource.
- All 25 wheel resources: 252 triangles, tag 2 only, one UV set, 4–5 draws,
  recognized bounds footer.
- Every car structural sidecar has crew names; no complete structural sidecar
  does.
- 25 complete sidecars have 4–5 non-spare wheels; Ufo has none.
- 22 complete resources contain the full separate-wheel edge signature at a
  four-copy minimum. IceCream, Kamaz, and Navara use named embedded wheels but
  do not match the separate wheel signature under this test.
- All cars use an opaque trailing family starting raw u32 `101`; only the
  `$chull`-bearing SeatBuggy complete shares that marker.
- In 24 standard cars, TXT span minus compiled render triangles equals the
  literal `$chull` triangle span exactly. Pajero's nonstandard source sidecar
  does not reconcile; forklift has no named hull.

## Collision conclusion

**PARTIAL / HIGH association.** `$chull`, `ConvexHull/PlaneThickness`, the
omission of hull triangles from the render table, and trailing marker `101`
form a coherent collision-resource chain. The exact trailing schema and
runtime activation rule remain unresolved. The complete-for-car failure is
consistent with a missing/incompatible race structural binding, not proof of
one exclusive collision-data location.

## Damage and glass conclusion

**PARTIAL.** Numeric damage behavior is data-driven through global
`Damage.xml` limits and per-vehicle `vehicles.xml` parameters. Car-only
tag-7/tag-8 groups provide strong static binding candidates for breakable glass
and brake-light states. No XML or mapped binary field binds procedural body
deformation to specific vertices.

## Lift anomaly

**UNRESOLVED_RUNTIME_TRANSFORM_DEPENDENCY.** Astero `car.dx` source-Y minimum is
-0.228596 while complete is -0.000733, and near-zero complete minima versus
lower car minima are common. This is a correlation only. Bounds, embedded
wheels, external suspension locations, and loader role remain competing
explanations.

## Decision

R4A requires no Ghidra. The next evidence-driven phase should be **R4B —
Targeted Vehicle Physics / Damage RE**, beginning with the four minimal runtime
experiments and then mapping only marker-101/hull structures needed to explain
their results. No R3 writer capability was expanded.

## Regression validation

- Python synthetic suite: **52/52 PASS**.
- Blender 5.2.2 LTS (`d13f752e3b9c`) synthetic import, save/reload,
  provenance rejection, and positions-only export: **PASS**.
- Packaged add-on install/import/zero-edit export: **PASS**.
- Existing diverse real-resource harness: **19 resources PASS**, including
  Astero, Pajero, Forester, Bruno, Ufo, and megane `sus.dx`; all 12 R3
  zero-edit export samples remained byte-identical.
- The genuine Pajero declared/root-count parser diagnostic remained visible;
  no game-derived output was added to Git.
