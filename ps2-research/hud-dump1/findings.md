# HUD-DUMP1 — PS2 race HUD runtime contract from GS dumps (2026-10-17)

Sources: user PCSX2 GS dumps on Turkey with SeatBuggy. 194946 and 195001 have green, yellow and orange
damage; 195259, 195339 and 195341 add red damage and the notification; SW dump 153853 is the race
start with no damage. Reader: `../course-light1/gsdump.py`. This pass added `primseq`: the vertex
queue now restarts on every PRIM write, including the GIFtag PRE bit.

Tools:
* `hud_extract.py` writes one record per PRIM (`hud-prims.json`).
* `hud_render.py` is a CPU rasteriser for the layout. HUD textures do not decode cleanly from the
  dump VRAM (CT32 swizzle/offset unresolved; see below), so use it for layout and untextured
  shapes only.

## Global draw contract

* Drawn into the 640x512 PSMCT16 draw buffer (FBP 0) after the course, the car, the env passes
  and the dust/smoke particle sprites (0x3810/0x3820/0x2e50).
* Each widget part is a TRISTRIP quad (prim 4), attr 0x5c: IIP+TME+ABE+FST=0, so it uses STQ.
* Textures are 64x64 PSMCT32 HUD atlases with TCC=1 and TFX=0 (MODULATE, 127 ≈ 1.0).
* Blending is ALPHA 0x44, `(Cs-Cd)*As+Cd`. ZBUF has ZMSK=1 (no depth writes) and TEST 0x1000.
* No HUD texture uploads happen in the frame: the atlases stay resident in VRAM.
* Coordinates: x is the same as the 640x480 authoring space in `HUD0.XML`, y = authoring y*512/480.
  Example: damage slot x=440,475,510,545,580 maps to 439.4+35k, and authored y=380 (bottom
  origin) maps to slot centre 107.2 = (480-380)*512/480.

## Damage row (HUD-DAMAGE atlases, 2 pages)

The row has 5 slots of 32x32 at x=439.4+35k, y=91.2..123.2. Each slot is drawn in two layers:
1. The icon, tinted with the state colour (vertex RGBA):
   * steering = page A (0x30c0) st(32,32);
   * engine = page A st(0,32);
   * suspension = page B (0x3100) st(32,0);
   * gearbox = page B st(0,0);
   * tyres = page B st(32,32).
2. A common frame over it: page B st(0,32)..(32,62), white (127,127,127,127).

All five icons first, then all five frames.

**State colours (exact vertex RGBA):**

| state | RGB |
|---|---|
| intact (race start) | 127,127,127 (white) |
| 1 | 1,127,1 (green) |
| 2 | 127,127,1 (yellow) |
| 3 | 127,95,38 (orange) |
| 4 | 127,1,1 (red) |

The tyres slot stayed white in every dump.

## EE logic (R5900 Ghidra EE project, `RangeDecomp.java` over 0x140e00..0x143000)

**gaHudAiCarDamage** (update `1414e8`, colour `1412f8`; the owner config `1410d8` binds the eggs
`Car%d_Damage_Steering/Engine/Suspension/Gear/Tyres`). Per frame, per channel:

* The value `d` is read from the car:
  * steering = car+0x108;
  * engine = car+0x104;
  * gearbox = car+0x10c;
  * suspension = max of four wheel floats (+0x9c, +0x48, +0x144, +0xf0);
  * tyres = max of (+0xa0, +0x4c, +0x148, +0xf4).
* The colour is updated only when `d` rises by more than 0.001 over the last value it was
  applied for. It then writes the entity colour and bumps entity+0x88.
* `1412f8`: h = 1 - clamp(d,0,1). The colour is chosen as follows:

| condition | d range | colour | in the dumps |
|---|---|---|---|
| h > 0.8 | d < 0.2 | white (1,1,1) | white |
| 0.6 < h ≤ 0.8 | 0.2 ≤ d < 0.4 | green (0,1,0) | (1,127,1) |
| 0.4 < h ≤ 0.6 | 0.4 ≤ d < 0.6 | yellow (1,1,0) | (127,127,1) |
| 0.2 < h ≤ 0.4 | 0.6 ≤ d < 0.8 | orange (1,0.75,0.3) | (127,95,38) |
| h ≤ 0.2 | d ≥ 0.8 | red (1,0,0) | (127,1,1) |

**gaHudAiCarDamage1** (notification; config `141db8`, tick `142018` → `1422f0` queue, `142ab0`
animate, `142b90` draw; colour `142068` = the same table with alpha 0).

* HUD0.XML egg: `DefaultEggName` at en2d (565,340), Scale 1.5, StartPos = TargetPos = (0,0,0),
  EndPos (0,-50,0), Birth/Death Time 25, Life Time 30.
* `1422f0` queues a 0x24-byte record (icon index: 0 steering, 1 engine, 2 suspension, 4 tyres,
  3 gear) when a channel's colour state changes.
* `142ab0` is a per-record state machine counted in frames (PS2 50 Hz):
  1. Birth: 25 frames.
  2. Life: 30 frames (counter +0xc4).
  3. Death: 25 frames.

  The record is removed after death. When a newer record exists, it starts its birth as the older
  one enters death.
* `142b90` draws the newest two records. For each it draws image `index` (tinted with the state
  colour), then the frame image 5, scaled 1.5:
  * Birth: t = k/25, position = Start + (Target-Start)·t, alpha = clamp(t,0,1). With this XML it
    stays in place and fades in.
  * Death: t = k/25, position = Target + (End-Target)·t·Scale, alpha = 1 - t. It moves 50·1.5 = 75
    authored px down (80 px in the 512-line buffer) while fading out.
* Dump check:
  * alpha 98 → t 0.23 → +19 px (measured 145.3-126.1 = 19.2);
  * alpha 27 → t 0.79 → +64 px (measured 64.0);
  * the 126.1 samples with alpha 32/104/127 are births or hold.

So the notification fades in at the slot, holds, then **slides down and fades out**. The earlier
"rising" reading below was wrong.

## Damage notification (rising and fading)

The notification is the same two-layer icon scaled 1.5 (48x48) at x=564.2..612.2. Samples
(top y / alpha):

* 190.1 / 27
* 145.3 / 98
* 129.3 / 124
* 126.1 / 127 (resting)
* 126.1 / 104
* 126.1 / 32

So it appears ~64 px lower with low alpha, rises to y=126.1 while fading in, stays, then fades out
in place. Two can be visible at once: the older one fades at the top while a newer one rises. The
state colour is the slot's new colour. The timing curve needs the EE owner; alpha and y are not
linear in each other.

## Minimap (gaHudAiMap): untextured, CPU geometry

Draw order (attr 0x14c: IIP+ABE+FST, no texture, all ALPHA 0x44):
1. Background quad, rect 29.0..118.9 x 376.5..459.7, RGBA (22,22,22,31).
2. RaceLine halo strip, (25,76,12,63), about 2 px wider, then the core strip (50,150,25,125).
   About 50–60 vertices each, already clipped to the map rect on the CPU.
3. Split/checkpoint marker quad (125,200,25,125), crossing the line, when one is in range.
4. Player arrow: a shadow (6,12,25,125) offset +3,+3, then the arrow (38,78,160,125). It is fixed
   at the map centre (~74,418): the map is **player-centred and heading-up**.
5. Frame ring (10-vertex strip): a shadow (9,9,9,31) at 23.8..124.1 x 369.9..466.3, then the white
   ring (216,216,216,125).

The PC shows a round GPS radar instead. The PS2 map needs the RaceLine geometry, the player
position/heading and the scale (EE gaHudAiMap, see `../ui2`).

## Other widgets (positions in the 512-line draw buffer)

* Timer (NEWHUD large digits): pages 0x3380/0x3440/0x34c0, x 493..611, y 32.5..56, white.
* RECORD TIME / SPLIT TIME: labels in green (1,127,1), times in white. Small font pages
  0x2d00/0x2d40/0x2d80/0x2e00, 15-px rows at y 57 and 73.
* Rank "1ST": pages 0x2c40/0x2c80/0x33c0 at 21..86 x 33..85.
* Speedometer: plate is 4 quads 0x2a40/0x2a80/0x2ac0/0x2b00 (128x128 at 492..619 x 340..475).
  The needle (0x2bc0 st 32..48) is a rotated quad. Speed digits are 0x3440 at 561..612 x 443..464,
  the gear is 0x2d80 at 584..599 x 419..434.
* Progress bar: caps 0x2b80, middle 0x2bc0 at 127..510 x 437..471. The player marker uses
  0x2bc0 st(48,0..61,16) tinted (19,39,81). Split ticks are on the same page.

## Finish state (dump 195654, "RACE COMPLETE")

* Overhead finish camera; the HUD stays up.
* "RACE COMPLETE" is in NEWHUD large letters (pages 0x33c0/0x3ec0/0x2dc0/0x3300/0x3340/0x3380), white
  with **alpha 69** (semi-transparent), x 200..438, y 235..257.
* "PRESS (X) TO CONTINUE" is in the small font (0x2d00/0x2d40/0x2d80), grey (114,114,114,127), at
  y 268..283. The X button glyph is a separate quad on page 0x3280 at 269..298 x 260..291.
* Minimap finish marker: a white quad (250,250,250,125) across the line.
* The progress marker sits at the finish flag (x 468..481).
* `hud_early.py` lists flat (attr 0x5c) prims before the damage row; the prompt and bar/dial are there.

## Draw order (finish dump, complete)

1. Progress bar: caps and middle, then 3 split ticks and the finish tick.
2. Speedometer plate (4 quads).
3. Prompt line.
4. Timer and RECORD/SPLIT text.
5. Gear, needle, speed digits.
6. Rank.
7. "RACE COMPLETE".
8. Progress marker.
9. Damage icons, then damage frames.
10. Notification. In 195001 it is drawn before the particles.
11. Minimap: background, line halo, line core, markers, arrow shadow, arrow, frame shadow, frame.

## Open items

* The CT32 VRAM decode of this dump format is still scrambled inside blocks; CT16 is mostly
  clean at +373. Textures come from the extracted PSB/GXI assets (`../ui`) instead.
* Damage thresholds and notification timing: solved above. The minimap transform is already in
  `../ui2/findings.md` (scale 0.4, window ±32 markers, clip ±45/±43, centre (74,392) authored =
  418.1 in the 512 buffer, which matches the dump arrow centre).
* PC side: the same five icons exist. Whether and how the PC tints them, and whether the PC has a
  notification, needs a PC screenshot and F10 capture with a damaged car.

## PC comparison (MRallye.exe bf8aef32, user screenshots and F10 2026-10-17 20:00–20:09)

* The PC has `gaHudAiCarDamage` but **no `gaHudAiCarDamage1`** (no notification) and **no
  `gaHudAiMap`**. Instead it has `gaHudAiGPSNeedle` and `gaHudAIGPSOrientedEntity` (the round
  green GPS radar).
* PC row: config `4a41f0` (`Car%d_Damage_*` at 0x6e4eb8..), update `4a4540`, colour `4a4420`.
  Same structure as on the PS2:
  * steering = car+0x104, engine = car+0x100, gear = car+0x108 (PS2 +0x108/+0x104/+0x10c);
  * the suspension and tyre wheel fields are identical (+0x9c/+0x48/+0x144/+0xf0 and
    +0xa0/+0x4c/+0x148/+0xf4).
* PC colour table (h = 1 - clamp(d); constants 0x68f538 = 1, 0x68f53c = 0, 0x690de4 = 0.75,
  0x68f958 = 0.5, 0x68feac = 0.25):

| d | PC | PS2 |
|---|---|---|
| ≤ 0.25 | white | white (d < 0.2) |
| 0.25–0.5 | green | green (0.2–0.4) |
| 0.5–0.75 | yellow | yellow (0.4–0.6) |
| 0.75–<1 | red | orange (0.6–0.8) |
| 1 | **black** | red (≥ 0.8) |

* PC icon art (`DataGx/Hud/hud-damage_000..005`): white 32x32 icons with the frame baked in.
  Index 5 is an empty frame. They are tinted at runtime like on the PS2.
* PC finish: "RACE COMPLETE" is opaque white and the prompt reads "PRESS RETURN TO CONTINUE"
  (PS2: alpha 69/127, grey prompt with the X glyph).
* The PC adds an opponent list under the rank ("U3TEST" with a car icon). This dump set has no
  PS2 counterpart.
* The pace-note sign is on both platforms (the PS2 uses PACENOTES.PSB; not in these dumps).
* The F10 UI draws are DrawPrimitive from a vertex buffer (caller rva 0x16d7c4). Vertex colours
  are not in the trace.

## HUD-PORT4: HUD-TEMPLATE, PC/PS2 HUD0 differences, egg names (2026-10-18)

Tools: `hud_all.py` (every HUD-class prim of a dump frame, from kick 0), `hud_bank.py` (PS2 PSB and PC DXB
F001/125 reader; the PC records have no 16-byte cell), `hud_substitute.py` (PS2 art resampled into the PC
texture of the same image).

* **Bank identity.** In dump 195341, the dial, needle, bar, ticks, finish flag and progress marker match
  HUD-TEMPLATE.PSB image by image:
  * dial: 4 quads, pages 0x2a40/0x2a80/0x2ac0/0x2b00 = HUD-TEMPLATE_001/002/003/004;
  * bar caps: 0x2b80 = _005 st(32,0,64,32) and (0,0,32,32);
  * 0x2bc0 = _006, which holds:
    * needle st(32,0,48,64);
    * bar middle st(48,32,56,64);
    * tick st(56,32,58,48);
    * finish flag st(56,48,64,64);
    * car marker st(48,0,61,16), tinted (19,39,81).

  PC Hud0.xml uses `hud\hud-template` for these eggs too.
* **PC vs PS2 bank geometry.** Image boxes are identical for HUD-TEMPLATE 0, 1, 2, 4, 5, 6, 8, 9, 10, for all of
  NEWHUD, HUD-DAMAGE, CARDAMAGEBITS, MASTER_TEMPLATE and HUD, and for the PSB key mappings. The exceptions:
  * image 3, the progress car: PC car 16x8 vs PS2 arrow 13x16;
  * image 7, the pointer: PC 8x8 vs PS2 16x16;
  * PACENOTES: PC 32 images, PS2 24.

  The PC NEWHUD art is nearly the PS2 art (mean premultiplied difference ≤0.08). The PC HUD-TEMPLATE art was
  redrawn (0.07..0.15, finish flag 0.49):
  * the PC needle is thinner;
  * the PC dial numerals are smaller and its ring thinner;
  * the PC progress bar is a light outline, while the PS2 bar has a dark fill.
* **HUD0.XML diff (PS2 vs PC).**
  * PC-only eggs: `SpeedVelocityText` ("MPH" text, font 101; draws K/P/H at (545,40)), `TimeDiffArrow`
    (hud-template image 7), `GPSBackground`/`GPSNeedle` and `HudOffCourse`.
  * PS2-only eggs: `DefaultEggName` (the damage notification), `Map`, `ConfirmMenuTiles`, `ReplayText`/`1`.
  * `TimeDiffs` uses `gaHudTimeDiffs2Ai` on the PS2 and `gaHudTimeDiffsAi` on the PC (the PC opponent list).
  * Fonts:

    | text | PS2 font | PC font |
    |---|---|---|
    | small: RECORD/SPLIT labels and times, SpeedGear, HudContinue | 102 | 101 or 501 |
    | large: GameTimer, SpeedVelocity, GameComplete, WrongWay, Failed, Reset | 103 | 502 |

  * `GameRank` draws from `HUD/Hud-nums` with font 103 on the PS2.
  * PaceNotes is invisible on the PS2 (en2d Visible False).
  * SpeedDial gear offset: PS2 (35,-24), PC (36,-23).
* **Egg names at runtime.**
  * The baseline UI consumer hook (0x56d110) passes the egg.
  * The egg layout: +0x4c en2d packet, +0x50 en3d, +0x5c name pool id, flag byte bit 1 = retired. The egg
    registry is at base+0x2f96fc, +0x1c (see fleet_participants.hpp).
  * The F10 frame 30009 UI draws group by WORLD translation:
    * dial and needle (565,75); speed digits (570,22); gear (601,52); KPH (545,40);
    * timer (490,440); record/split labels (540,423/408) and times (610,423/408);
    * damage row (440..580,390); bar (128..480,30); rank (20,410); opponent list (20,365).

## TimeDiffs: opponent list (2026-10-18; dumps 20261018 110543 = practice, 111758 = 4-car race start)

### PS2 gaHudTimeDiffs2Ai

Code: vtable 0x44c640; ctor 0x14fa88; methods 0x150108 (config), 0x150250 (load, "Hud No"), 0x1502a8 (init),
0x151120 (tick).

**Init (0x1502a8).**
* N = number of cars. If N < 2, no rows are created: practice shows no list.
* Per car it reads the Broker keys `Race/Car%d/Time`, `Progress`, `Rank`, `Finished`, `Car%d`, `LastMarker`.
* Per car it creates a child entity (0x1501b0) copying the egg en2d matrix, with y += -15·i.
* Font 0x66 = 102. Image bank `Frontend/new/SmallCars/SmallCarSheet`.
* Local car = `Hud No` → car index (+0x18).

**Tick (0x151120).**
1. Every frame, each car stamps the local race time (`Race/Car<local>/Time`) into its per-marker table at its
   `LastMarker`, if that entry is still 0 (0x150fd8).
2. Every 40 frames (0.8 s at 50 Hz), each car's diff is computed (0x150d18):
   * car behind the local car (Progress_i < Progress_local): the local car's stamp at or near (±8) the car's
     LastMarker, minus the car's stamp there (negative);
   * car ahead: T minus the car's stamp at or near the local car's LastMarker (positive).
   * The local car's diff is 0. 0x150f40 also stores Progress.
   * Car 0 has an extra special case through 0x48dd30.
3. Values are put in rank order (`Rank-1`). A monotonic fix is applied: if a[r] < a[r+1], then
   a[r+1] = a[r] - (a[r+1]-a[r])·0.25. Ranks above the local car get negatives cleared to 0; ranks below get
   positives cleared to 0.
4. Row r draws car i (0x150b28):
   * text at +35: the local car or a 0 value shows `--.--` in white (1,1,1,1); otherwise `%.2f` in green
     (0.5,1,0.5,1) when > 0, or in red (1,0.5,0.5,1) when < 0. The colours are statics 0x48dd00/10/20 set
     at 0x158b10.
   * icon at (0,-4): SmallCarSheet image = car table[CarType].+0x18. The car database is built at 0x116f88:
     29 cars, args (id, class, 4 stats, image).

| id | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| image | 9 | 17 | 22 | 15 | 1 | 16 | 20 | 13 | 18 | 7 | 4 | 24 | 19 | 14 | 26 |

| id | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| image | 3 | 25 | 0 | 5 | 11 | 10 | 2 | 27 | 6 | 8 | 28 | 29 | 21 | 23 |

**Font 102 = `\TNG\DATAPSM\FONTS\ARIAL\ARIAL_16.PSB`.** The glyph UV rects for '0', '.', '1' and '7' match
dump 111758 exactly (pages 0x3240/0x32c0/0x31c0).

**Dump 111758 rows:**
* icon 32x17 at x 21.5..53.5;
* text from x 56.5;
* row pitch 16 (512-line) = 15 authored;
* egg at (22,365);
* 3 green `0.17` rows, then the local row `--.--` in white.

### PC gaHudTimeDiffsAi

Code: vtable 0x691058; init 0x4ab040; row set 0x4aae70.

* 3 fixed rows (AI +0xc/+0x10/+0x14): car ahead `-%1.2f`, local name (`Settings/Player%dName`), car behind
  `+%1.2f`. Font 0x65 = 101. Bank `Frontend/RaceResults/SmallCarSheet`.
* The rows are created even in practice (local name row).
* The rows are unnamed entities (0x4aad60). PC egg at (20,380).
* The PC has the same Broker keys plus `Race/Car%d/CarType`.
