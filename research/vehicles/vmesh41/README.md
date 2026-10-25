# V-MESH4.1 - Native LOD0 geometry import

**Status: READY_FOR_HUMAN_RUNTIME. Not runtime-qualified. No runtime PASS is claimed.**
V-MESH4 (`v4-exp-001`, tools `vmesh_*` and its docs) is the untouched reference; every V-MESH4 output still rebuilds
byte-for-byte (`car.dx` `db02354d...`, `complete.dx` `191fa49d...`). V-MESH4.1 changes only the *source geometry and how it is
used*; wheel anchors, scale, ride lift (+0.12 m), collision refit, crew placement, cabin inset, glass texture edit and the
ID27/T2 addon identity (plan SHA256 `567a27a8...`) are the same. GT data, derived files, source maps and the bundle stay private
under `.research-output/vehicles/vmesh41/`.

## Finding: LOD0 already contains what V-MESH3/4 reconstructed

`model0.lod1.obj` (2263 triangles) has no wheel openings: its arches are texture-alpha cut-outs on solid panels, so V-MESH3 carved
them (alpha sub-triangles) and V-MESH4 cut them analytically (24-gon prism + liner). `model0.lod0.obj` (3435 triangles) has the
openings, wheel-house tubes, wing legs and mirror/mast details as real geometry (renders:
`preview/raw_lods/sheet_lod1_vs_lod0.png`). Details in `comparison.md`.

## What V-MESH4.1 does

* **Geometry:** `BuildOptions(arch="native")` - no cut, no relief, no subdivision, no generated surface. Every emitted body
  vertex is the transformed source vertex (verified, see below). The arch contour is the source contour.
* **Classification (`tools/vmesh_lod0.py`, content driven):** GT3 `MatN_TexM` indices are per-LOD (`Mat6_Tex10` in LOD1 = `Mat6_Tex37`
  in LOD0), so roles come from data: structural object names (`*reflection*`, `*_tail_lamp_on`, `*tail_lamp_off`), the `Mat-1/1/2/4/6`
  class, texture alpha/luminance (translucent dark Mat6 = glazing pane) and geometry (single-sided front-corner objects = head lamp
  units; their cut-out lens material = head lamp). Every decision has a recorded reason (`source-map/source-classification.json`).
* **Overlays (the LOD0-specific problem):** LOD0 uses mostly-transparent materials both as decals (stickers, vents, strips lying on
  another surface) and as the only surface (bonnet, a splitter piece). The V-MESH4 rule "drop mostly-transparent materials" would
  delete real surface. New rule: an overlay triangle is dropped only if another visible surface lies within 3 cm under it
  (`SupportIndex`); otherwise it is kept. LOD0: 166 decal triangles dropped, 84 unsupported ones kept.
* **Cut-out textures** (1-50 % transparent; in LOD0 their transparent area is small and decorative, e.g. 0.01-0.2 m2 per material)
  are no longer carved; their alpha is recorded, not applied.
* **Source identity for the material importer (private, `source-map/`):** per emitted triangle the DX draw/triangle index, source
  object, material, face number and the three source corners (vertex index, normal index, **original UV**); per source material the
  texture file, size, SHA256, alpha statistics, policy and the donor role(s) it was mapped to; the dropped decal faces with their UVs.
  `verify_source_map` re-reads the built DX and checks every non-cabin record against the transformed source face:
  1478 of 1478 triangles per file match exactly, 0 mismatches, 0 records without UV. The game files still use the temporary donor
  materials (single-texel donor UVs, donor draws, V-MESH4 paint and glass tint).

## Remaining stance/arch relationship

The native arches are centred on the GT wheel centre; the body is lifted 12 cm (V-MESH4 stance, kept). The arch is therefore not
concentric with the tyre: the gap is about 4.5-4.8 cm at the front/rear edges (minimum measured; 0 tyre intrusions at all hubs,
race and frontend) and larger above the tyre. This is the same visual language as a raised rally car. It is a trade-off between
"keep the stance" and "keep the source arch"; `--ride-lift 0.046` gives a nearly concentric arch (physical-ground clearance 0.10 m).

## Reproducible build

```powershell
$env:PYTHONPATH = 'src;.'
python tools/build_vmesh41_impreza_experimental.py `
  --gt-dir ".research-output/vehicles/gt-import/gt3-dumps/sb0097/sb0097_dump/CarModelSet" `
  --retail-root "D:/Game/Master Rallye/corpora/retail" `
  --retail-exe "D:/Game/Master Rallye/MRallye.exe" `
  --before-candidate-dir ".research-output/vehicles/vmesh4/v4-exp-001/runtime/resource-root/DataGx/Vehicles/ImprezaProto" `
  --output-root ".research-output/vehicles/vmesh41/v41-exp-001" `
  --blender "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe"
python -m unittest tests.synthetic.test_vmesh_lod0 tests.synthetic.test_vmesh_arch tests.synthetic.test_vmesh_geometry tests.synthetic.test_vmesh_gt3_to_dx
```

The driver builds the launcher from the current launcher source (the V-LAUNCH1 proxy-compatible one) and refuses to continue if the
result lacks `--verify-launch-environment`.

## Launcher, graphics proxy and first in-game test (human)

The launcher is bundle-pinned (resource index/manifest are compiled in), so V-MESH4.1 has its own launcher
`.research-output/vehicles/vmesh41/v41-exp-001/launcher/mr-runtime-launcher.exe`; the V-MESH4 `vlaunch1-final` launcher only accepts the
V-MESH4 bundle. Same policy as V-LAUNCH1: exactly one of the four audited `d3d8.dll` builds may sit beside `MRallye.exe`
(see `research/vehicles/sdk/vlaunch1/graphics-proxy-compatibility.md`); anything else fails closed. The game directory
currently contains a `d3d8.dll` with SHA256 `eb7ea3d9...` (the audited baseline build) and the launcher reports
`LAUNCH_ENVIRONMENT_VERIFIED graphics_proxy=approved-d3d8` for it (also checked, in an isolated copy, for the other three).

```powershell
$exe = 'D:\Game\Master Rallye\MRallye.exe'
$bundle = 'D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\vmesh41\v41-exp-001\runtime'
$loader = 'D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\vmesh41\v41-exp-001\launcher\mr-runtime-launcher.exe'
& $loader --verify $exe $bundle                      # RESOURCE_ROOT_VERIFIED files=187 ..., RUNTIME_BUNDLE_VERIFIED patch_operations=246
& $loader --verify-launch-environment $exe $bundle   # APPROVED_GRAPHICS_PROXY ... LAUNCH_ENVIRONMENT_VERIFIED
& $loader --integrated $exe $bundle
```

Check and report (screenshots; free camera and HUD-free capture with your proxy are welcome for the arch/glass details):

1. **Arches (race + Vehicle Select).** Source arch contour with its wheel-house tube: smooth, no jagged edge, no sparkle, no
   see-through. Wheels centred left-right; larger gap above the tyre is expected (stance). Full steering lock and bumps: does a tyre
   touch the arch or tube?
2. **Body detail.** Rear wing legs, mirrors, bonnet vents, bumpers, lamps; anything missing, doubled or z-fighting? Front lower bumper
   has no black grille now (it is texture detail in LOD0) - is that acceptable for this stage?
3. **Windows.** Same glass look as V-MESH4 (uniform tint, translucent), crew visible through it; any pane opaque/missing?
4. **Stance** unchanged versus V-MESH4 (skirt 0.178 m above physical ground).
5. **Glass damage, collision, damage deformation, brake lights:** as in V-MESH4 (known open points below).
6. With the proxy: launch works, free camera/HUD toggle work, no new artefacts compared with the V-MESH4 candidate.

## Unresolved (not hidden)

* **Materials/textures:** body detail that LOD0 expresses through textures (grille, intakes, stickers, vents) is not reproduced; the
  data needed is in the source map. 166 decal triangles are dropped, 84 unsupported overlay triangles are drawn solid in the paint/trim
  draw (alpha ignored), 277 cabin-shell triangles include a 24-triangle partly transparent piece drawn solid.
* **Arch/stance trade-off** above; tyre/arch clearance in motion (steering, travel) is not modelled.
* **LOD0 face density:** 2305 / 2775 triangles (car / complete) - back inside the donor envelope (2366 / 2761) except complete.dx
  exceeding the retail maximum 2761 by 14.
* **Glass damage states, glass tint/alpha, brake-light glow, cockpit camera, native proportions (H1 wheel anchor), physical tyre
  radius 0.383 vs visual 0.337, filler draws, hull refit:** unchanged from V-MESH4 (see `research/vehicles/vmesh4/README.md`).
* **V-MESH4 note correction:** the V-MESH4 README says the thin GT glass strips became opaque trim; in the code they were dropped by the
  overlay policy (80 triangles). V-MESH4 files are left untouched; V-MESH4.1 drops the analogous LOD0 strips deliberately
  (supported overlays) and lists them in `dropped-overlays.json`.
