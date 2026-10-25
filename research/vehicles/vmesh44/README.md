# V-MESH4.4 — material passes, fender fitment and Subaru candidate

**Status: offline candidate prepared; human runtime test pending.** V-MESH4.4 keeps V-MESH4.3's body geometry, collision, addon identity, and reflection attenuation. It adds generic alpha-cutout routing and a measured race-wheel fitment rule. The output is private and ignored under `.research-output/vehicles/vmesh44/v44-exp-001/`.

## Pipeline changes

- `gtmat.pass_of()` now preserves three visible material states: opaque, cutout, and blend. Fully clear footprints are still dropped. UV-footprint classification remains per triangle rather than per whole source texture.
- Binary body/bumper cutouts share opaque donor pools, but those pools use the existing DX alpha-test selector (`+0x21`) with source alpha thresholded to the audited `GREATER 128` convention. Opaque texels retain alpha 148/255, so the reflection stage stays attenuated; clear cutout texels become zero. True translucent and mixed footprints keep alpha blending. Cabin-interior cutouts remain blended to preserve their existing texture packing around glazing. Headlamp cutouts use the same binary mask treatment while retaining the configurable 0.72 headlamp texture-alpha scale.
- DX attribute writing and project validation now allow the two known mutually exclusive material pass bits (blend or alpha-test), while continuing to reject any other draw-record or feature-mask changes. Alpha-test material edits are limited to existing physical vehicle draw records.
- `vmesh_geometry.wheel_scale_from_clearance()` grows the standalone race wheel toward the donor physics radius, capped by the measured arch-lip gap and a configurable safety margin. It leaves frontend embedded wheels and physics data untouched.

## V-MESH4.4 candidate result

- Race `wheel.dx` visual radius: **0.3373 m → 0.3774 m**; half-width: **0.1285 m → 0.1438 m**. The scale comes from the 0.3832 m donor physics radius and a measured 5 mm minimum front arch-lip margin. Offline body-sample checks report no tyre/body penetrations.
- Opaque, cutout, and true blend routes are recorded in `reports/validation-report.json`, including the draw pass bits. Opaque pools retain the V-MESH4.3 reflection scale of 0.58; headlamp scale remains 0.72.
- The exact body vertex and face construction is unchanged from V-MESH4.3. Correct alpha-test depth writes should reduce apparent holes and sorting artifacts around masked body and bumper texels, but this does **not** weld source vertices, repair geometric cracks, or fix the 7 source-normal disagreements reported by the converter.

## Fixed versus reduced

| Issue | V-MESH4.4 status | Evidence boundary |
|---|---|---|
| Reflection strength | **Reduced and user-confirmed in V-MESH4.3**, retained in this candidate. | V-MESH4.4 still needs the user's frontend/race test with reflections enabled. |
| Opaque vs cutout vs translucent classification | **Fixed in the offline pipeline.** Cutouts use alpha-test/depth-write; true mixed/translucent surfaces remain blended. | Sorting, depth interactions, and exact game alpha-test parity still need in-game verification. |
| Body/bumper see-through artifacts | **Reduced for binary cutout footprints.** | Mixed-alpha and translucent triangles still use blending and may remain washed out or order incorrectly. |
| Body seams/gaps | **Not geometrically repaired.** Alpha cutouts no longer need to fake holes with blended polygons. | Existing source topology and normal disagreements remain; the current evidence does not justify a generic spatial weld. |
| Headlight reflection | **Reduced** by the retained 0.72 headlamp alpha control; binary lamp cutouts now use alpha-test. | Brightness and lens appearance require runtime confirmation. |
| Race wheel fitment | **Improved offline** by clearance-bounded scaling to 0.3774 m. | No suspension, steering, or physics values were changed; race handling remains for the user's test. |

## Visual and offline validation

`preview/sheet_gt3_vs_vmesh43_vs_vmesh44.png` compares the GT3 reference, V-MESH4.3, and V-MESH4.4 with the same offline cameras. The raster preview does not emulate D3D8 alpha-test, environment mapping, lighting, or draw sorting; use it for silhouette/texture placement only. The supplied in-game screenshots remain the pre-V-MESH4.3 baseline, not V-MESH4.4 runtime evidence.

The builder checked source-map positions, frontend/race face consistency, DXT size/header preservation, collision parity, project compilation, runtime bundle verification, launcher preflight, retail executable hash, and wheel clearances. Synthetic tests cover the new pass-state and wheel-scale rules. None of these checks is gameplay confirmation.

Candidate package: `.research-output/vehicles/vmesh44/v44-exp-001/review/v44-exp-001-candidate.zip`. It contains the local runtime overlay and launcher; it excludes the GT3 source model and source textures. The source/docs/test review archive is `review/vmesh44-review-archive.zip`.

Rebuild from the private local GT3 input:

```powershell
$env:PYTHONPATH = 'src;.'
python tools/build_vmesh44_impreza_experimental.py `
  --gt-dir ".research-output/vehicles/gt-import/gt3-dumps/sb0097/sb0097_dump/CarModelSet" `
  --retail-root "D:/Game/Master Rallye/corpora/retail" `
  --retail-exe "D:/Game/Master Rallye/MRallye.exe" `
  --before-candidate-dir ".research-output/vehicles/vmesh43/v43-exp-002/runtime/resource-root/DataGx/Vehicles/ImprezaProto" `
  --output-root ".research-output/vehicles/vmesh44/v44-exp-001"
```
