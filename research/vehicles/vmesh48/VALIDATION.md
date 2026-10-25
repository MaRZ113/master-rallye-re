# V-MESH4.8 final offline validation — v48-exp-003

Date:2026-10-22. Branch:research/vehicles. Status:PASS_OFFLINE_NOT_RUNTIME_QUALIFIED.

## Hood result and evidence

Experimental v48-exp-002 showed a black U around the scoop. The source texture contains4490 zero-alpha texels with blue RGB(0,23,65), almost matching dominant opaque RGB(0,27,69); filling that cutout with black backing caused the visible patch. The final opt-in palette heuristic restores solid paint coverage and the six black upper-paint backing faces are no longer generated. This is an inferred import policy, not confirmed GT3 renderer semantics. Original source RGB/UVs/positions remain unchanged.

Final resource audit samples7560 interior points on the repaired source faces:403 points had clear coverage in V4.7; all7560 are solid chromatic paint in the final candidate. The black upper-paint underlay count is0. This proves the sampled coverage/material correction, not all-view watertightness. The actual hood image was inspected after serialization. The black U is gone; source paint variation remains. Actual game reflections require the user's test.

Private comparison:preview/hood_v48_exp002_vs_exp003.png (left experimental black patch; right final paint). preview/index.html includes V4.7/final body, wheel and reflection-control comparisons. All previews are software approximations without native environment mapping, lighting or mipmapping.

## Additional phase corrections

- Structural cutouts use full coverage alpha255/0 with reflection0.58 carried in helper RGB; this reduces alpha-test edge erosion. Genuine masks remain cutouts.
- Lamp glass has112 triangles with120 shared generated vertices per frame, rather than a different offset on every triangle. Native blend flags1,0 and glass helper are retained. Swatch RGBA110,130,150,67. This fixes offset disagreement; native blend sorting and close-up appearance await in-game validation.
- Seven bounded recess collars include the rear plate and front grille/vertical slots. They reduce local see-through gaps; they are not a globally watertight body reconstruction.
- Stock Master Rallye tread is byte-identical to donor. Sidewall samples the donor annulus. Rim gaps are dark opaque RGB9,10,12 with zero reflection; wheel alpha gates remain0,0. Accepted radius0.3762008m and rim ratio0.80 are retained. Complete/race wheel embedding delta is below0.000001m. Race anchors remain the H1 donor-hub hypothesis.
- Paint livery priority atlas128-square gives Pirelli3.81x, stars3.67x and SUBARU lettering2.51x linear UV texel scale compared with V4.7. STI, oval badge and existing small technical decals retain previous density. This does not create additional source detail. Tradeoff:24 interior-mask triangles use a32-square blend atlas (0.383x previous linear density), retaining their alpha behavior.
- Rear graphic uses four original source faces. It is a private approximation composed from existing source artwork, not a recovered original rear bitmap. Original GT3 wheel OBJ remains empty; wheel geometry is donor reconstruction.

## Checks completed

- 106 synthetic tests passed,0 failures (reports/focused-tests.log).
- Project/compiler/bundle validation and native launcher build passed. Launcher --verify and --verify-launch-environment passed; the game was not launched.
- 3802 source-face records compared across car/complete; maximum source-position delta0m. Car/complete texture/UV routing matches. Existing collision hull parity passes.
- Final native material selector audit passes.1494 texture footprints checked, mean RGB error1.55 with21 tolerance outliers: finite atlas resampling remains a limitation, not pixel parity.
- Material-aware H1 tyre clearance sampling reports no visible body penetration. This is offline sampled geometry, not suspension/steering qualification.
- Candidate ZIP CRC passes,202 members. Review archive is separately refreshed with final source/docs/tests/reports and CRC-checked. Proprietary source meshes/textures and converted runtime assets are excluded from the review archive. The candidate itself remains a private local derivative.
- Retail EXE SHA256 remains bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4. No installed graphics DLL edits, Randomizer work, staging/commit, push or publication.

## Final artifacts

- Candidate: .research-output/vehicles/vmesh48/v48-exp-003/review/v48-exp-003-candidate.zip
- Candidate SHA256:659f53696135b8b210ef213bd23a621be515fc7b6720e9bd5f696313eebb3e06
- car.dx SHA256:332b2b70db4e0d7d8a99ffdd00033a4e62ac4a0b55805cf6c154c111e62505c3
- complete.dx SHA256:179e0256d0ec67fca8aeb5cd4311f91b1ba46ad2d8d28c5df4116a2240ca4777
- wheel.dx SHA256:f78b7d6a5af4eb732bccf1f79784f413f25299b0c329bb8290da0ae6b5793b07
- Review: .research-output/vehicles/vmesh48/v48-exp-003/review/vmesh48-review-archive.zip

Use the candidate's HANDOFF.md for verification and manual launch instructions. Stop here for the user's frontend/race test, with reflections on/off and close-ups of hood, lamps, front recesses, rear plate and wheels. Superseded v48-exp-001/002 are retained privately for diagnosis and should not be tested as the final candidate.
