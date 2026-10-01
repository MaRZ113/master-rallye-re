# Retail Vehicle Select scene inventory

## Scene structure and widget contract

`DataScene/FrontendScreens/VehicleSelect.xml` has an
`EggLists_Version4/List Name="VehicleSelectScreen"` for screen controls and a
sibling `List Name="cars"` for car icon widgets. The 25 stock `Tn_CarN` objects
are direct children of `cars`; there is no `T3_Car12` object.

All 25 stock icon widgets have these shared fields:

- `en2d Model Name = frontend\\vehicleselect\\carsheet` and `en2d FileType = 1`.
- `en2d Image Bank Index` is a literal frame selector stored in the scene.
- `en2d Matrix Row3 = 340.00 309.00 0.00 1.00`; the other matrix rows use the
  identity transform. `en2d Visible = True` in the source scene.
- One `gaFrontendXYButtonAI`: Button ID 1, X ID equal to class-local index,
  Y ID equal to class row (T1=0, T2=1, T3=2), and XPos* bound to
  `Frontend/VehicleSelect/Button<local>XPos`.
- Indexed DXT frames are 128x128 RGBA images; the scene has no per-widget size
  override.

The first normally selectable entries are free of unlock AIs. Later entries
carry both `gaFrontendDisablerAI` and `gaFrontendButtonUnlockerAI`. In retail,
T1 local 3–6, T2 local 3–6 and T3 local 4–10 are lock-gated. T3_Car11 / ID24
uses `Progress/UnlockedCars/Bonus1`. The proposed diagnostic widget clones
T3_Car1, which has no slot-specific unlock behavior.

## T1 icons

| Local | ID | Widget | Carsheet frame | XPos key | Unlock AI |
|---:|---:|---|---:|---|---|
| 0 | 0 | T1_Car1 | 3 | Button0XPos | no |
| 1 | 1 | T1_Car2 | 10 | Button1XPos | no |
| 2 | 2 | T1_Car3 | 18 | Button2XPos | no |
| 3 | 3 | T1_Car4 | 27 | Button3XPos | yes |
| 4 | 4 | T1_Car5 | 19 | Button4XPos | yes |
| 5 | 5 | T1_Car6 | 17 | Button5XPos | yes |
| 6 | 6 | T1_Car7 | 16 | Button6XPos | yes |

All use Y ID 0.

## T2 icons

| Local | ID | Widget | Carsheet frame | XPos key | Unlock AI |
|---:|---:|---|---:|---|---|
| 0 | 7 | T2_Car1 | 23 | Button0XPos | no |
| 1 | 8 | T2_Car2 | 1 | Button1XPos | no |
| 2 | 9 | T2_Car3 | 2 | Button2XPos | no |
| 3 | 10 | T2_Car4 | 12 | Button3XPos | yes |
| 4 | 11 | T2_Car5 | 20 | Button4XPos | yes |
| 5 | 12 | T2_Car6 | 9 | Button5XPos | yes |
| 6 | 13 | T2_Car7 | 24 | Button6XPos | yes |

All use Y ID 1.

## T3 icons

| Local | ID | Widget | Carsheet frame | XPos key | Unlock AI |
|---:|---:|---|---:|---|---|
| 0 | 14 | T3_Car1 | 6 | Button0XPos | no |
| 1 | 15 | T3_Car2 | 13 | Button1XPos | no |
| 2 | 16 | T3_Car3 | 5 | Button2XPos | no |
| 3 | 17 | T3_Car4 | 11 | Button3XPos | no |
| 4 | 18 | T3_Car5 | 8 | Button4XPos | yes |
| 5 | 19 | T3_Car6 | 7 | Button5XPos | yes |
| 6 | 20 | T3_Car7 | 0 | Button6XPos | yes |
| 7 | 21 | T3_Car8 | 28 | Button7XPos | yes |
| 8 | 22 | T3_Car9 | 26 | Button8XPos | yes |
| 9 | 23 | T3_Car10 | 21 | Button9XPos | yes |
| 10 | 24 | T3_Car11 | 30 | Button10XPos | yes; Bonus1 |
| 11 | 25 | **T3_Car12 absent** | **no binding** | Button11XPos | n/a |

All use Y ID 2. Frame 5 is already a stock Astero image assigned to T3_Car3 / ID16.

## Code boundary and root cause

The raw Bridge export `research-output/r5v_e0_2/ghidra/481950.asm` shows
`FUN_00481950` iterating `ESI=0..11` and formatting
`Frontend/VehicleSelect/Button%dXPos`; the loop ends with `CMP ESI,0xC`.
Thus the position-key updater covers 12 local columns and is not capped at 11.
It does not assign the icon's `en2d Image Bank Index`. Neither the source XML
nor `VehicleSelect.hnt` contains a static `Button11XPos` string; the executable
constructs that property at runtime in the verified loop, so the candidate
widget binds to a key the updater already creates.

`FUN_00481E20` maps class-local state to absolute IDs with current bases 0, 7
and 14. For T3 local 11, the result is ID25. The stock selection data path
therefore reaches the expected ID, while the `cars` list lacks the matching
X=11/Y=2 button and carsheet frame. The missing icon is classified
**SCENE_OBJECT_MISSING**. The stock retail class capacity (7/7/11) and the
separately runtime-confirmed ID25 setup are outside this scene-only overlay.

No vehicle record field or resource-family lookup drives this widget's frame.
`smallcarsheet_index` is a different selector used for race/HUD/results icons;
it is not reused here.
