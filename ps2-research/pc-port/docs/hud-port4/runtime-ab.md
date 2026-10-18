# HUD-PORT4 runtime A/B

Install:
1. Replace `d3d8.dll`.
2. Copy `PS2Hud/PS2HudTemplate.bin` next to the existing `PS2Hud/PS2HudDamage00x.gxi`.
3. In `PS2Port.ini`, add `PS2HudTemplate=1` and `PS2HudHidePcOnly=1`. Keep `PS2HudDamage=1` and `PS2HudMap=1`.

Checks:
1. **Turkey, SeatBuggy, race start, PS2HudTemplate=1**, compared with PS2 screenshot 195341:
   * speed dial: bolder, larger numerals 0..8 and a thicker ring;
   * needle: a thick white bar;
   * progress bar: a thick white outline with a dark translucent fill;
   * finish flag: a coarse checker.

   The needle must still turn with the revs. The split ticks and the finish flag must stay in their places.
2. **PS2HudTemplate=0**: the PC art comes back unchanged.
3. **PS2HudHidePcOnly=1**: "KPH" (or "MPH") under the speed disappears. In a race with AI, the opponent list
   under the rank ("U3TEST" with a car icon and a green arrow) disappears too. The pause menu, the pace notes,
   "WRONG WAY" and "OFFCOURSE" must stay.
4. **Clean View, H, pause menu and finish**: all elements behave as before.

Logs:
* `ps2_hud_template` should show `"reason":"race_hud_context"` and a growing `substituted`, and `hidden` should
  be above 0 when KPH is hidden.
* Send the `ps2_hud_eggs` line: it lists the HUD element names the game drew, and it is needed for the font
  step.
