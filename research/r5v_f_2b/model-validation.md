# R5V-F.2c model validation

All three retail-cooked models pass the current modern rev135 parser. Cook B regenerated all three in one session, and its output bytes equal the frozen Cook A snapshot for each role.

Complete: 122372 bytes, SHA-256 ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b; 2305 vertices, 2096 triangles, 18 draws; tag102 and marker-1339 accepted.

Car: 112722 bytes, SHA-256 5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44; 2115 vertices, 1632 triangles, 17 draws; authentic tag101 plus marker-1339 accepted. Structural collision checks pass; the legacy secondary descriptor comparison remains open as documented in collision-validation.md.

Wheel: 12997 bytes, SHA-256 8707d887a75c452eb739775e21f94109521d9fc6be07726cee28a8e911c590ff; 220 vertices, 252 triangles, 5 draws; tag102 and marker-1339 accepted.

All three strict validator outputs are VALID with no parser errors. All non-null texture references resolve to the locked 25-file DXT set. Legacy render comparison and exact runtime cook evidence are in car-wheel-cook.md and cook-a/validation.json.

The cache-only package uses the byte-verified Cook B files. It contains no GXM, GXI, or TXT under `DataGx/Vehicles/Mercedes`; the package copy has not yet received the human preview/race load test. No original game assets were changed.
