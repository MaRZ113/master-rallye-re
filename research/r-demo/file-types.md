# R-DEMO file type inventory

Read-only corpus scan. Header signatures are the first eight bytes of each file; they are not format claims.

## demo-8.4.1

| Extension | Count | Retail count | Bytes | Mean/min/max bytes | Main path prefixes | Common sibling extensions | Header 8-byte modes |
|---|---:|---:|---:|---:|---|---|---|
| `.gxi` | 2046 | 0 | 88394976 | 43203/72/1755944 | DataGx/Fonts (839), DataGx/Vehicles (392), DataGx/Frontend (349) | .dxt (1746), .gxb (1084), .dxb (1063) | `3930010020002000 (471), 3930010080008000 (464), 3930010010001000 (295)` |
| `.dxt` | 1181 | 6960 | 43406468 | 36753/84/262164 | DataGx/Fonts (405), DataGx/Frontend (299), DataGx/Vehicles (291) | .gxi (1157), .dxb (682), .gxb (622) | `edfe000001000000 (1181)` |
| `.xml` | 184 | 124 | 10208912 | 55483/9/317905 | DataScene/FrontendScreens (56), DataScene/Test (45), DataScene/old (41) | .xml# (179), .hnt (45), .gxi (7) | `3c5363656e653e0a (88), 3c5363656e653e0d (75), 3c47616d653e0d0a (15)` |
| `.xml#` | 107 | 4 | 6246181 | 58375/9/317874 | DataScene/FrontendScreens (43), DataScene/old (28), DataScene/Test (15) | .xml (107), .hnt (41), .gxi (7) | `3c5363656e653e0a (91), 3c5363656e653e0d (6), 3c47616d653e0d0a (5)` |
| `.gxm` | 76 | 0 | 41949311 | 551964/657/11489135 | DataGx/Vehicles (40), DataGx/multiPlayer (11), DataGx/Test (10) | .gxi (69), .txt (57), .dx (50) | `0207010000000000 (34), 0207020000000000 (18), 0207050000000000 (8)` |
| `.dxb` | 64 | 113 | 152002 | 2375/166/14576 | DataGx/Frontend (46), DataGx/Fonts (13), DataGx/Hud (4) | .dxt (64), .gxi (64), .gxb (38) | `01f000007d000000 (64)` |
| `.txt` | 51 | 149 | 400915 | 7861/0/158889 | DataGx/Vehicles (40), DataGx/Misc (4), DataGx/Course (2) | .gxm (50), .gxi (48), .dx (39) | `6d6f4d6f64656c28 (49),  (1), 50757420616c6c20 (1)` |
| `.dx` | 49 | 160 | 29409375 | 600191/431/13092323 | DataGx/Vehicles (30), DataGx/Misc (7), DataGx/Markers (4) | .gxm (49), .gxi (42), .dxt (40) | `0dd000007f000000 (39), 0dd000007d000000 (5), 0dd000007b000000 (3)` |
| `.gxb` | 40 | 0 | 8321384 | 208034/2712/1967112 | DataGx/Frontend (19), DataGx/Fonts (17), DataGx/Hud (4) | .gxi (39), .dxt (39), .dxb (35) | `393001004001f000 (2), 3930010002012800 (2), 393001009801d900 (2)` |
| `.wav` | 38 | 83 | 2668208 | 70216/4704/346688 | DataAudio/vehicles (15), DataAudio/Frontend (8), DataAudio/Environment (5) | — | `5249464646210000 (2), 5249464688dc0000 (1), 52494646803a0000 (1)` |
| `.mp3` | 21 | 26 | 47253827 | 2250182/1273312/5454785 | DataAudio/Music (21) | — | `fffb707c0000e000 (3), fffb707c00014000 (2), fffb707c00000000 (1)` |
| `.map` | 17 | 0 | 10380 | 610/74/837 | DataGx/Fonts (16), DataGx/Frontend (1) | .gxb (17), .gxi (16), .dxt (16) | `2f2f202d2d2d2d2d (15), 4109300d0a420931 (1), 3332093130092f2f (1)` |
| `.fl` | 8 | 0 | 10027316 | 1253414/749192/1755956 | DataScene/ICont (7), DataScene/France1.fl (1) | .sf (8), .gxi (1), .xml (1) | `0000404000c04c44 (1), 0000404000c04b44 (1), 0000404000c00644 (1)` |
| `.hnt` | 5 | 54 | 57794 | 11558/2194/27926 | DataScene/FrontendScreens (2), DataScene/RaceTest (2), resources.hnt (1) | .xml# (4), .xml (4), .exe (1) | `496d61676542616e (3), 4d6f64656c095b76 (2)` |
| `.tga` | 3 | 0 | 4092672 | 1364224/580764/1755954 | DataGx/Frontend (1), DataScene/France1FL.tga (1), DataScene/France1SF.tga (1) | .gxi (3), .xml (2), .fl (2) | `0000020000000000 (3)` |
| `.exe` | 2 | 2 | 2166846 | 1083423/81920/2084926 | MRallye.exe (1), StartMR.exe (1) | .hnt (2), .ico (2), .txt (2) | `4d5a900003000000 (2)` |
| `.jpg` | 2 | 0 | 201054 | 100527/58216/142838 | DataGx/Test (2) | .gxi (2), .dx (2), .gxm (2) | `ffd8ffe000104a46 (2)` |
| `.sf` | 2 | 0 | 3511912 | 1755956/1755956/1755956 | DataScene/France1.sf (1), DataScene/ICont (1) | .fl (2), .gxi (1), .xml (1) | `0000404000c04c44 (2)` |
| `.ico` | 1 | 1 | 2238 | 2238/2238/2238 | MRallye.ico (1) | .hnt (1), .exe (1), .txt (1) | `0000010001002020 (1)` |
| `.psd` | 1 | 0 | 9249 | 9249/9249/9249 | DataGx/Test (1) | — | `3842505300010000 (1)` |

Total: 3898 files, 298491020 bytes, 20 unique extensions.

## demo-9.3.1

| Extension | Count | Retail count | Bytes | Mean/min/max bytes | Main path prefixes | Common sibling extensions | Header 8-byte modes |
|---|---:|---:|---:|---:|---|---|---|
| `.dxt` | 1380 | 6960 | 51418320 | 37259/276/262164 | DataGx/Fonts (618), DataGx/Frontend (373), DataGx/Vehicles (167) | .dxb (1054), .gxb (915), .map (640) | `edfe000001000000 (1380)` |
| `.gxi` | 677 | 0 | 20280248 | 29956/264/262152 | DataGx/Vehicles (409), DataGx/Course (224), DataGx/particles (23) | .txt (638), .dxt (481), .dx (451) | `3930010080008000 (230), 3930010020002000 (203), 3930010040004000 (164)` |
| `.wav` | 72 | 83 | 5281990 | 73360/4704/846808 | DataAudio/Environment (30), DataAudio/vehicles (29), DataAudio/Frontend (8) | .mp3 (1) | `52494646bc710100 (2), 5249464630f80000 (2), 5249464646210000 (2)` |
| `.dxb` | 65 | 113 | 158050 | 2431/158/14576 | DataGx/Frontend (50), DataGx/Fonts (9), DataGx/Hud (4) | .dxt (65), .gxp (49), .gxb (40) | `01f000007d000000 (65)` |
| `.xml` | 62 | 124 | 3359812 | 54190/222/574802 | DataScene/FrontendScreens (35), DataScene/Hud (3), DataScene/RaceTest (2) | .xml# (19), .cfg (18) | `3c5363656e653e0d (42), 3c47616d653e0d0a (14), 3c47616d653e0a20 (4)` |
| `.txt` | 45 | 149 | 444082 | 9868/0/175192 | DataGx/Vehicles (35), DataGx/Misc (5), DataGx/Course (2) | .gxi (42), .gxm (35), .dx (28) | `6d6f4d6f64656c28 (43),  (1), 4d61737465722052 (1)` |
| `.gxb` | 42 | 0 | 9148832 | 217829/16392/1967112 | DataGx/Frontend (23), DataGx/Fonts (12), DataGx/Hud (6) | .dxb (39), .dxt (39), .gxp (21) | `3930010095014700 (2), 393001006d004c00 (1), 3930010084006f00 (1)` |
| `.gxp` | 38 | 0 | 31511184 | 829241/1032/1228808 | DataGx/Frontend (37), DataGx/Dummy.gxp (1) | .dxb (38), .dxt (38), .gxb (6) | `393001008002e001 (25), 393001008a022900 (4), 3930010080021e00 (2)` |
| `.gxm` | 33 | 0 | 5184303 | 157100/26967/309448 | DataGx/Vehicles (33) | .gxi (33), .txt (33), .dx (18) | `0207010000000000 (15), 0207020000000000 (10), 0207050000000000 (6)` |
| `.dx` | 30 | 160 | 26206323 | 873544/1187/13944061 | DataGx/Vehicles (17), DataGx/Misc (7), DataGx/Markers (3) | .dxt (26), .gxi (26), .txt (24) | `0dd0000083000000 (27), 0dd0000082000000 (2), 0dd0000080000000 (1)` |
| `.mp3` | 22 | 26 | 49435991 | 2247090/1273312/5454785 | DataAudio/Music (22) | .wav (22) | `fffb707c0000e000 (3), fffb707c00014000 (2), fffb707c00000000 (1)` |
| `.map` | 14 | 0 | 7543 | 538/74/837 | DataGx/Fonts (12), DataGx/Frontend (1), DataGx/Misc (1) | .gxb (14), .dxb (11), .dxt (11) | `2f2f202d2d2d2d2d (11), 4109300d0a420931 (2), 3332093130092f2f (1)` |
| `.tga` | 5 | 0 | 878367 | 175673/23723/307244 | DataGx/Fonts (4), DataGx/Misc (1) | .map (4), .gxb (4), .dxb (2) | `0000020000000000 (5)` |
| `.exe` | 2 | 2 | 2719806 | 1359903/81920/2637886 | MRallye.exe (1), StartMR.exe (1) | .hnt (2), .ico (2), .txt (2) | `4d5a900003000000 (2)` |
| `.sfl` | 2 | 36 | 684904 | 342452/213374/471530 | DataScene/ICont (2) | — | `000040404d030000 (1), 00004040b7010000 (1)` |
| `.xml#` | 2 | 4 | 127795 | 63897/8253/119542 | DataGame/options.xml# (1), DataScene/FrontendScreens (1) | .xml (2), .cfg (1) | `3c47616d653e0a20 (1), 3c5363656e653e0a (1)` |
| `.cfg` | 1 | 0 | 13 | 13/13/13 | DataGame/video.cfg (1) | .xml# (1), .xml (1) | `3634300d0a343830 (1)` |
| `.hnt` | 1 | 54 | 11492 | 11492/11492/11492 | resources.hnt (1) | .exe (1), .ico (1), .txt (1) | `496d61676542616e (1)` |
| `.ico` | 1 | 1 | 2238 | 2238/2238/2238 | MRallye.ico (1) | .hnt (1), .exe (1), .txt (1) | `0000010001002020 (1)` |

Total: 2494 files, 206861293 bytes, 19 unique extensions.

## retail

| Extension | Count | Retail count | Bytes | Mean/min/max bytes | Main path prefixes | Common sibling extensions | Header 8-byte modes |
|---|---:|---:|---:|---:|---|---|---|
| `.dxt` | 6960 | 6960 | 305808064 | 43937/276/262164 | Data.sma_unpacked/DataGx (6960) | .dx (5175), .txt (5167), .dxb (1753) | `edfe000001000000 (6960)` |
| `.dx` | 160 | 160 | 451488195 | 2821801/444/15275322 | Data.sma_unpacked/DataGx (160) | .dxt (154), .txt (144) | `0dd0000087000000 (160)` |
| `.txt` | 149 | 149 | 6651074 | 44638/0/299784 | Data.sma_unpacked/DataGx (148), Readme.txt (1) | .dx (148), .dxt (146), .exe (1) | `6d6f4d6f64656c28 (147),  (1), 3d3d3d3d3d3d3d3d (1)` |
| `.xml` | 124 | 124 | 23450534 | 189117/146/956977 | Data.sma_unpacked/DataScene (99), Data.sma_unpacked/DataGame (23), DataGame/options.xml (1) | .hnt (95), .xml# (6) | `3c5363656e653e0d (98), 3c47616d653e0d0a (25), 3c5363656e653e0a (1)` |
| `.dxb` | 113 | 113 | 265604 | 2350/158/15268 | Data.sma_unpacked/DataGx (113) | .dxt (113) | `01f000007d000000 (113)` |
| `.wav` | 83 | 83 | 8584542 | 103428/4704/1663320 | DataAudio/vehicles (37), DataAudio/Environment (30), DataAudio/Frontend (8) | .mp3 (1) | `52494646bc710100 (2), 5249464630f80000 (2), 52494646948e0100 (1)` |
| `.hnt` | 54 | 54 | 326491 | 6046/387/45323 | Data.sma_unpacked/DataScene (54) | .xml (54), .xml# (2) | `4d6f64656c095b63 (36), 4653546578747572 (18)` |
| `.sfl` | 36 | 36 | 18169268 | 504701/213374/958984 | Data.sma_unpacked/DataScene (36) | — | `0000404022060000 (2), 00004040e1050000 (2), 00004040b3040000 (2)` |
| `.mp3` | 26 | 26 | 57998624 | 2230716/1273312/4800679 | DataAudio/Music (26) | .wav (26) | `fffb7800000002c8 (3), fffb7800000002bb (3), fffb7800000002c6 (2)` |
| `.xml#` | 4 | 4 | 472806 | 118201/15042/176185 | Data.sma_unpacked/DataScene (2), DataGame/options.xml# (1), DataGame/PlayerState.xml# (1) | .xml (4), .hnt (2) | `3c5363656e653e0d (2), 3c47616d653e0d0a (2)` |
| `.avi` | 3 | 3 | 9426196 | 3142065/1337654/5060792 | DataVideo/mastersport.avi (1), DataVideo/microids.avi (1), DataVideo/monkeys.avi (1) | — | `52494646b0384d00 (1), 524946461e332e00 (1), 524946462e691400 (1)` |
| `.exe` | 2 | 2 | 3211326 | 1605663/90112/3121214 | MRallye.exe (1), StartMR.exe (1) | .sma (2), .ico (2), .txt (2) | `4d5a900003000000 (2)` |
| `.ico` | 1 | 1 | 2238 | 2238/2238/2238 | MRallye.ico (1) | .exe (1), .sma (1), .txt (1) | `0000010001002020 (1)` |
| `.sma` | 1 | 1 | 282396172 | 282396172/282396172/282396172 | Data.sma (1) | .exe (1), .ico (1), .txt (1) | `504b030414000000 (1)` |

Total: 7716 files, 1168251134 bytes, 14 unique extensions.
