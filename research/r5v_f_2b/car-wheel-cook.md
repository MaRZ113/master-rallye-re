# R5V-F.2c Cook A car/wheel validation

## Runtime evidence

The isolated runtime capture at research-output/r5v_f_2b/cook-b/car-cook.log contains successful fresh cooks for car and wheel. Despite its directory name, this log is not a full Cook B: complete.dx was already present and loaded from cache in that session. The existing complete cook remains the first Cook A output. Together, those captures form the frozen Cook A evidence set; they are not one three-role launch.

| Role | Cache miss | Read GXM | Build | Save DX | Reload DX |
|---|---:|---:|---:|---:|---:|
| complete | line 1499, event 00002924 | 1500, 00002925 | 1501, 00002927 | 1521, 00002958 | 1522, 00002960 |
| car | line 1591, event 00003075 | 1592, 00003076 | 1593, 00003078 | 1613, 00003109 | 1614, 00003111 |
| wheel | line 1620, event 00003123 | 1621, 00003124 | 1622, 00003126 | 1642, 00003157 | 1643, 00003159 |

Car and wheel messages share DebugView process id 39308. Both GXM inputs are the staged files under runtime-cook/DataGx/Vehicles/Mercedes, match the pinned Copy of Mercedes source hashes, and produce DX files at those same runtime cache paths. The complete cook was recorded in the earlier process id 22504 capture. The car/wheel log was copied to cook-a/car-wheel-cook.log while preserving the original cook-b/car-cook.log evidence.

## Cooked outputs

| Role | Bytes | SHA-256 | Revision | Parser | Tags | Trailer |
|---|---:|---|---:|---|---|---|
| complete | 122372 | ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b | 135 | VALID | 102 | footer56 plus marker1339 |
| car | 112722 | 5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44 | 135 | VALID | 101 | marker1339 with tag101 trailer |
| wheel | 12997 | 8707d887a75c452eb739775e21f94109521d9fc6be07726cee28a8e911c590ff | 135 | VALID | 102 | footer56 plus marker1339 |

All three pass parse_dx and strict validate_existing_rev135. Position, normal and UV arrays are finite; draw/index ranges and global index coverage validate. Footer or marker bounds are finite. Details are in cook-a/validation.json and cook-a/hashes.json.

## Legacy rev127 comparison

The selected control is demo-8.4.1/DataGx/Vehicles/Copy of Mercedes, the exact family matching the pinned GXM/TXT/GXI/DXT source. It is not the separate demo DataGx/Vehicles/Mercedes folder.

Car: both revisions have 2115 vertices, 1632 triangles and 17 draw records. Local/global indices, reconstructed triangles, positions, normals, UVs and AABB are exact. Thirty color bytes change by one code; alpha is unchanged. Material and texture slots map exactly to the 17 car.txt materials.

Wheel: both revisions have 220 vertices, 252 triangles and 5 draw records. Indices, reconstructed triangles, normals, UVs, colors and AABB are exact. Three position components differ by at most 3.55e-15. All five wheel.txt materials map uniquely.

Complete regression: both revisions have 2305 vertices, 2096 triangles and 18 draw records. Indices, normals, UVs and AABB are exact; position noise is at most 1.42e-14; 30 RGB bytes change by 178 to 179 with alpha unchanged. The prior complete result remains valid.

These differences are bounded format/cooker precision effects, not topology or bounds drift. Color quantization cause was not independently isolated.

## Runtime scope

The captured Practice/Quick Race resource-load sequence proves native GXM-to-DX cooking and cache reload. It is not gameplay acceptance or final Mercedes ID26 acceptance. Do not infer handling, damage, or final identity from this cook-only capture.
