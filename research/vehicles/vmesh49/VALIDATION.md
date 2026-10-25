# V-MESH4.9 — final validation

Final local candidate: `.research-output/vehicles/vmesh49/v49-exp-004`. Before reference: `.research-output/vehicles/vmesh48/v48-exp-003`. Status: **PASS_OFFLINE_NOT_RUNTIME_QUALIFIED**. No in-game run was performed.

## Results

| Issue | Actual resource change | Evidence and remaining boundary |
|---|---|---|
| Outer headlight backing | Whole-triangle generated black backs removed;8 original circular cap faces remain opaque; original upper housings and112-triangle shared glass shell retained | Both DX frames audited. Glass/cap appearance, sorting and native reflections require the user's test; source lens detail is limited |
| Bumper rectangles/overlap |8 originally clear exterior swatch faces no longer forced opaque; black backs beneath decorative masks removed | Declared source omissions audited, genuine dark trim/intakes retained. This does not promise every all-view gap is closed |
| Upper grille | Source material has2.15x previous linear UV texel density; bridges restricted to4mm, collar padding6mm | Source paint vertices unchanged. Aliasing is reduced in the offline view; low-resolution source masks and native mipmaps remain limitations |
| Rear logo | Higher atlas priority plus preserved lettering RGB, replacing the prior flat yellow silhouette |1.32x previous linear texel density. SUBARU is recognizable in the final close-up. Artwork remains an authored source-art approximation |
| Rim depth | Stock-derived shallow bowl, about20.05mm deep; redundant centre cap removed | Width/radius/envelope, hubs and tyre tread/inboard geometry remain unchanged. Gold rim RGB is retained; metal reflection alpha becomes217 instead of26. The outboard rubber shoulder uses9 smooth rings with tangent normals and stock tyre palette sampling. No race placement/physics correction |
| Brake Glow | Four explicit source lit triangles plus28 stock halo triangles placed in the existing case2 | Original state controls/materials retained; case1 has no lit/halo surface. Native EXE switches case2 above brake0.1 and case1 otherwise. Actual braking response is pending |

The static tail-light surface remains identical between car/complete. `complete.dx` has no native brake state group; its preview stays unlit. Do not add permanent halo geometry to compensate for that difference.

## Regression checks

- **116 tests passed**,0 failures. Includes clear exterior swatches versus internal caps, shared constant use across lamp/non-lamp objects, mask density priority, rim envelope/tyre preservation, repeated-recess rejection, native case2 ownership and unknown-layout rejection. Earlier phase defaults remain covered.
- Project validation, project compilation, author verification, runtime preparation and bundle verification pass. Native launcher builds; `--verify` and `--verify-launch-environment` pass. No `--integrated` launch was run.
- **3794 retained source-face records** compared across car/complete: maximum position delta0m. Each new source map contains1897 records:1620 exact checks and277 range-only checks inherited from cabin processing. Existing original UVs/geometry remain unchanged; destination atlas UVs are reallocated as reported.
- Car/complete routing has1897 shared faces and0 texture/UV mismatches. Frontend wheel embedding error is at most`5.96e-8m`.
- Collision suffix bytes match V4.8 exactly. All hub transforms and wheel width/radius extrema match. Tread and inboard sidewall attributes/topology match; outboard tyre annulus remains while only its redundant centre cap is removed. Tread and inboard-side texture files match V4.8 byte-for-byte; stock tread matches retail. The outboard annulus is sampled from the original stock tyre palette with a1.5-texel guard beyond the old baked rim boundary. Rim metal alpha changes only where it was nonzero; dark spoke gaps stay0 and opaque.
- Of187 sealed resources,178 are byte-identical. Only3 DX files and5 DXT files change: `car.dx`, `complete.dx`, `wheel.dx`, `frontwa-tga.dxt`, `headlamp-tga.dxt`, `underdash-tga.dxt`, `mercwheel64-tga.dxt`, `nevwheel-tga.dxt`. The permitted user-editable `options.xml` differs because the previous tested root contains user settings. Physics and other nonvisual resources have0 changes. Unindexed user player-state/backups in the previous test root are excluded from comparison.
- **1486 material footprints** checked: mean RGB error1.51,15 tolerance outliers,0 opaque triangles with transparent footprints,0 pool alpha-selector mismatches. This is not pixel-perfect GT3 parity.
- All edited DXT files retain stock dimensions, wrapper/header and exact RGBA round trip. The wrapper uses uncompressed BGRA, so no block-compression repair was needed. UV density, source alpha/RGB interpretation and atlas downsampling explain the decal changes.
- Optional compact free-rectangle packing reuses space that the shelf packer wasted. The final128-square livery atlas gives the rear graphic1.32x linear UV density while preserving general SUBARU lettering, Pirelli and stars at1.00x V4.8. Their source art and placement remain intact. The final resource audit rejects regression of these main livery densities. Full source resolution and uniform perceptual sharpness are not claimed.
- Native brake textures match the donor, and case labels/tags/controls remain unchanged. Exact EXE bytes, PE address mapping, REA evidence identities and independent assembly are retained in ignored phase scratch; the short evidence summary is in `reports/native-brake-evidence.json`.

## Reflection and state previews

`preview/index.html` includes before/after body/wheels, window close-ups, reflection-control views, brake case1/case2 and reflection OFF/ON diagnostics. Brake images explicitly select the recorded cases offline. Reflection OFF renders albedo; ON adds a constant average helper colour times texture alpha, preserving coverage. It does **not** reproduce native environment coordinates, lighting, mipmapping or exact brightness.

Serialized helper bindings, cutout/opaque/blend gates and unchanged coverage between those diagnostic paths were checked. Actual reflections ON/OFF regressions remain a runtime boundary. Recommended user checks: headlight housing/glass without hollow cavities; front rectangles/overlaps; grille gaps and aliasing; rear logo; rim depth; and a fixed rear race camera with brake released/pressed. Steering/suspension/wheel offset qualification is deferred. Separate wheel close-ups use explicitly illustrative directional lighting derived from serialized normals; they are not native specular renders.

## Artifacts and scope

- Private runtime ZIP: `review/v49-exp-004-candidate.zip` with `HANDOFF.md` and launcher verification/manual-test instructions.
- Before/after gallery: `preview/index.html`.
- Clean source/docs/tests review archive: `review/vmesh49-review-archive.zip`; proprietary input/converted assets and diagnostic image bulk excluded.
- Detailed audit: `reports/final-offline-audit.json`; tests:`reports/focused-tests.log`; changed-source list:`reports/phase-source-files.json`.
- Model-specific editable density/depth bounds:`research/vehicles/vmesh49/subaru-cleanup.json`. Reusable helpers contain no Subaru material IDs. The brake importer currently admits the verified stock layout only; generic processing is not a GT4 qualification claim.

Retail EXE remains SHA256`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; installed graphics proxy preflight reports approved hash`eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`. No original EXE/installed DLL edits, Randomizer work, staging/commit, push or publication. Superseded intermediate v49-exp-001/002/003 are retained privately and are not the final test package.

## Package identity

Candidate ZIP SHA256: `bb151a606b6e0461473df934866f375493435ff95e64d5eb53147e8d271680b2`.

Compiled runtime resource hashes (the car source candidate hash differs because the project compiler reapplies the inherited collision transform):

- car.dx:`5769fbdf5e77baeb7de62cabd6005cb313461d14128ef61523b1a534ae81e3b9`
- complete.dx:`f88bfc70284090ec228eff91241e14917b2464004c116abb1b2ed0552f8a6f3f`
- wheel.dx:`3e56f0ee1815519a417329599086bc2453e454431bd533de75e92f0e454a74c2`
