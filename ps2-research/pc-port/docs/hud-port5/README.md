# HUD-PORT5: PS2 opponent list (`PS2HudTimeDiffs=1`)

This replaces the PC `gaHudTimeDiffsAi` name list under the rank with the PS2 `gaHudTimeDiffs2Ai` time-gap
list. Asset: `PS2Hud/PS2HudTimeDiffs.bin`, built by `tools/prepare_hud_timediffs_asset.py`. Evidence is in
`ps2-research/hud-dump1/findings.md` (section TimeDiffs).

## PS2 contract

* **When the list is shown.** With fewer than 2 cars nothing is drawn, so practice shows no list (dump 110543).
* **Time stamps** (every 50 Hz frame). Each car stamps the local car's `Race/Car<local>/Time` into its
  per-RaceLine-marker table at its `LastMarker`, unless that marker already has a stamp.
* **Gaps** (every 40 frames, 0.8 s). EE 0x150d18 computes each car's gap to the local car:
  * car ahead: T minus the car's stamp at or near (±8) the local car's marker;
  * car behind: the local car's stamp at or near the car's marker, minus the car's own stamp.

  The car-0 rule of 0x151120 applies. The gaps are placed in `Rank` order, made monotonic
  (a[r+1] = a[r] - 0.25·(a[r+1]-a[r]) when it rises), and get the wrong signs above or below the local car
  cleared.
* **Rows** (EE 0x150b28). Row r is at the egg position (22,365) with y - 15r. Each row has:
  * a SmallCarSheet icon at (0,-4): the image is car table[`CarType`] (EE 0x116f88, 29 cars);
  * text at +35 in font 102 = ARIAL_16: `%.2f` in green (0.5,1,0.5) when ahead, red (1,0.5,0.5) when behind,
    `--.--` in white for the local car or 0.

## PC integration

* **Feed** (read only). Broker keys `Race/NumCars`, `Car%d` (tag 10 object = car exists) and `Race/Car%d/`
  `PlayerType` and `Progress` (float, tag 1), `Rank`, `LastMarker` and `CarType` (int, tag 2). The local car's
  `Time` (float). The RaceLine marker count. Tags: PC 0x4d6650 float = 1, PS2 0x1e3610 = 1, 0x1e3650 = 2.
* **PC rows.** Egg `TimeDiffs` (unique in the egg registry) → egg+4 = `gaHudTimeDiffsAi` (vtable
  base+0x291058) → rows at AI +0xc/+0x10/+0x14. The baseline reads egg+4 the same way for RaceLimits.
  * Their draws are not forwarded while the feed is live. Practice gives an empty list, as on the PS2.
  * The first row drawn each frame gives the placement: PC row k is at (20, 380-15k), and PreserveMargins is
    included.
  * The local row's PC SmallCarSheet icon (exact level-0 SHA; PC and PS2 image indices match) checks the car
    table. If it disagrees, the PS2 icons are switched off and the log says so.
* **Not yet known.** What the PS2 tick does after the local car finishes (the PC freezes its rows). The PS2
  list keeps updating from the same keys.

## Log

`{"type":"ps2_hud_time_diffs","reason":..,"layer":..,"cars":N,"local":i,"markers":M,"quads":Q,"hidden":H,"pc_local_icon":k}`
