# HUD-PORT6: progress-bar order, SPLIT TIME flash, map splits and opponents

User reports, 2026-10-18:
* on the PC the finish flag on the progress bar is greyer than on the PS2;
* on the PS2 the timer "blinks" after a checkpoint (GS dumps 20261018 161115 / 161201);
* the map needs the split crossbars and the opponents' X marks (in each car's colour).

## 1. Ticks and finish flag over the bar (`PS2HudTemplate=1`)

The flag and ticks were not grey. They were drawn under the bar:
* The PC draws the split marker, the ticks and the finish flag (hud-template images 4, 5, 6) **before** the
  progress bar. In F10 the finish is draw 347, the ticks 349-354 and the bar 359-442.
* With the PS2 bar art, the bar's dark translucent fill covers them. The PS2 draws the bar first (GS dump
  195341: bar 1817-1829, then ticks and finish 1831-1837).
* Fix: these three PC draws are not forwarded. Their placement (WORLD·VIEW·PROJ) is kept, and they are drawn
  at Present with the PS2 textures, white as in the dump, over the bar.
* Small difference: they now also cover the progress car marker. On the PS2 the marker is drawn after them.

## 2. SPLIT TIME flash (`PS2HudSplitFlash=1`, new)

EE gaHudAiSplitTime tick 0x14c000, per 50 Hz frame:
* While active and angle < 450: c = clamp(|sinf(angle)|, 0, 1), using fdlibm sinf 0x3f3140 in radians, then
  angle += 6. The colour becomes (c,c,c,1).
* Otherwise active = 0, angle = 90 and the colour returns to white.
* A change of `Race/Car<local>/SplitPoint` restarts it (active = 1, angle = 90). The last value starts at -1.

The dumps show the value at (10,10,10) and (119,119,119) while the labels stay white. The PC gaHudAiSplitTime
(0x4a9050) only rewrites the text.

Port: the draws of egg `GameSplitTimeNumber` (exact egg name, white vertices) are drawn with stage1
`MODULATE(CURRENT, TFACTOR)`, with TFACTOR = c, and the native states are restored. This happens only when
stage1 is disabled.

## 3. Map (`PS2HudMap=1`)

Order follows dump 161201: background, route, split crossbars, finish crossbar, chevron shadow, then each
opponent's shadow X and X, then the chevron and the frame.

* **Splits.** PS2 0x181dd0: BestMarker is the nearest RaceLine marker to the split egg, and
  Percentage = BestMarker / count. The PC has only `Race/SplitTime%d/Percentage` (the same code and log text),
  so BestMarker = round(Percentage × count). The crossbar is green (125,200,25, GS alpha 125), half-length 10
  (2.5·4), width 3 (dump 161115: 19.9 × 3.0).
* **Finish crossbar.** Width corrected from 4 to 3 (dump 195654: 23.2 × 3.0).
* **Opponents** (EE 147038, ui2/minimap.md). Every car except the player, at its vehicle position (the same
  fields as the player).
  * Two clipped diagonals ±4, width 4. The shadow is shifted +2,+2.
  * Colour from `Race/Car%d/Colour` (Broker tag 5, RGBA float; PC 0x4de9e0), white by default.
  * Foreground = colour·250, shadow = colour·40, GS alpha 125. Dump: (60,83,153) and (9,13,24).

## 4. Verification

From `dist/hud-port6/build-report.json` (schema 3, branch `master`, base HEAD 4b160e6):
* baseline build, ctest and proxy verification: PASS;
* PS2-enabled build: PASS; `ps2_port_tests`: PASS;
* the baseline and PS2-enabled `d3d8.dll` differ (`dll_distinct`).

Not verified here: the in-game visual check against the PS2 dumps (161115, 161201, 195341/195654).
Build outputs (`dist/`) are not tracked; the A/B notes are in `dist/hud-port6/runtime-ab.md`.
