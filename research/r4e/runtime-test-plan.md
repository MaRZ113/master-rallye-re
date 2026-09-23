# R4E human runtime matrix

Candidates are ignored under `.research-output/r4e/runtime-tests`. Test one at a time, restoring the original resource/archive after each run. Keep game screenshots and original bytes outside Git.

| Candidate | Controlled change | Expected observation | Current state |
|---|---|---|---|
| E1 | Astero sticker draw 12, UV0 U +0.05 | Sticker mapping moves, shape/collision unchanged | pending human runtime |
| E2 | Astero chrome draw 11, first eight source normals rotated 15 degrees | Local reflection orientation changes | pending human runtime |
| E3 | Astero body draw 7, first twelve raw colors darkened | Stage-0 diffuse modulation darkens patch | pending human runtime |
| E4 | Astero windscreen draw 23, flag byte 0 from 1 to 0 | Glass becomes opaque/non-alpha | pending human runtime |
| E5 | Full Python SMA with E1 car.dx override | Archive accepted and E1 visible | pending human runtime |

Each candidate has validation.json with source/output hashes, semantic fields, byte ranges, collision/topology hashes and dependencies. E5 additionally has archive SHA-256 and member verification. No game pass is claimed until owner observations arrive.
