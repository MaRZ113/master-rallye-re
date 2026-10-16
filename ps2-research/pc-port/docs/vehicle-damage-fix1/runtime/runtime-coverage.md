# Session 21808 bounded runtime coverage

Read-only audit. Log success proves native submissions and restoration, not visual correctness. Draw/frame numbers are evidence locators only.

Source `session-20261015-103238-21808.jsonl`, SHA-256 `89fb2756880dc498f14c60f38b03a81d2ccbd5ffa7ad3266249702dbd6caf482`, 16777207 bytes; proxy `ac0e0ddd779264ce7cbc990d7534c10e9bba13a75630fa751478374c44afb3fc`.

2900 valid rows; 135 malformed free-camera rows excluded without repair. The session is 9 bytes below 16 MiB and nevertheless ends with shutdown breadcrumbs: bounded/category logging means absence of later events cannot establish that a feature stopped rendering.

## COMPLETE matrix

| PC family | Result | Success frame(s) | Source records / PS2 faces |
|---|---|---|---|
| Astero | NATIVE_DRAW_RESTORE_PASS | 10293, 12315, 12434 | 24 / 5370 |
| Bruno | NATIVE_DRAW_RESTORE_PASS | 11971, 12941 | 16 / 4748 |
| ChevyBlazer | NATIVE_DRAW_RESTORE_PASS | 1343 | 24 / 2562 |
| forklift | NO_SUCCESS_EVENT |  | Not observed |
| Frontera | NATIVE_DRAW_RESTORE_PASS | 887 | 24 / 5061 |
| IceCream | NO_SUCCESS_EVENT |  | Not observed |
| Jump | NATIVE_DRAW_RESTORE_PASS | 8833 | 19 / 5079 |
| Kamaz | NATIVE_DRAW_RESTORE_PASS | 13591, 13890 | 26 / 6496 |
| Kangoo | NATIVE_DRAW_RESTORE_PASS | 11802, 12217, 12388, 12588 | 21 / 4997 |
| LandCruiser | NATIVE_DRAW_RESTORE_PASS | 3358, 14489 | 24 / 5436 |
| megane | NATIVE_DRAW_RESTORE_PASS | 11874, 12151, 12637 | 26 / 3770 |
| Navara | NATIVE_DRAW_RESTORE_PASS | 7999 | 26 / 4633 |
| NewRav | NATIVE_DRAW_RESTORE_PASS | 9364, 9493 | 20 / 5038 |
| Pajero | NATIVE_DRAW_RESTORE_PASS | 2624, 6931, 14316, 14572 | 25 / 5058 |
| Patrol | NATIVE_DRAW_RESTORE_PASS | 9282, 9446 | 26 / 5212 |
| RMonster | NATIVE_DRAW_RESTORE_PASS | 9185 | 24 / 4791 |
| SeatBuggy | NATIVE_DRAW_RESTORE_PASS | 13488, 13651 | 25 / 3822 |
| Terrano | NATIVE_DRAW_RESTORE_PASS | 2288 | 20 / 5132 |
| WildCat | NATIVE_DRAW_RESTORE_PASS | 9875 | 21 / 4983 |
| Xtrail | NATIVE_DRAW_RESTORE_PASS | 118, 1275, 14688 | 24 / 4636 |

18/20 admitted families have successful draw/restore events. Forklift has no selection evidence. IceCream has no success; frame 13958 gate 8/seen 1 followed by frame 13959 gate 2/seen 0x7ffff7 (23-source set missing bit 3). This is a native binding/descriptor/FVF gate before source hash, not proof of missing assets or a hash mismatch. Gate has several subconditions and does not identify the exact one.

## Crew, lamps and Reset

At frames 15133 and 16189, verified race parts submit both 48-face source face subsets, 252-face bodies, 148-face helmets and 52-face visor/trim combination; all logged draw/restore HRESULTs are zero. This proves submissions, not two visually distinct correctly occluded occupants. Native suppression completeness and screenshot review remain user checks.

No lamp, brake or glow event type occurs in this session. Rear OFF/ON/glow visual correctness is unproved by these capped logs.

Reset at frame 16188 succeeds with MSAA=4 retained. Current race owner rewarms and successful chassis/parts/wheel replacement resumes at 16189. F10 frames 23999 and 32683 also report effective MSAA 4; native reset count 1. Successful restoration events do not measure menu FPS.

## Next bounded runtime recipe

1. Cold launch with the corrected DLL and all prior options unchanged; save the fresh session header/hash.
2. X-Trail race: F10 healthy before contact; moderate body contact then F10; further contact then F10. Retain one session, same camera bookmark and visible decals/lamps/wheels. Label each file; do not infer damage from draw ordinal.
3. With stationary X-Trail, capture rear brake OFF then held ON; inspect upper OFF base separately from brake core and additive fade. Capture crew through windshield, both occupants, and wheel steering.
4. Reset once at MSAA 4x and repeat damaged body F10 plus rear OFF/ON. Restart race and capture healthy again.
5. Frontend: explicitly select IceCream and each newly corrected family; allow two frames then F10, rotate and F10, switch away/back and repeat. Forklift requires explicit selection evidence. Record exact successful source family or fallback gate.
6. One visual check of all admitted families, menu responsiveness, no duplicate geometry or missing pieces. Native success entries are not substitutes for screenshots.
