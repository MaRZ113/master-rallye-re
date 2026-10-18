# HUD-PORT2 runtime A/B

## Install

* Replace `d3d8.dll`.
* Copy the `PS2Hud` folder (two .gxi files) next to `PS2Port.ini`.
* In `PS2Port.ini` set `PS2HudDamage=1`. `PS2HudAssetDir=PS2Hud` is the default.

## Checks

1. Race start (Turkey, SeatBuggy): the damage row shows five white icons with white frames, in the
   same place as the PC row. Check both a windowed 640x480 run and full screen (PreserveMargins).
2. Crash lightly, then harder. Each icon should go white → green → yellow → orange → red, with no
   black. On every colour change, a 1.5× icon appears below-right of the row: it fades in, holds
   ~0.6 s, then slides down and fades out.
3. Pause, the H key (HUD hide) and Clean View: the row and the notification disappear with the PC
   HUD and come back with it.
4. Finish screen, then restart the race: the row is white again.
5. Optional: set `PS2HudDamage=0` for an A/B against the PC row. Damage at 0.75–1 is red on the
   PC and orange or red on the PS2 layer.

## Logs

`session-*.jsonl` should contain `ps2_hud_damage` lines:
* `"feed":"live_vehicle_output"` and `"layer":"ps2_hud_damage_drawn"`;
* `"values"` rising when you crash.

Send any other `feed`/`layer` reason and an F10 capture if something looks wrong.
