# V-MESH4.7 final candidate and offline evidence

Final candidate: **v47-exp-003**, including the user's requested glass-like lamp layer. Development outputs v47-exp-001 and002 are superseded. They are not the final handoff.

## Verified in serialized output

- 99 focused tests pass. The new coverage exercises reflective paint masks and native alpha-test flags, retained constant-black lamp surfaces, translucent glass swatch isolation, larger coordinated wheel profiles, tread/sidewall texture edits and bounded edge bridging. Existing alpha, geometry, LOD, arch and material-writer cases pass.
- Vehicle/project validation, project build, author bundle verification, runtime prepare/verify, launcher build and both launcher verification modes pass. No game launch was performed.
- In both frames **99 paint-mask source faces change from non-environment to environment-enabled alpha-test draws**. Ordered slot identities remain fixed; only existing reflective capacity is used. Solid mask texels have alpha148 (> native reference128), holes retain zero. All 891 opaque paint faces remain reflective too. This corrects a verified material discontinuity; it does not prove the photographed hood/rear appearance has been eliminated in game.
- **16 original constant-black source faces are restored per frame**. Eight are the lamp-core quads; these now use the native lamp helper. Other recovered black swatches close technical surfaces. No globally clear paint overlay was made opaque.
- Per frame **110 source-linked cavity-back triangles** generate220 two-sided triangles; **26 bounded paired edges** generate86 additional triangles (degenerate halves are omitted). Eight supported edge-pair candidates are skipped. Maximum configured gap20mm, backing depth4mm. These local interior closures do not imply a watertight whole vehicle.
- **112 source reflection-shell triangles per frame** form the requested optical overlay, offset outward1mm. Final lamp glass uses native car draw35 / complete draw24, flags(1,0), helper `glass-tga`, sampled RGBA(110,130,150,67). It blends over opaque internal housing. This is a glass-like conversion using native material behavior, not original GT3 glass-shader reconstruction.
- **3,770 preexisting source-face records** compare with V4.6 at exactly zero position delta. All44 main glazing faces stay on the native blend path. Generated closures/glass are reported separately and never replace original source-map records.
- Rim/tyre radius ratio is **0.80**, up from approximately0.60. Rim radius0.30096m; tyre radial envelope0.37620m; half-width0.12852m. Wheel axis and H1 hub positions are retained. New wheel:405 vertices /468 triangles. Four embedded frontend copies match the race mesh within5.96e-8m. The ratio is a configurable visual setting, not an exact measured GT3 dimension. Rubber texture is procedural and coordinated across tread/sidewalls; gold disc imagery is source-derived. Spoke openings remain opaque dark imagery.
- Alpha-aware fitment checks **319,460 visible samples**, skips11,632 masked samples and finds zero sampled tyre/body penetrations for all four H1 hubs. Fixed assumed anchors and static pose only; suspension/steering clearance remains unqualified.
- Texture validation checks1,490 footprints: mean colour error1.63/255, seven outliers. No opaque source-coverage violations. These finite atlas samples do not establish pixel parity; the prior V4.6 result had16 outliers over1,482 checked footprints, a different routed set.
- The unchanged original EXE SHA256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Existing graphics DLL and Randomizer were not edited. No staging, commit, push or publication.

## Package

`review/v47-exp-003-candidate.zip`: **355,037,998bytes**,202 members, CRC PASS.
SHA256: `45e12dc64aea7e4bf8749fbe6270bd596195bea02511e86beeb449344020e184`.

The separate `review/vmesh47-review-archive.zip` contains source, documentation and validation evidence, without GT3/retail models, textures or binaries. All private derived candidates and previews stay under the ignored `.research-output` directory.

## Visual review and remaining work

Open `preview/index.html`: V4.6/V4.7 wheels, body, front detail, window/cowl close-ups and encoded reflection controls. The latter show material alpha/coverage and are not rendered environment reflections. The software preview does not reproduce game lighting, environment mapping, mipmaps or full sorting. In particular, it cannot validate the requested glass highlight strength.

The user has confirmed disappearance of V4.6 window gaps. V4.7 still needs the user's in-game review of lens glare/visibility, the hood outline and rear patches, paired front-gap closures and tyre texture/profile. Glass is intentionally translucent; a missed housing/backing area could still reveal the scene. Some lamp surfaces remain simplified and the source reference has finer optics and wheel detail. This stage does not claim every photographed defect is fixed.

Re-run the final independent audit with `tools/validate_vmesh47_candidate.py --stage .research-output/vehicles/vmesh47/v47-exp-003 --before .research-output/vehicles/vmesh46/v46-exp-002 --previews`. Use `reports/wheel-conversion.json` for final wheel geometry; `fit/race_wheel/wheel_dx` is the preceding donor-scale step.
