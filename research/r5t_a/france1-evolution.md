# France1 course evolution (R5T-A)

All paths below are archive-relative. Hashes identify files in the supplied local corpus.
Layer presence and same-build file pairing are `CONFIRMED_BY_CORPUS`; source-to-compiled and cooker semantics remain `UNKNOWN` unless separately stated.

| Layer | 8.4.1 | 9.3.1 | 9.10.0 | Retail |
|---|---|---|---|---|
| GXM | 11489135 B; `56ebbf03fe68` | absent | absent | absent |
| DX | 13092323 B; rev 127; `9dd07341aa8f` | 13944061 B; rev 131; `3fe57cb8da2b` | 13475793 B; rev 135; `f33ce88ee0c1` | 13489510 B; rev 135; `a6bfcef97684` |
| TXT | 158889 B; `71ea372203bc` | 175192 B; `3ff161641f18` | 180249 B; `dc2f31cffb1a` | 172020 B; `fbb4153afa20` |
| HNT | absent | absent | absent | 3802 B; `d61ac7cd70a5` |
| XML | 245196 B; `89304e2f0e0e` | 336617 B; `42d3735f76c5` | 334577 B; `6048ed26c781` | 474787 B; `beaa2180912f` |
| SFL | absent | 471530 B; `cbf46dcf263d` | 471530 B; `36146806cb04` | 471530 B; `36146806cb04` |
| FL | ambiguous (2) | absent | absent | absent |
| SF | ambiguous (2) | absent | absent | absent |

## Resource inventory

Dxt assets are recorded per course folder in `course-corpus.json`; each entry carries its byte size and SHA-256.
Matching is exact after case-folding and removing filename separators. Unmatched or ambiguous paths stay explicit.

## Structural snapshot

| Build | DX rev | Vertices | Course DX parse / draws / triangles | TXT materials / mesh entries / span | SFL dimensions |
|---|---:|---:|---|---|---|
| Demo 8.4.1 | 127 | 64248 | unsupported revision 127 | 121/121 / 2283 / 61917 | absent |
| Demo 9.3.1 | 131 | 73404 | unsupported revision 131 | 150/150 / 2517 / 60650 | 845×558 |
| Demo 9.10.0 | 135 | 64961 | parsed / 977 / 64569 | 158/158 / 2520 / 64105 | 845×558 |
| Retail | 135 | 65206 | parsed / 995 / 64577 | 127/127 / 2527 / 64101 | 845×558 |
