# V-MESH4.2 - GT3 material and texture restoration

**Status: READY_FOR_HUMAN_RUNTIME. Not runtime-qualified. No runtime PASS is claimed.**
Starting point: `v41-exp-001` (LOD0 geometry, wheel anchors, +0.12 m stance, collision refit, ID27/T2 identity, V-LAUNCH1 launcher
with graphics-proxy support). V-MESH4.2 changes materials only: the same LOD0 triangles, the same hull (hull vertices identical to
V-MESH4.1, verified), plan SHA256 `567a27a8...` unchanged; `wheel.dx` byte-identical. GT3 data, derived DX/DXT, source maps and the
bundle stay private under `.research-output/vehicles/vmesh42/`.

## Preview first

`preview/sheet_gt3_vs_vmesh41_vs_vmesh42.png`: columns = GT3 original (OBJ + PNG, same renderer and camera), V-MESH4.1, V-MESH4.2;
rows = side, front 3/4, rear 3/4, front close-up, bonnet. The renderer (`tools/vmesh_raster.py`) samples textures, blends alpha per draw
and modulates vertex colour; it does **not** simulate the engine's environment mapping, lighting or mip-mapping, so it shows UV
mapping, alpha and colour, not final shading.

## What was wrong in V-MESH4.1 (black gaps and triangles around bonnet, grille, headlights)

Every GT triangle was drawn with a single donor texel, so (details: `reports/artifact-analysis.json` of the build):

* grille, intercooler mesh, vents, bumper-corner pieces and lamp housings are *cut-out* textures (texels with alpha 0 or 25 %);
  V-MESH4.1 drew them as solid black or solid blue, producing black blocks and triangular slivers where the original shows mesh,
  stickers or nothing;
* lens materials with 43 % transparent texels were solid black; 36 triangles whose texel footprint is completely clear were drawn
  as opaque surfaces (V-MESH4.1 kept 84 "unsupported overlay" triangles solid);
* decals (SUBARU lettering, STi, Pirelli, flames) were dropped or flat blue.

## How V-MESH4.2 restores the materials (reusable pipeline)

`tools/gtmat.py` (format primitives) -> `tools/vmesh_materials.py` (planner) -> `vmesh_geometry.build_candidate(material_plan=...)`.

1. **Alpha is judged per UV footprint of each triangle**, not per texture (most GT textures are mostly unused atlas space). PS2
   alpha (0x80 = opaque, exported as `2a+1`) is normalised: PNG alpha >= 246 is opaque (249 = 0.97), 65 is 25 %.
   Classes: *opaque*, *clear* (nothing visible: dropped, 36 triangles listed in `dropped-faces.json`), *cutout*, *translucent*, *mixed*.
2. **Routing by what the texels need.** Opaque triangles -> opaque donor pools; cutout/translucent/mixed -> alpha-blend donor pools
   (existing draws whose alpha-enable flag is switched on, R4E E4 mechanism); never replaced by an opaque surface. Opaque flat-black
   regions (trim, cabin shell) keep the donor black trim draw unchanged.
3. **UV islands** (triangles of one material/pass with overlapping UV boxes) are packed with area-adaptive resolution into the
   donor textures. Donor DXT size and header are fixed (the writer boundary), so a pool is a donor draw present once in both
   `car.dx` and `complete.dx` whose texture is not shared with crew, wheels, glass, lamps or trim. Pools: 14 donor textures
   (sidenav1 128x128 and underdash 128x128 are the large ones), see `material-report.md`. Colour is alpha-weighted-averaged (no dark
   halos), edges get a 2-texel replicated gutter, transparent texels get neighbour colour (no fringe under bilinear filtering).
4. **Lamps and glass keep their donor draws** and get the packed GT texture of their role: head lamp lens (`headlamp-tga`, alpha
   cut-outs preserved by the donor's alpha draw), tail lamp (`backlightjnavp-tga`), window panes (`windscreen32-tga`, GT pane texture
   with its blue sun strip; alpha x 0.7 so the interior stays visible, `--glass-alpha-scale`).
5. **Vertex colour is white** on GT-textured draws (texture as authored); the donor's 0.4-0.7 greys were calibrated for donor textures
   (`--vertex-gray`).
6. **car.dx and complete.dx share the plan**: same textures, same UVs, same alpha flags per pool (verified: 1822 source faces in both,
   0 texture/UV mismatches).
7. **Validator extension** (tracked source `src/master_rallye/vehicle_project.py`): a topology candidate may now also toggle the
   alpha-blend flag of existing draws (only when the alpha-test byte is 0 and the draw is a vehicle draw); every other material field
   remains locked (test: tampering with the alpha-test byte is rejected). Together with V-MESH3's wheel-bounds fallback this is the
   only tracked source change of the V-MESH line.

## UV orientation evidence

DX UV is treated as v-up on an upright image (identical to the GT OBJ convention, so GT UVs pass through unchanged). Offline check
against retail data: rendering the stock Navara `complete.dx` with its own DXT files and UVs under both conventions shows
"NAVARA", "NISSAN" and the race number "258" upright and legible with v-up and upside-down with the flipped convention
(`.research-output/vehicles/vmesh42/study/orient_*`). Runtime confirmation of V-MESH4.2 itself is still pending your test.

## Offline validation (build `reports/validation-report.json`)

* mrtool `validate-vehicle`, `addon project-validate/build/verify`, `runtime-prepare/verify`, launcher `--verify` and
  `--verify-launch-environment` (game directory `d3d8.dll` accepted as an audited proxy): all PASS.
* 17 DXT files (14 pools + glass, head lamp, tail lamp) rebuilt, header and size identical to the donor files, decode round trip exact.
* Source map: every non-cabin triangle matches its source face exactly (0 mismatches); source UVs, objects and materials of every
  triangle stay in the private map together with the remapped DX UVs.
* Material mapping: footprint colour/alpha of every routed triangle compared between the GT texture and the *decoded final DXT*:
  mean colour error 1.2 (0-255), 8 of 1482 triangles over tolerance (thin slivers and tiny islands); no opaque-pool triangle
  has a transparent footprint; no pool/flag mismatch; nothing rejected, nothing degraded to a swatch.
* Hull vertices identical to V-MESH4.1; triangle count +118 (car.dx 2427, complete.dx 2897; alpha decals now included).

## Reproducible build and test package

```powershell
$env:PYTHONPATH = 'src;.'
python tools/build_vmesh42_impreza_experimental.py `
  --gt-dir ".research-output/vehicles/gt-import/gt3-dumps/sb0097/sb0097_dump/CarModelSet" `
  --retail-root "D:/Game/Master Rallye/corpora/retail" --retail-exe "D:/Game/Master Rallye/MRallye.exe" `
  --before-candidate-dir ".research-output/vehicles/vmesh41/v41-exp-001/runtime/resource-root/DataGx/Vehicles/ImprezaProto" `
  --output-root ".research-output/vehicles/vmesh42/v42-exp-001"
python -m unittest tests.synthetic.test_gtmat tests.synthetic.test_vmesh_materials tests.synthetic.test_vmesh_lod0 tests.synthetic.test_vmesh_arch tests.synthetic.test_vmesh_geometry
```

Knobs: `--glass-alpha-scale`, `--vertex-gray`, `--ride-lift`. Launcher/proxy rules are the V-LAUNCH1 ones
(`research/vehicles/sdk/vlaunch1/graphics-proxy-compatibility.md`); the launcher is pinned to this bundle:

```powershell
$exe = 'D:\Game\Master Rallye\MRallye.exe'
$bundle = 'D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\vmesh42\v42-exp-001\runtime'
$loader = 'D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\vmesh42\v42-exp-001\launcher\mr-runtime-launcher.exe'
& $loader --verify $exe $bundle
& $loader --verify-launch-environment $exe $bundle
& $loader --integrated $exe $bundle
```

## What to check in game (screenshots please)

1. **Livery (frontend and race):** blue body, yellow swoosh and stars on both sides, SUBARU on roof/bonnet/doors, STi and Pirelli stickers.
   Mirrored, upside-down or shifted decals mean a UV-convention problem (tell me which side/which way).
2. **Brightness/colour:** too dark or too bright versus the preview? (vertex colour 255 + the donor environment stage on opaque pools.)
3. **Bonnet, grille, headlights, bumper corners:** black gaps/triangles gone? Headlight lens and housing look? Grille mesh visible?
4. **Transparency:** no see-through holes in the body (look into the engine bay and through doors/fenders), no flicker or sorting
   artefacts where decal layers overlap (alpha-blended pools: draws 0, 11, 14, 15, 23/19), glass tint/transparency, crew visible.
5. **Race vs Vehicle Select:** identical look. Wheel arches, wheels, damage, collision as in V-MESH4.1.
6. **Damage and glass breaking:** does damage still deform/darken the body textures sensibly? (damage reuses the same draws.)
7. Proxy: free camera/HUD toggle still work; any new artefact versus V-MESH4.1.

## Remaining limitations (not hidden)

* **Resolution:** all body textures share 55 k texels of fixed-size donor DXT space (14 pools) instead of GT's several times larger
  atlases; densities 425-2200 texels per m2 (livery 1300), glass 180, tail lamp 2100, head lamp 10000. Stickers and thin lettering are soft, small ones blurry. Changing DXT
  dimensions is outside the runtime-confirmed writer boundary and is not attempted.
* **Alpha is blend, not test.** The donor engine offers alpha blending for existing draws (alpha-test selector stays locked). Blended
  pools are drawn after the opaque ones, depth-tested without depth write, sorted per object: coplanar decal layers rely on the same
  depth test as in GT; sorting/z-fight artefacts are possible. Alpha is switched on for exactly four draws in both files (0, 11, 14, 15:
  `underdash`, `grillenav`, `nisbackbadge`, `inbak`; none of them has an environment stage); lamps/glass use the donor's own alpha draws.
* **Environment mapping:** donor paint pools keep their `silverpaint` reflection stage (mask 7, texture alpha forced to 255), GT's
  reflection shells stay excluded; the amount of shine differs from GT and is untested.
* **Brightness** (vertex colour, alpha 0.7 on glass) is derived, not calibrated in game.
* **PS2 alpha decoding** (0x80 = 1.0, PNG `2a+1`) is inferred from the exported value set {0, 65, 99, 199, 249, 255}.
* **Not touched:** wheel/tyre textures (donor wheel UVs belong to the donor model), crew textures, brake-light/glow draws, damage
  decal logic, cracked glass (hidden fillers as before), `colour-tga` (flat blue placeholder for the addon colour mechanism).
* **Per-draw sharing:** the filler draws that share a donor texture with a pool (e.g. blight draw with `backlightjnavp`, extra windscreen
  draws with `windscreen32`) show the packed texture too if the engine ever draws them; they are hidden fillers today.
* **Tiled UVs** (slightly over 1.0 on a few lamp/trim islands, tiled cabin fabric) are represented inside their rectangle at reduced
  resolution; interior fabric is a flat swatch of its true colour.
