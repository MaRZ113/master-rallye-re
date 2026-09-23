# R4E.1 focused closeout status

Published R4E remains untouched. Human R4E results: E1 UV **PASS**, E2 normal **INCONCLUSIVE**, E3 vertex color **PASS**, E4 alpha flag **PASS**, E5 full-tree Python SMA **PASS**. See ../r4e/runtime-results.md/json. E2 edited only eight of 192 chrome normals by about 15 degrees; absence of a clear difference is not a writer failure.

Both writer audits pass. N1 rotates all 192 original Astero draw-11 normals +90 degrees around source +Y and changes 1504 authorized bytes. M1 changes draw-7 environment mask 7 to 3 in one byte. Both have zero unexpected ranges, reparse, preserve collision/topology and use protected source SHA-256 `b97949651ae1c0089a614beaa24f6b07bbea84735c70faf1570760a9aaa16d90`. Blender 5.2.2 verified source IDs and mask metadata without custom-normal APIs.

Regression evidence: 77 Python synthetic tests passed; protected original corpus 78/78 DX and 6,960/6,960 DXT zero edits passed; Blender 5.2.2 passed full 78-resource zero exports, 22-resource real regression, synthetic import/edit checks, packaged add-on installation, and focused N1/M1 export audit.

**Human runtime closeout: N1 PASS, M1 PASS — both CONFIRMED_BY_RUNTIME. SAME-TOPOLOGY VEHICLE SDK V1 BASELINE FROZEN.** See runtime-results.md/json. N1 visibly changed chrome/chromebar reflection/shading with geometry intact; M1 removed body-draw environment contribution while slot-0 livery and other reflective materials remained. The constant-normal fallback is unnecessary. Topology-changing DX writing remains an R4F task.
