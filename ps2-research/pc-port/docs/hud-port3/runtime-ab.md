# HUD-PORT3 runtime A/B

Replace only `d3d8.dll`. In `PS2Port.ini` add `PS2HudMap=1` and keep `PS2HudDamage=1`.

1. Turkey, SeatBuggy, race start: the bottom-left round GPS should be replaced by the PS2 square
   map:
   * dark translucent background with a white frame;
   * a blue chevron in the middle;
   * a green route line ahead of it.
2. Drive: the map should turn with the car (heading-up) and the route should scroll under the
   chevron. Near the end of the stage, a white finish bar should appear across the line.
3. Compare with the PS2 screenshots (same corners). Check the line width, the colours and how far
   ahead the route reaches (32 markers).
4. H key, Clean View and the pause menu: the map should hide together with the PC HUD.

Logs: `ps2_hud_map` should show `"feed":"live_raceline"`, `"layer":"ps2_hud_strips_drawn"`, and a
changing `"last"`. Send the line together with an F10 capture if the map is missing or wrong.
