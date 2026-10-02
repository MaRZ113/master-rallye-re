# G1 Retail RaceTest marker corpus

Evidence: `CONFIRMED_BY_CORPUS`; courses: 36; Retail EXE SHA256: `BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4`.
Source order is preserved. These reports describe structure and geometry, not semantics inferred from names.

## Marker-list inventory

| List | Coverage | Total markers | Per-course min / median / max | Pos | Dir | Extra fields |
|---|---:|---:|---:|---:|---:|---|
| `RaceLine` | 36/36 | 12604 | 136 / 355.0 / 470 | 12604 present, 0 missing | 12604 present, 0 missing | Marker Type |
| `LeftInnerLimit` | 36/36 | 7582 | 107 / 212.0 / 336 | 7582 present, 0 missing | 7582 present, 0 missing | Marker Type |
| `LeftOuterLimit` | 36/36 | 6519 | 85 / 181.5 / 323 | 6519 present, 0 missing | 6519 present, 0 missing | Marker Type |
| `RightInnerLimit` | 36/36 | 7533 | 130 / 210.0 / 335 | 7533 present, 0 missing | 7533 present, 0 missing | Marker Type |
| `RightOuterLimit` | 36/36 | 6442 | 97 / 188.0 / 323 | 6442 present, 0 missing | 6442 present, 0 missing | Marker Type |
| `Cameras` | 36/36 | 2975 | 56 / 79.5 / 127 | 2975 present, 0 missing | 2975 present, 0 missing | Marker Type |

## RaceLine geometry

| Course | Count | Length X/Z | Spacing X/Z min / median / max | First-last / length | duplicates | turns >45° | Dir central X/Z median cosine |
|---|---:|---:|---:|---:|---:|---:|---:|
| France1 | 448 | 8992.22 | 12.31 / 20.00 / 31.17 | 0.0285 | 0 | 9 | 0.004521106032588576 |
| France2 | 349 | 6902.43 | 0.01 / 19.97 / 38.02 | 0.0339 | 0 | 7 | 0.02993417136859647 |
| France_M | 412 | 8263.30 | 10.29 / 20.05 / 38.42 | 0.5561 | 0 | 11 | 0.7651465042558794 |
| France_S1 | 388 | 7800.41 | 13.41 / 20.03 / 30.61 | 0.4856 | 0 | 4 | 0.7213999147235937 |
| France_S2 | 429 | 8537.96 | 0.00 / 19.98 / 48.40 | 0.5372 | 1 | 13 | -0.7759492080324645 |
| France_W | 429 | 8551.80 | 10.89 / 19.94 / 33.16 | 0.5059 | 0 | 7 | -0.7518846266021851 |
| France_W_flip | 429 | 8554.12 | 10.89 / 19.94 / 33.16 | 0.5058 | 0 | 6 | 0.7518846266021851 |
| Italy1 | 213 | 7008.66 | 8.78 / 31.39 / 103.46 | 0.0670 | 0 | 19 | 0.07901386185456635 |
| Italy2 | 175 | 7072.53 | 12.68 / 41.44 / 51.02 | 0.0878 | 0 | 32 | 0.11914045594413147 |
| Italy3 | 136 | 5583.27 | 15.79 / 41.21 / 81.29 | 0.1776 | 0 | 8 | 0.21083853533762065 |
| Italy_M1 | 385 | 8355.98 | 10.81 / 21.53 / 48.03 | 0.4073 | 0 | 5 | 0.59343298690357 |
| Italy_M1_flip | 385 | 8355.98 | 10.81 / 21.53 / 48.03 | 0.4073 | 0 | 5 | -0.59343298690357 |
| Italy_M2 | 386 | 8531.10 | 11.93 / 21.61 / 37.05 | 0.5318 | 0 | 3 | -0.7182380598883564 |
| Italy_S1 | 292 | 6328.50 | 0.00 / 21.32 / 43.70 | 0.4462 | 1 | 11 | 0.5899973817402986 |
| Italy_S2 | 416 | 8754.35 | 12.71 / 20.51 / 38.92 | 0.3765 | 0 | 2 | 0.5980797072212365 |
| Italy_S3 | 346 | 7432.62 | 15.06 / 21.41 / 33.78 | 0.5246 | 0 | 5 | 0.6633448079792705 |
| Italy_S3_flip | 340 | 7310.79 | 15.06 / 21.41 / 33.78 | 0.5191 | 0 | 5 | -0.6599131598385397 |
| Italy_S4 | 365 | 7884.34 | 13.48 / 20.93 / 59.61 | 0.5783 | 0 | 9 | 0.7638509057162592 |
| Italy_W1 | 354 | 7301.23 | 13.65 / 20.11 / 34.65 | 0.4017 | 0 | 7 | -0.6363608992216574 |
| Italy_W2 | 356 | 7654.79 | 13.50 / 21.11 / 59.61 | 0.5893 | 0 | 13 | -0.7383896264219754 |
| Spain1 | 307 | 5970.38 | 8.23 / 19.10 / 34.37 | 0.0742 | 0 | 3 | 0.08492696093019805 |
| Spain2 | 324 | 7652.32 | 11.82 / 17.47 / 45.98 | 0.0733 | 0 | 14 | -0.19116233924529388 |
| Spain_M | 401 | 6846.34 | 12.54 / 17.17 / 20.83 | 0.3306 | 0 | 2 | -0.48549402157859217 |
| Spain_S1 | 337 | 7628.30 | 13.72 / 17.39 / 51.63 | 0.3638 | 0 | 18 | 0.532457779928268 |
| Spain_S1_flip | 337 | 7628.30 | 13.72 / 17.39 / 51.63 | 0.3638 | 0 | 18 | -0.532457779928268 |
| Spain_S2 | 258 | 7000.55 | 9.12 / 24.66 / 71.30 | 0.3676 | 0 | 21 | -0.5166484847257725 |
| Spain_W | 202 | 7793.11 | 22.61 / 38.96 / 51.63 | 0.3578 | 0 | 34 | 0.5038178007830034 |
| Spain_W_flip | 202 | 7793.11 | 22.61 / 38.96 / 51.63 | 0.3578 | 0 | 34 | -0.5038178007830034 |
| Turkey1 | 339 | 7508.14 | 12.04 / 21.96 / 32.38 | 0.0640 | 0 | 14 | -0.1958256988634928 |
| Turkey2 | 349 | 5932.52 | 7.08 / 19.81 / 30.15 | 0.0244 | 0 | 1 | -0.0974969600660046 |
| Turkey3 | 420 | 8092.55 | 0.62 / 19.90 / 39.03 | 0.0212 | 0 | 6 | 0.020504149479293323 |
| Turkey_m | 458 | 7946.66 | 7.28 / 19.77 / 28.09 | 0.3422 | 0 | 14 | 0.5548260611757292 |
| Turkey_s1 | 364 | 7026.69 | 8.74 / 19.93 / 29.85 | 0.5120 | 0 | 9 | -0.7103470454622913 |
| Turkey_s2 | 469 | 8222.64 | 7.28 / 19.86 / 47.00 | 0.4104 | 0 | 7 | 0.6335020497429436 |
| Turkey_s2_flip | 470 | 8238.70 | 0.00 / 19.86 / 47.00 | 0.4114 | 1 | 7 | -0.634617836587904 |
| Turkey_w | 334 | 6746.69 | 8.10 / 20.19 / 31.42 | 0.4429 | 0 | 7 | -0.680895166124381 |

## Marker Dir versus source-order tangents

Pooled over all present marker directions. Cosine is measured after the documented common course-to-Blender axis rotation; comparisons remain geometric and do not establish runtime use of `Marker Dir`.

| Tangent | Dimension | Samples | Min | Median | Mean | P05 | P95 | Max |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| forward | 3D | 12565 | -1.0000 | -0.0518 | -0.0241 | -0.9874 | 0.9851 | 1.0000 |
| forward | XZ | 12565 | -1.0000 | -0.0518 | -0.0241 | -0.9908 | 0.9890 | 1.0000 |
| backward | 3D | 12565 | -1.0000 | 0.0518 | 0.0241 | -0.9851 | 0.9874 | 1.0000 |
| backward | XZ | 12565 | -1.0000 | 0.0518 | 0.0241 | -0.9890 | 0.9908 | 1.0000 |
| central | 3D | 12532 | -1.0000 | -0.0503 | -0.0243 | -0.9879 | 0.9859 | 1.0000 |
| central | XZ | 12532 | -1.0000 | -0.0504 | -0.0243 | -0.9910 | 0.9896 | 1.0000 |

## Limit-to-route geometry

Positions are projected onto the nearest source-order RaceLine segment in X/Z. Distances in 3D are also retained because some lists use course-dependent Y values. Retail executable helper `0x004CE140` selects the nearest marker by 3D distance; for all four France1 limit lists Y is constant at 280.3, so the per-list nearest-marker ordering there reduces to X/Z distance. That statement does not generalize to all 36 courses. Side signs use each course's ordered route tangent and are not runtime labels.

| List | Markers | Y constant courses | X/Z distance median (min–max) | 3D distance median (min–max) | dominant side by course | mean dominant fraction |
|---|---:|---:|---:|---:|---|---:|
| LeftInnerLimit | 7582 | 22/36 | 29.09 (1.97–510.12) | 49.86 (5.59–510.88) | {'-1': 36} | 0.9922 |
| LeftOuterLimit | 6519 | 24/36 | 47.64 (0.55–562.92) | 69.83 (0.57–564.61) | {'-1': 36} | 0.9925 |
| RightInnerLimit | 7533 | 20/36 | 29.35 (1.97–510.12) | 51.24 (5.59–510.88) | {'1': 36} | 0.9911 |
| RightOuterLimit | 6442 | 24/36 | 48.04 (0.55–562.92) | 70.15 (8.93–564.61) | {'1': 36} | 0.9915 |

| Inner/outer comparison | Courses | matched progress pairs | Outer farther | per-course fraction median | distance delta X/Z median of per-course medians |
|---|---:|---:|---:|---:|---:|
| LeftInnerLimit_vs_LeftOuterLimit | 36 | 7455 | 7299/7455 (97.907%) | 98.521% | 20.72 |
| RightInnerLimit_vs_RightOuterLimit | 36 | 7415 | 7262/7415 (97.937%) | 98.526% | 20.12 |

## Bounded interpretation

- XML MarkerLists/RaceLine and GXM _raceline/raceline are distinct resources; only static spatial correlation is computed.
- Polyline order is literal source order; no nearest-neighbor reordering is applied.
- Side sign is the signed X/Z cross product relative to the nearest source-order RaceLine segment; it is not a semantic left/right claim.
- Inner/outer comparisons pair nearest route progress only within 0.0125 normalized progress; geometric correlation is not runtime proof.
