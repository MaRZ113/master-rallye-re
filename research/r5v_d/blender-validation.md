# R5V-D Blender validation

## Environment

- Blender **5.2.2 LTS** (`d13f752e3b9c`)
- Add-on version **4.4.0**
- Packaged add-on built from the current tracked source tree
- Install test profile isolated under ignored `.research-output/r5v_d/`

## Multi-revision corpus import

`tests/blender/multirevision_vehicle_smoke.py` passed in headless Blender.
The add-on imported all **50 supported DX files** in the supplied demo input
folders and **9 retail DX files** from the Astero, Pajero, and Terrano folders.
The two revision-125 inputs were correctly skipped and reported as
unsupported. Folder imports created the expected number of mesh objects and
preserved geometry counts, revision and filename properties, vehicle roles,
validation profile, UV layer count, collision status, and conservative normal
policy.

Single-resource imports passed for revision-127 Trooper `car.dx`, revision-131
Trooper `car.dx`, the revision-135 Forester trigger
`!other_research/9.10.0_dxForester/car.dx`, and retail Astero `car.dx`. The
Forester object has 2,459 vertices, 1,864 triangles, 15 draws, and profile
`VALID_WITH_INDEX_ORDERING_DIVERGENCE`. Its mesh imported successfully while
retaining the exact mismatch diagnostics.

The direct import smoke also checked source-index and draw-role metadata,
direct-source-V UVs, absence of native custom-normal setter use, DXT PNG row
policy, and resolution of available preview textures. Some supplied demo
folders contain incomplete texture sets; missing resources produced explicit
preview warnings and did not prevent structurally valid geometry imports.

## Packaged add-on

`tests/blender/multirevision_addon_smoke.py` passed after installing and
enabling the generated ZIP from an isolated Blender user profile. The packaged
vendor parser imported all three resources in each of the revision-127
Trooper, revision-131 Trooper, revision-135 Forester trigger, and retail
Astero folders. The output retained the expected roles, geometry counts and
validation profiles, including all three Forester ordering-divergence
resources.

The existing `tests/blender/addon_install_smoke.py` also passed on the ZIP:
operator registration, vendored synthetic DX import, collision overlay,
direct-V policy, and byte-identical zero-edit positions export all passed.

## Blender regression checks

- `tests/blender/import_smoke.py`: **PASS**. Synthetic folder/single imports,
  mesh and metadata, save/reload, source-normal fallback, collision overlays,
  strict provenance checks, and zero-edit/one-vertex positions export passed.
- `tests/blender/validate_real_vehicles.py`: **PASS**, 22 vehicle resources
  across the selected retail families, including auxiliary `megane/sus.dx`.
  Save/reload metadata and selected zero-edit retail exports remained valid.
- Python synthetic suite: **127/127 PASS**, including course regression tests
  from the unchanged baseline.
- Independent older revision-135 validator: **15/15 PASS** on supplied demo
  rev135 files (3 exact, 12 allowed ordering divergences), matching the new
  per-draw oriented topology classification.

Machine-readable reports are `blender-validation.json`,
`packaged-addon-validation.json`, `blender-synthetic-validation.json`, and
`blender-retail-regression.json`. Blender and Python results validate parsing,
import, and tooling behavior only; no new original-game runtime test was
performed in this phase.

## Manual Blender validation and freeze

The project owner reports completing the following Blender UI checks on
2026-09-29:

- Demo 8.4.1 vehicle-folder import: **PASS**.
- Demo 9.3.1 vehicle-folder import: **PASS**.
- Demo 9.10.0 cooked vehicle import, including the previously rejected
  index-ordering-divergence resource: **PASS**.
- No Blender crashes were observed.

**LEGACY MATERIAL SEMANTICS PARTIAL.** Revision-127/revision-131 geometry
import is supported. Texture lookup and UV import are supported where proven.
Alpha, alpha-test, and environment semantics are not fully decoded. Direct
legacy demo DX import does not establish visual Direct3D 8 material parity;
visible alpha/transparency, including vehicle glass, remains incomplete.
Revision 125 remains an unsupported legacy outlier and was not investigated.

**R5V-D STATUS: PASS — VEHICLE BLENDER BASELINE FROZEN.** This closes the
multi-revision vehicle import phase only. It does not close course/track
support or declare the project-level SDK ready for public release.
