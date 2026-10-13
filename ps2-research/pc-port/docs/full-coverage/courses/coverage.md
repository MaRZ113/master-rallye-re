# Full original course vegetation coverage

36 source-owned course pairs and 72 private category assets are verified. Identity transforms in game coordinates come from independently parsed RaceLine and landscape XML; direct .001 triangle anchors gate each source triangle. No arbitrary registration transform, nearby terrain guesses or invented density.

All 36 landscapes have recognized grass and shrubs sources. Original GRASS1/BUSH1 textures remain global 32x32 images; no course texture variants are proved. The singular `$detail(shrub)` token is not normalized. Full-triangle float32 nearest-even placement remains an approximation of original incremental activation/history, not PS2 pixel parity.

| Course | Native certificate | Grass exact/eligible faces | Grass points | Shrubs exact/eligible faces | Shrubs points |
|---|---|---:|---:|---:|---:|
| FRANCE1 | RaceTest/France1 | 5192/5193 | 197680 | 1463/1463 | 169932 |
| FRANCE2 | RaceTest/France2 | 1735/1736 | 100931 | 1315/1315 | 83480 |
| FRANCEM | RaceTest/FranceM | 2959/2961 | 112186 | 2217/2236 | 150261 |
| FRANCES1 | RaceTest/FranceS1 | 2900/2901 | 142461 | 1717/1718 | 95088 |
| FRANCES2 | RaceTest/FranceS2 | 3256/3257 | 190435 | 2257/2259 | 175225 |
| FRANCEW | RaceTest/FranceW | 3445/3454 | 257177 | 2448/2451 | 209758 |
| FRANCEW_FLIP | RaceTest/FranceWFlip | 3470/3477 | 288863 | 2365/2367 | 168699 |
| ITALY1 | RaceTest/Italy1 | 3430/3430 | 99749 | 961/961 | 40227 |
| ITALY2 | RaceTest/Italy2 | 3664/3666 | 187555 | 2023/2048 | 161539 |
| ITALY3 | RaceTest/Italy3 | 4499/4526 | 186468 | 1913/1922 | 124947 |
| ITALY_M1 | RaceTest/ItalyM1 | 3785/3786 | 131242 | 1140/1143 | 88866 |
| ITALY_M1_FLIP | RaceTest/ItalyM1Flip | 3775/3776 | 130935 | 1140/1143 | 88866 |
| ITALY_M2 | RaceTest/ItalyM2 | 5211/5222 | 226946 | 2614/2631 | 192383 |
| ITALY_S1 | RaceTest/ItalyS1 | 3239/3239 | 125524 | 1137/1158 | 75253 |
| ITALY_S2 | RaceTest/ItalyS2 | 4052/4080 | 136922 | 1634/1639 | 115838 |
| ITALY_S3 | RaceTest/ItalyS3 | 4171/4176 | 204564 | 2266/2276 | 173599 |
| ITALY_S3_FLIP | RaceTest/ItalyS3Flip | 4173/4180 | 204388 | 2266/2276 | 173599 |
| ITALY_S4 | RaceTest/ItalyS4 | 5349/5361 | 202413 | 2881/2927 | 191259 |
| ITALY_W1 | RaceTest/ItalyW1 | 3856/3859 | 134281 | 1518/1550 | 94366 |
| ITALY_W2 | RaceTest/ItalyW2 | 4639/4643 | 190312 | 2738/2776 | 174404 |
| SPAIN1 | RaceTest/Spain1 | 3226/3248 | 59726 | 2176/2188 | 154887 |
| SPAIN2 | RaceTest/Spain2 | 2302/2362 | 58174 | 477/484 | 26499 |
| SPAIN_M | RaceTest/SpainM | 3266/3299 | 63180 | 1635/1638 | 111262 |
| SPAIN_S1 | RaceTest/SpainS1 | 3192/3201 | 70819 | 1518/1520 | 85147 |
| SPAIN_S1_FLIP | RaceTest/SpainS1Flip | 3192/3201 | 70819 | 1518/1520 | 85147 |
| SPAIN_S2 | RaceTest/SpainS2 | 3230/3266 | 58296 | 1386/1387 | 95600 |
| SPAIN_W | RaceTest/SpainW | 3250/3254 | 70030 | 1392/1393 | 88613 |
| SPAIN_W_FLIP | RaceTest/SpainWFlip | 3250/3254 | 70030 | 1392/1393 | 88613 |
| TURKEY1 | RaceTest/Turkey1 | 5204/5204 | 151186 | 1277/1278 | 44464 |
| TURKEY2 | RaceTest/Turkey2 | 2814/2894 | 79135 | 1961/2193 | 72131 |
| TURKEY3 | RaceTest/Turkey3 | 2797/2912 | 64900 | 3702/3835 | 146498 |
| TURKEY_M | RaceTest/TurkeyM | 3091/3160 | 83697 | 1559/1643 | 53682 |
| TURKEY_S1 | RaceTest/TurkeyS1 | 3068/3348 | 86962 | 1687/1782 | 95801 |
| TURKEY_S2 | RaceTest/TurkeyS2 | 3905/4081 | 102363 | 1042/1111 | 48954 |
| TURKEY_S2_FLIP | RaceTest/TurkeyS2Flip | 4472/4650 | 115107 | 1070/1137 | 49546 |
| TURKEY_W | RaceTest/TurkeyW | 3598/3643 | 182955 | 2309/2427 | 81185 |

Total: 8,914,029 derived points and 113,814,796 private artifact bytes. The whole-game inventory describes source potential, not a simultaneously visible population. 2,317 slope-eligible source faces have no exact PC triangle counterpart and are excluded; unknown correspondence does not prove missing terrain.

FranceW grass (257,177) and FranceWFlip grass (288,863) exceed the old 250,000-point artifact cap. A bounded 300,000-point cap retains all source-derived samples. Every other category fits 250,000. Keep the 16,384 runtime visible-point guard unchanged. Conservative 9x9 eight-unit bins bound all 60-unit windows to 2,997 points/category or less; this is a byte-derived upper bound, not a runtime measurement.

Avoid preloading/retaining all 114 MB of assets merely to enter the menu. Keep registry metadata resident, load the selected course/category once at an admitted race boundary, retain a bounded cache across restart, and never rescan source files per frame. Each course has a unique verified filename/PSM/GXI/PC DX/artifact hash tuple. Existing Turkey3/France1/ItalyS1 artifacts reproduce byte-exactly.

Focused synthetic/registry tests: 8/8 PASS. Private artifact readback: 72/72 PASS. Resource hashes, bounded bins, point coordinates and metadata are checked by the existing `validate_artifact`. Generation above 300,000 points fails explicitly without thinning. Original assets and Course SDK remain read-only. Menu/race FPS, course-switch, MSAA and HUD observations remain pending user runtime.

Executed:

```powershell
python ps2-research/pc-port/docs/full-coverage/courses/prepare_all.py --ps2 'D:/Game/Master Rallye PS2' --pc 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --publish --budget 1000000
python ps2-research/pc-port/docs/full-coverage/courses/validate_registry.py
python ps2-research/pc-port/docs/full-coverage/courses/test_prepare_all.py
```

Initial generation used an explicit 1M diagnostic cap; the observed maximum of 288,863 supports tightening the final registry/default budget to 300,000. Five France special stages were rerun after correcting exact resource-owned pairing. Regeneration must reproduce existing artifact bytes; overwriting different or linked artifacts is prohibited.
