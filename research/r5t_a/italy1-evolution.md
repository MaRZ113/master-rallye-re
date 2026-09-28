# Italy1 course evolution (R5T-A)

All paths below are archive-relative. Hashes identify files in the supplied local corpus.
Layer presence and same-build file pairing are `CONFIRMED_BY_CORPUS`; source-to-compiled and cooker semantics remain `UNKNOWN` unless separately stated.

| Layer | 8.4.1 | 9.3.1 | 9.10.0 | Retail |
|---|---|---|---|---|
| GXM | 8728347 B; `c9ca6831569e` | absent | absent | absent |
| DX | 10053551 B; rev 127; `c96f11357edb` | 10461490 B; rev 131; `15018fd652c6` | 10264956 B; rev 135; `341f9a0c5aa1` | 10243860 B; rev 135; `971b44ab0f15` |
| TXT | 80331 B; `7e7406a6c277` | 84284 B; `ad23fcf568bf` | 89573 B; `39c9a12b92eb` | 89567 B; `f21fd87e09ee` |
| HNT | 4624 B; `0ffcf28f1b51` | absent | 0 B; `e3b0c44298fc` | 3112 B; `2505aec1193b` |
| XML | 162288 B; `e93f20c5d1cc` | 190533 B; `09c840bbe73c` | 187803 B; `c7e591a7b723` | 473135 B; `216c0b7c3320` |
| SFL | absent | 213374 B; `ce8f9809e14d` | 213374 B; `e497ca6c5872` | 213374 B; `e497ca6c5872` |
| FL | 768600 B; `8b535b0be427` | absent | absent | absent |
| SF | absent | absent | absent | absent |

## Resource inventory

Dxt assets are recorded per course folder in `course-corpus.json`; each entry carries its byte size and SHA-256.
Matching is exact after case-folding and removing filename separators. Unmatched or ambiguous paths stay explicit.

## Structural snapshot

| Build | DX rev | Vertices | Course DX parse / draws / triangles | TXT materials / mesh entries / span | SFL dimensions |
|---|---:|---:|---|---|---|
| Demo 8.4.1 | 127 | 55725 | unsupported revision 127 | 66/66 / 1082 / 47377 | absent |
| Demo 9.3.1 | 131 | 57170 | unsupported revision 131 | 90/90 / 1102 / 46786 | 439×486 |
| Demo 9.10.0 | 135 | 54529 | parsed / 794 / 41711 | 100/100 / 1098 / 46680 | 439×486 |
| Retail | 135 | 54612 | parsed / 837 / 41722 | 100/100 / 1098 / 46687 | 439×486 |
