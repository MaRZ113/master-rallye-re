# V-MESH4.13 — native-style UI preview authoring

Scope: UI sources and their generation/normalization only. Branch:
`research/vehicles`. Baseline: private V412 `v412-exp-006`. Final candidate:
`.research-output/vehicles/vmesh413/v413-exp-004/`.

## What the original pictures show

All 32 Vehicle Select frames and 30 smallcarsheet frames were inspected from
the user's retail archive. There are 30 and 29 nonempty alpha silhouettes
respectively; a further Vehicle Select image is a black silhouette placeholder.
Contact sheets retain native ordering (8 frames per row); small images are
enlarged with nearest sampling only for inspection.

| Feature | Vehicle Select | RaceResults smallcarsheet |
| --- | --- | --- |
| View | front three-quarter, nose left; near wheel visibly larger | almost pure side, nose right |
| Canvas | 128×128, art low in canvas, generally left of canvas centre | 32×16, almost full width |
| Median visible bounds | `[13,67.5,99,121)` | `[0,1,31,15)` |
| Mean visible luma, corpus median | about 83 | about 118 |
| P90 visible luma, non-placeholder median | about 166 | about 203 |
| Apparent illumination | overhead/front, readable roof/hood, dark tyres and glass | brighter, simplified contrast survives very small size |
| Presentation | transparent background; no consistent large cast ground shadow | transparent background; common wheel baseline |

Special vehicles and blanks are not evidence for a universal road-car size.
The preset targets ordinary cars, pickups and SUVs; proportions remain intact.
Lighting directions and camera numbers below are estimates. The stored textures
prove pixel composition, not the original offline renderer or lighting rig.

## Camera calibration instead of a guessed 3/4 view

The first 120°/18° orthographic render was too lateral. A subsequent 135° view
still lacked the original's near/far wheel size difference; the user requested
closer matching. The original Navara `complete.dx` was then projected against
its original `carsheet_023_000.dxt`. A bounded azimuth/elevation/distance grid
and local refinement compared binary silhouette intersection-over-union (IoU),
normalizing width and centre without independently stretching X/Y.

- Best orthographic grid fit: IoU **0.79365**.
- Best refined perspective fit: **138° azimuth, 10° elevation, distance 7m**,
  IoU **0.93129**. This is silhouette overlap, not 93% overall visual fidelity.
- Source DX SHA256:
  `0edab556302273db41736993cdd041e73b1894419a623526c91f458b5fcfdc2e`.
- Original frame SHA256:
  `68537352277a0431c8a8363cf09d25cce7d693030d5cc47dc691b86bca65da4f`.

The final preset uses that perspective for Vehicle Select. Smallcarsheet uses
the separate side camera already accepted by the user, unchanged by this
camera refinement. Calibration overlay, source hashes and ranked parameters
are retained privately. No native executable analysis or recovered camera
settings are claimed. A single stock reference is not cross-vehicle parity.

### Source-viewport clipping correction

The user correctly spotted clipping in the first perspective Subaru render.
Fitting only projected width/height did not centre its asymmetric perspective
projection: the nose reached x=-26.44 and the wheels y=337.67 in a 512×320
source frame. Later PNG normalization could not restore these missing pixels.
The renderer now centres the complete projected bounds using an image-plane
offset, keeps a 12-pixel guard, and rejects clipping. Camera angle/distance and
vehicle geometry do not change. A dedicated asymmetric-perspective regression
and a source-alpha guard check cover this failure before final normalization.

## Why the previous Subaru icon stood out

V412 was technically correct: admitted DXT dimensions/CRC, bank frame mapping,
alpha and a bounded image. However, its GT3 image was only 51×27, used a different
viewpoint/contrast, and exposed low-resolution palette/detail differences when
enlarged. The old race thumbnail reused a three-quarter source although native
smallcarsheet pictures are side views. Fixing position alone cannot fix these
source-image differences.

Subaru now uses its actual final MR `complete.dx` and DXT textures to render
separate high-resolution source images. Its existing body and wheel assets
are read, never edited. The same calibrated camera is used for a Navara
re-render, permitting a direct original / reproduction / Subaru comparison.

## Reusable implementation

- `addon_sdk/ui_preview.py`: opt-in `mr-native-v1` profiles for each role;
  bounded exposure, highlight shoulder, premultiplied area reduction, fixed
  baseline and role-specific composition. Existing sidecars preserve their
  previous pixels unless they opt in.
- `generate_vehicle_ui_previews.py`: optional offline authoring tool, separate
  perspective frontend / orthographic side cameras, vertex-normal diffuse
  light, 512×320 sources. Maximum 200,000 vertices / 100,000 triangles.
- `vmesh_raster.Camera.distance`: optional perspective; default `None`
  preserves existing diagnostic camera behaviour. No game runtime dependency.
- Corpus and silhouette calibration tools accept explicit user-owned paths.
- GT3 extraction remains optional and unchanged. GT3/custom PNGs can opt into
  normalization, but their single source view cannot be re-projected into a
  different view. No GT3 or MR image is bundled in SDK source.

These are explicit authoring defaults, not a universal image classifier or a
new UI subsystem. The source renderer does not emulate native environment
reflection, mipmaps, lighting, or perspective-correct texture interpolation.

## Candidate validation and remaining human checks

Project build/verify, runtime verification, launcher build/preflights and an
independent pixel/references/ZIP audit all pass for the final candidate.
All **196** SDK/converter regression tests pass. Final visible bounds and
source-viewport guards are recorded in `reports/final-ui-audit.json`.
The user-accepted side preview is byte-identical before/after the perspective
camera refinement. The full validation records exact pixel recomposition
through the SDK, texture dimensions/CRC, references and package integrity.
Only two runtime files may change:

- `DataGx/Frontend/VehicleSelect/carsheet_032_000.dxt`
- `DataGx/Frontend/RaceResults/smallcarsheet_030_000.dxt`

All 191 runtime resources are compared against the sealed V412 baseline;
prepared Data.sma is checked against its prior manifest SHA when omitted from
the older private ZIP. All geometry, wheel shelf/recess, tyres, fitment,
collision, physics, body/livery, native operations, scene controls, bank records
and other vehicle resources remain byte-identical. No original executable or
graphics DLL is changed. No game was launched and nothing was pushed/published.

Runtime checks remain: native UI scaling/filtering, alpha edges against the
actual menu background, selection/reentry, and race/Results rendering. An
offline camera match and package validation do not prove the in-game result.
This pass stops at the candidate and does not start Evo IV.
