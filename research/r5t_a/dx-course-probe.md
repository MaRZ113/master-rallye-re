# R5T-A course DX parser probe

The current vehicle parser was run unchanged against every retail `DataGx/Course/*/*.dx` resource. The additive course reader reuses the shared DX arrays and draw-record parser, then follows the observed revision-135 root records, repeated draw batches, and course wrapper records.

- Retail course DX files: **36**
- Shared common-prefix success: **36**
- Current vehicle-parser status: **{'unsupported': 36}**
- Course-parser status: **{'parsed': 36}**
- Every course parse requires complete, disjoint local-index and vertex-range coverage; course tails are handed to the shared optional-section boundary reader.

| Resource | Revision | Vertices | Local triangles | Vehicle parser | First divergence | Course parser | Draws |
|---|---:|---:|---:|---|---|---|---:|
| `DataGx/Course/France1/france1.dx` | 135 | 65206 | 64577 | unsupported | 0x31B0EE | parsed | 995 |
| `DataGx/Course/France2/france2.dx` | 135 | 85024 | 60211 | unsupported | 0x3E98D2 | parsed | 1085 |
| `DataGx/Course/France_M/francem.dx` | 135 | 87479 | 75687 | unsupported | 0x41A97E | parsed | 1343 |
| `DataGx/Course/France_S1/frances1.dx` | 135 | 73815 | 67301 | unsupported | 0x37B872 | parsed | 1044 |
| `DataGx/Course/France_S2/frances2.dx` | 135 | 86268 | 72776 | unsupported | 0x409520 | parsed | 1263 |
| `DataGx/Course/France_W/francew.dx` | 135 | 81274 | 72145 | unsupported | 0x3D2BFE | parsed | 1094 |
| `DataGx/Course/France_W_flip/FranceW_flip.dx` | 135 | 81280 | 72145 | unsupported | 0x3D2D06 | parsed | 1101 |
| `DataGx/Course/Italy1/track01.dx` | 135 | 54612 | 41722 | unsupported | 0x287C6C | parsed | 837 |
| `DataGx/Course/Italy2/italy2.dx` | 135 | 68007 | 50501 | unsupported | 0x324872 | parsed | 981 |
| `DataGx/Course/Italy3/italy3.dx` | 135 | 61833 | 46271 | unsupported | 0x2DC026 | parsed | 656 |
| `DataGx/Course/Italy_M1/italy_m1.dx` | 135 | 70092 | 51171 | unsupported | 0x33BE82 | parsed | 1124 |
| `DataGx/Course/Italy_M1_flip/italy_m1_flip.dx` | 135 | 70092 | 51171 | unsupported | 0x33BE82 | parsed | 1124 |
| `DataGx/Course/Italy_M2/italy_m2.dx` | 135 | 77189 | 56223 | unsupported | 0x38F8B6 | parsed | 1126 |
| `DataGx/Course/Italy_S1/italy_s1.dx` | 135 | 61463 | 46367 | unsupported | 0x2D82CE | parsed | 867 |
| `DataGx/Course/Italy_S2/italy_s2.dx` | 135 | 69268 | 52955 | unsupported | 0x335AFF | parsed | 1212 |
| `DataGx/Course/Italy_S3/italy_s3.dx` | 135 | 70375 | 50628 | unsupported | 0x33E26C | parsed | 919 |
| `DataGx/Course/Italy_S3_flip/Italy_S3_flip.dx` | 135 | 70746 | 50836 | unsupported | 0x342710 | parsed | 922 |
| `DataGx/Course/Italy_S4/italy_s4.dx` | 135 | 79114 | 59903 | unsupported | 0x3A99D2 | parsed | 1011 |
| `DataGx/Course/Italy_W1/italy_w1.dx` | 135 | 64648 | 52899 | unsupported | 0x303F52 | parsed | 1017 |
| `DataGx/Course/Italy_W2/italy_w2.dx` | 135 | 80979 | 61157 | unsupported | 0x3BF7C2 | parsed | 975 |
| `DataGx/Course/Spain1/spain1.dx` | 135 | 38179 | 30170 | unsupported | 0x1C6540 | parsed | 367 |
| `DataGx/Course/Spain2/spain2.dx` | 135 | 77164 | 61445 | unsupported | 0x396ECE | parsed | 537 |
| `DataGx/Course/Spain_M/spain_m.dx` | 135 | 68207 | 53521 | unsupported | 0x32B19A | parsed | 579 |
| `DataGx/Course/Spain_S1/spain_s1.dx` | 135 | 66778 | 55462 | unsupported | 0x31E97C | parsed | 595 |
| `DataGx/Course/Spain_S1_flip/Spain_S1_flip.dx` | 135 | 66779 | 55462 | unsupported | 0x31E9A8 | parsed | 595 |
| `DataGx/Course/Spain_S2/spain_s2.dx` | 135 | 71560 | 53602 | unsupported | 0x34F3CC | parsed | 479 |
| `DataGx/Course/Spain_W/spain_w.dx` | 135 | 74963 | 58738 | unsupported | 0x37B510 | parsed | 545 |
| `DataGx/Course/Spain_W_flip/Spain_W_flip.dx` | 135 | 74963 | 58738 | unsupported | 0x37B510 | parsed | 545 |
| `DataGx/Course/Turkey1/turkey1.dx` | 135 | 58804 | 46199 | unsupported | 0x2BB5DA | parsed | 1295 |
| `DataGx/Course/Turkey2/turkey2.dx` | 135 | 65454 | 51417 | unsupported | 0x30A71E | parsed | 1159 |
| `DataGx/Course/Turkey3/turkey3.dx` | 135 | 54589 | 42237 | unsupported | 0x28848A | parsed | 939 |
| `DataGx/Course/Turkey_m/turkey_m.dx` | 135 | 85520 | 67115 | unsupported | 0x3F8FE2 | parsed | 1558 |
| `DataGx/Course/Turkey_s1/turkey_s1.dx` | 135 | 81765 | 65079 | unsupported | 0x3CDAC6 | parsed | 1510 |
| `DataGx/Course/Turkey_s2/turkey_s2.dx` | 135 | 74765 | 58528 | unsupported | 0x378E1C | parsed | 1223 |
| `DataGx/Course/Turkey_s2_flip/turkey_s2_flip.dx` | 135 | 74765 | 58528 | unsupported | 0x378E1C | parsed | 1224 |
| `DataGx/Course/Turkey_w/turkey_w.dx` | 135 | 60188 | 47716 | unsupported | 0x2CC748 | parsed | 1352 |

## Unsupported structures

None.

A `tag100`/`tag101`/`tag102` result is listed only when reached through the parsed course tail. Raw byte coincidences are not counted as tags.
