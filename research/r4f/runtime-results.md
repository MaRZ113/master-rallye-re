# R4F F1 human runtime result

The project owner tested the Astero `car.dx` F1 candidate in the original Master Rallye runtime. This human evidence is recorded separately from the pre-runtime candidate validation file.

| Check | Result |
|---|---|
| Game and Astero load | PASS |
| New raised hood/body triangle visible | PASS |
| Original primary collision | Works normally |
| Procedural external damage | Works |
| Procedural internal/mesh damage | Works |
| Breakable glass | Works |
| Wheels and general vehicle function | Normal |

F1 adds three serialized render vertices and one triangle to existing body draw 7: 2543 to 2546 vertices, 2021 to 2022 triangles. The new triangle is subtle because it inherits the existing material and texture, but its geometry is visibly present near the hood/body region. This confirms **TOPOLOGY-CHANGING VEHICLE RENDER WRITING — CONFIRMED_BY_RUNTIME** for the tested `car.dx` case, with unchanged collision and normal damage/glass/wheel behavior.

Original SHA-256: `b97949651ae1c0089a614beaa24f6b07bbea84735c70faf1570760a9aaa16d90`.
Candidate SHA-256: `b03e8402baef682bb5665ccbce3a9cc8342e87409b3a5bd2170e9674d6ed7835`.
The ignored candidate's automated validation reported zero unexplained external diffs. The result does not establish out-of-donor-bounds geometry or topology writing for `complete.dx` and `wheel.dx`.
