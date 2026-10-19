# TRACK-GROUND1 final report: ground material parity and collision diagnostics (Turkey3)

Date 2026-10-19. Repository `master-rallye-re-general`, branch `master`, one local commit for this phase (not pushed). Original game files and corpora were not modified (see `runtime-validation.md`).

## Verdicts
| Item | Verdict |
|---|---|
| 1. Texture parity | PASS (offline). Orientation, thresholds, renamed textures, PS2-only fallback and DXT headers audited and tested; runtime A/B not performed |
| 2. Ground material parity | PARTIAL. 2,104 equivalent ground triangles keep the native PC material including the noise stage; the 1,916 replaced triangles have PC-quality base textures and the measured mean noise brightness but no noise detail. An experimental noise-stage candidate exists, unverified |
| 3. Candidate package | READY: `t4-terrain-g1` (default) and `t4-terrain-g1-noise2` (experimental), both under `D:\Game\Master Rallye\research-output` |
| 4. Collision diagnosis | DONE: 66,684 columns, three-way exact queries, 48 mismatch regions, 3 eligible, ranked |
| 5. Automated tests | 27 new and existing track tests pass (15 in `track-ground1`, 12 in `track-delta1`), root synthetic suite 630 of 630, `compileall` clean |
| 6. Runtime checks | prepared in `runtime-validation.md`, none performed |
| 7. TRACK-COLL1 readiness | GO, conditional (see `next.md`): first region rank 1, centre (2173.6, 16.5) |

## CONFIRMED_BY_BYTES (derived from the original files, see the linked documents)
- 69 PS2 textures in Turkey3: 63 same-name PC matches (difference at most 6.56 of 255), 2 renamed on the PC (PS2 plating2 is PC tanky, PS2 i2a_planks2 is PC wood_01), 4 PS2-only; the expected orientation (PC rows flipped) is the best in 63 of 63 genuine matches (`material-parity.md`, `texture-audit-turkey3.json`).
- DXT header word_0x08 is the CRC32 of the pixel payload in 65 of 65 PC files; earlier converted textures carried the haybale value (fixed).
- The PC ground has base texture plus `noise-tga` (128x128, identical in all 36 courses, mean x 2 = 0.9537) on a second UV array; the noise UV is not planar and is authored per mesh; the PS2 vertex float pair at +28/+32 equals neither PC UV set at 16,845 paired vertices.
- Of 4,020 position-non-exact PS2 ground triangles, 2,104 are equivalent to a PC triangle (398 exact UV, 1,706 UV differing by one common integer offset), 1,916 differ in geometry (679), base texture (473), UV mapping (17) or have no PC footprint (747).
- Collision (exact queries, 6-unit grid, `collision-regions.json`): of 66,684 columns the patched tree agrees with the PS2 BSP in 39,031 (retail 38,466), has 114 missing-support (retail 325) and 363 invisible-block columns (retail 717); 24,244 are PS2 exterior and 2,932 PS2 void and excluded.

## SYNTHETIC (tests and built data)
- `test_ground1.py` (11 tests: CRC header, orientation, same-name, different artwork, renamed file, missing files, unreadable PS2 file, retail header CRC, noise factor, ground triangle refinement), `test_collision_diag.py` (4 tests: classes, components, eligibility, exterior-first ranking), plus the 10 earlier tag100 tree and patch tests and the PS2 BSP parser test.
- `package_checks.py`: 21 models parse; texture slots resolve; DXT CRC headers correct; the loose `turkey3.dx` differs from retail only in 2,808 local-index bytes (1,402 triangles made degenerate) and the tag100 suffix; tag100 invariants hold; all seven object hulls are solid at their centroids; 0 of 1,916 added ground triangles coplanar with a remaining PC triangle (no duplicate z-fighting); the only duplicate Egg name (`AttractMode`) is in the retail XML.
- Determinism: two collision runs over the same columns gave byte-identical output.
- The renderer proxy and native tests were not touched in this phase (no CTest rerun).

## RUNTIME_CONFIRMED
None in this phase. Earlier phases (owner-confirmed): teleport, loose files, plain models with PS2 lighting, house and caravan collision, texture V flip, no terrain holes after the culling fix. The PC-texture fallback, the equivalence rule, the tint and everything in `runtime-validation.md` are not yet seen in the game.

## HYPOTHESIS
- The PS2 vertex pair at +28/+32 is the PS2 noise UV; the engine would apply the noise stage to a model Egg whose slot 2 is `noise-tga` and which has a second UV set (candidate C only).
- PS2 void columns are intended PS2 behaviour.
- Rank 1 region: the PC surface sits 0.3 to 1.1 above the PS2 one because of PC terrain, cause not established.

## UNKNOWN
- Whether the engine uses the DXT word_0x08; how the car reacts to a 1-unit invisible bump; whether PS2 leaf plane codes mean anything in the PC tree; how the noise detail looks on added ground (grain absent in B).

## What changed in code (all under `ps2-research/`)
`track-delta1`: `ps2_terrain.py` (`make_dxt`, `texture_difference`, `choose_texture`, `refine`, `noise_mean_factor`, `visual_models` options), `ps2_course_objects.py` (`--ground-detail`, refined replacement set), `ps2_obj_to_dx.py` (CRC header, `source_triangles_ext`), `ground_clusters.py` (PC triangle texture/UV/vertex ids, PS2 aux pair, ground family = shader or noise slot), `ground_material.py` (experimental 2-UV template). New folder `track-ground1`: the audits, diagnostics, tests and the six deliverables. Existing verified behaviour (objects, tag100 editing, slabs) is unchanged; the earlier `t4-terrain` package is superseded by `t4-terrain-g1` (it still carries the wrong DXT headers and replaces all 4,020 triangles).

## Deliverables
`final-report.md` (this file), `material-parity.md`, `collision-regions.json`, `collision-diagnostics.md`, `runtime-validation.md`, `next.md`; code and data `texture_audit.py`, `texture-audit-turkey3.json`, `ps2_vertex_fields.py`, `ps2-vertex-fields-turkey3.json`, `collision_diag.py`, `package_checks.py`, `package-checks-default.json`, `package-checks-noise2.json`, `test_ground1.py`, `test_collision_diag.py`.

## Recommendation for TRACK-COLL1
First region: rank 1, centre (2173.6, 16.5), box x 2148.5 to 2196.5, z 1.73 to 25.73 plus a 6-unit margin. It is exterior-free, single-layer, isolated (252 units), reachable (58 from the road), away from converted objects, and untouched by the slab pass, with exact PS2 contact heights per column; its weakness (0.3 to 1.1 units) is answered by a read-only chassis-height measurement at the probe columns. Reasoning and scope in `next.md`.
