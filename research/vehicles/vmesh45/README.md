# V-MESH4.5 — correction of V4.4 alpha regression, panel continuity and tyre width

Status: **candidate for human runtime validation**. Work is confined to `research/vehicles`. Private input and derived candidates remain ignored. No game execution, push or publication is part of this stage.

## Confirmed regression

V4.4 used DX flags `(alpha_enable, alpha_test_selector) = (0, 1)` and treated them as independent exclusive modes. This was wrong. The original retail selector at `0x580360` first tests runtime `+0x22`, and skips both alpha suffixes when it is zero. Only then does `+0x23` choose `_alpha` or `_alphatest`.

| DX bytes +0x20/+0x21 | Effective native family |
|---|---|
| 0,0 | opaque |
| 1,0 | alpha blend |
| 1,1 | alpha test |
| 0,1 | still opaque; rejected by the corrected writer as an inactive selector |

REA/Ghidra evidence: `ev_b7bb165be1c04d9d308a93a4acec809d2f8e7d5b34f026c7fafb6849e41d48f3`. Assembly anchors: `0x580568` loads the gate; `0x58056d` branches past suffix selection; `0x5805bb` loads the second selector. A 96-byte read at VA `0x580568` was mapped by Ghidra to original file offset `0x180568` and independently compared with the original EXE bytes. Target SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The previously audited D3D8 alpha-test method writes depth and tests GREATER 128; see `research/r4d_1/alpha-path.md`.

The screenshots supplied on 2026-10-22 confirm the V4.4 regression in game. The old offline raster also ignored the gate/selector combination and did not emulate alpha test, so its comparisons were insufficient. The raster now distinguishes opaque, blend and depth-writing cutout. It still does not emulate lighting, environment mapping, mipmaps or the engine's complete sorting behavior.

## Generic pipeline correction

- `r4e_writer.py` and `vehicle_project.py` accept the three effective states above and reject `(0,1)`. Ordered texture slots and unknown draw bytes remain checked.
- `MaterialPlan(..., structural_coverage=True)` gives classified paint panels a solid-coverage policy: nonzero source alpha becomes solid; zero-alpha holes remain holes. This is an explicit **conversion heuristic**, not a claim that all GT3 alpha channels mean the same thing. Glazing, trim and cabin translucency are preserved. It prevents sole roof/trunk panels from being rendered as partly transparent merely because their source alpha contains 65/255 texels.
- Cutout islands use dedicated donor pools without environment mapping, separately from opaque paint and actual translucency. Their texture masks use 0/255 and their serialized selector is `(1,1)`. No Subaru material numbers or face IDs are hardcoded.
- Reflective opaque pools inherited different donor slot-1 helpers: silverpaint, whitepaint, chrome and perspex. The dominant helper by opaque surface area is selected automatically; other existing helper textures are resampled to that appearance with their dimensions and ordered slot bindings preserved. For this donor the canonical helper is silverpaint. Shared users are reported: the chrome helper also affects a wheel draw, perspex affects tail lamps, and whitepaint affects a retained crew draw. This side effect is confined to the candidate and needs visual review.
- The opaque reflection attenuation stays 0.58; the headlamp control stays 0.72. These values are independent of opaque shell coverage.

## Roof and trunk seams

There are two addressed material causes: essential panels previously routed through blend, and differing inherited reflection helpers across adjacent packed material pools. `reports/artifact-analysis.json` compares the effective before/after passes on spatial roof and trunk regions using the private face maps. Source-map position verification remains exact. Body vertices have not been moved or welded; no watertight-mesh repair or in-game seam elimination is asserted. Any geometric gaps or remaining source-normal discontinuities require the next runtime captures.

## Wheel protrusion and anchor investigation

V4.4 uniformly enlarged `wheel.dx`, taking tyre half-width from 0.12852 m to 0.14380 m as well as increasing its radius. V4.5 starts from the V4.4 radius and computes lateral scale separately from the original wheelbase fit. Half-width returns to 0.12852 m: each sidewall extends **15.28 mm less** from its hub. Alpha-aware silhouette checks then reduce the radial scale by 1.837 percent: vertical radius **0.37742 m -> 0.37049 m**, actual maximum Y/Z envelope **0.38324 m -> 0.37620 m**. The correction is derived from sampled front-wheel protrusion and a 2 mm target margin, not a car-specific coordinate. Normals use the inverse scale and the bounds footer is recomputed. No wheel-centre translation is baked into the shared spinning mesh.

This corrects excess tyre width, **not the physical track/axle transform**. Source `vehicles.xml` has donor `Dimensions/TrackWidthFront=1.7`, `TrackWidthRear=1.7`, `WheelBase=2.8`, and wheel radii 0.38. The donor mesh radius is 0.38323 and its embedded hub wheelbase is 2.95735: those are different measurements. V4.4's documentation incorrectly called the donor mesh radius a confirmed physical radius. The family reader `0x49b0c0` reads these dimension keys, but the exact race wheel-instance placement was not recovered in this bounded investigation. Arbitrary signed translations in shared `wheel.dx` would also rotate under steering/spin and are not a valid substitute for hub placement.

To change actual offset, the required control is the per-axle race hub/track transform, with frontend embedded hubs updated consistently. Its XML-to-instance mapping remains unverified. H1 uses `complete.dx` hub centres expressed in the race body frame; all offline fitment checks label that assumption explicitly.

## Validation and remaining limits

The prior diagnostic checked only five legacy body draw IDs and omitted most imported material pools. V4.5 supplies the actual generated role draws and adds alpha-aware sampling over all body-pool triangles. A circular approximation initially suggested 0.292 mm overlap; the actual wheel silhouette revealed **4.933 mm** sampled front overlap. The automatic radial correction removes all detected overlap: **270,490 visible samples tested, 11,336 mask samples skipped, zero samples inside any of the four fitted tyre outlines**. These are grid samples against the wheel's convex Y/Z silhouette extruded across its width, not a mathematical 3D intersection proof or suspension-travel validation. Legacy unmasked diagnostics are retained as geometry-only information.

The focused suite passed 92 tests including native selector persistence/rejection, black-rectangle raster regression, solid-panel versus glazing coverage, independent wheel width/radius scaling, actual tyre-outline geometry, writer/project validation and existing LOD/arch tests. Project build, bundle verify and launcher preflight also pass. Source-face maps have no position mismatches. The roof audit finds 14 previously blended faces now opaque; the trunk audit finds 28 now opaque and 2 now alpha-tested. Atlas resolution remains finite: 16 of 1,482 mapped triangles exceed the colour/alpha tolerance (mean colour error 1.33/255). These outliers are retained rather than treating classification success as texture parity.

Final local package: `.research-output/vehicles/vmesh45/v45-exp-002/review/v45-exp-002-candidate.zip`.
The candidate contains runtime overlay and a bundle-pinned launcher. It is private and is not for redistribution. The source/docs/tests review archive is `review/vmesh45-review-archive.zip`. GT3 source models/textures and generated source maps are excluded from the review archive.

Rebuild with the private local input:

```powershell
$env:PYTHONPATH = 'src;.'
python tools/build_vmesh45_impreza_experimental.py `
  --gt-dir .research-output/vehicles/gt-import/gt3-dumps/sb0097/sb0097_dump/CarModelSet `
  --retail-root "D:/Game/Master Rallye/corpora/retail" `
  --retail-exe "D:/Game/Master Rallye/MRallye.exe" `
  --before-candidate-dir .research-output/vehicles/vmesh44/v44-exp-001/runtime/resource-root/DataGx/Vehicles/ImprezaProto `
  --output-root .research-output/vehicles/vmesh45/v45-exp-002
```

After extraction, from the candidate directory: `launcher/mr-runtime-launcher.exe --integrated "<retail MRallye.exe>" runtime`. The builder ran verification-only launcher modes, never `--integrated`. Runtime qualification is pending the user's test of transparency, roof/trunk reflection continuity and tyre stance.
