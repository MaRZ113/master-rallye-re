# V-MESH4.3 — generic runtime material normalization and fitment

**Status: READY_FOR_HUMAN_RUNTIME. Offline-validated; not runtime-qualified.** This candidate continues V-MESH4.2 using the same LOD0 source geometry, wheel anchors, collision refit, addon identity and donor resource set. GT3 inputs and all generated DX/DXT, source maps, and packages stay under ignored `.research-output/vehicles/vmesh43/`.

## Changes

`tools/vmesh_materials.py` now has two reusable material controls:

* Opaque triangles still route only to opaque pools; cutout, translucent and mixed UV footprints still route to alpha-enabled blend pools; fully clear footprints are dropped. This preserves the V-MESH4.2 footprint classification and prevents transparent texels from being silently baked into solid surfaces.
* The opaque pools all use the donor's environment helper. Their packed texture alpha is now scaled to **0.58** (configurable) to attenuate that environment-stage contribution. The draw's alpha-blend flag stays off, and the RGB atlas content is unchanged. The headlamp texture alpha is scaled to **0.72** (configurable) to temper its unusually strong reflection while retaining the source cutout pattern. These controls are generic to donor reflection pools and the classified headlamp role; there is no `sb0097` draw-index special case.
* Wheelbase, donor hub spacing and GT wheel radius continue to determine body alignment and standalone `wheel.dx` scale via `plan_fit`. For this candidate the wheel scale is 0.8802; no manual per-car placement offsets were added. Race physics/tyre radius is not rewritten.

The reflection scales rely on the audited D3D8 material path where the reflection stage uses texture alpha. This is a controlled reduction, not proof that every broken reflection facet is fixed. The offline raster preview does not simulate the environment stage, lighting, mipmaps or game draw sorting.

## Issue status

| Goal | V-MESH4.3 result | Evidence limit |
|---|---|---|
| Body lighting/reflections | **Reduced** by lowering reflection-stage alpha on opaque pools. Same plan feeds `car.dx` and `complete.dx`. | Needs your frontend and race captures with reflections enabled. Artifacts from imported normals or reflection-shell intersections may remain. |
| Opaque / cutout / reflective material routing | **Classified offline** per triangle UV footprint; reflective opaque surfaces have a separate strength control. | Cutouts still use alpha blending because the candidate path does not change the alpha-test selector. Sorting and depth-write artifacts may remain. |
| Body and bumper transparency | **Reduced where clear texels are dropped and cutouts are routed to blend pools.** | Mixed/translucent surfaces can still look washed out or expose seams; alpha-test routing is not enabled. |
| Body seams / gaps | **Not geometrically changed.** Source mapping is preserved and both front-end and race files share the same transformed faces. | The preview can show topology and texture placement, not D3D8 reflection seams. Any actual cracks require runtime screenshots to localize. |
| Headlight reflections | **Reduced** with generic headlamp alpha scale 0.72. | Runtime brightness and lens transparency remain uncalibrated. |
| Race wheel fitment | **Aligned offline** from the measured GT axle gap and donor hubs; wheel mesh scale derives from wheelbase and GT/donor radius. | Physics wheels, steering and suspension are untouched; human race validation remains required. |

## Preview and validation

`preview/sheet_gt3_vs_vmesh42_vs_vmesh43.png` contains the GT3 source reference, V-MESH4.2, and V-MESH4.3 at matching offline cameras. The rasterizer does not implement environment mapping, so opaque body shading is expected to look the same in the V-MESH4.2 and V-MESH4.3 columns; the headlamp texture change is visible. This is not a before/after game capture.

The build's `reports/validation-report.json` records input hashes, candidate hashes, per-triangle texture/alpha mapping, draw flags, race/frontend consistency, collision parity, generated previews and tool validation. Expected invariants: unchanged `MRallye.exe` hash, no changes to the installed graphics proxy, matching source-face mappings between `car.dx` and `complete.dx`, and unchanged collision hull from V-MESH4.2.

Rebuild command:

```powershell
$env:PYTHONPATH = 'src;.'
python tools/build_vmesh43_impreza_experimental.py `
  --gt-dir ".research-output/vehicles/gt-import/gt3-dumps/sb0097/sb0097_dump/CarModelSet" `
  --retail-root "D:/Game/Master Rallye/corpora/retail" --retail-exe "D:/Game/Master Rallye/MRallye.exe" `
  --before-candidate-dir ".research-output/vehicles/vmesh42/v42-exp-001/runtime/resource-root/DataGx/Vehicles/ImprezaProto" `
  --output-root ".research-output/vehicles/vmesh43/v43-exp-002"
python -m unittest tests.synthetic.test_gtmat tests.synthetic.test_vmesh_materials tests.synthetic.test_vmesh_lod0 tests.synthetic.test_vmesh_arch tests.synthetic.test_vmesh_geometry
```

Optional conservative tuning: `--body-reflection-scale` and `--headlamp-reflection-scale`, each in `[0,1]`. The default values are intentionally exposed so the same pipeline can be reused for other donor-based vehicles.

The generated review ZIP contains source, docs and validation reports only. Private GT3 textures/models and generated candidate binaries are excluded.
