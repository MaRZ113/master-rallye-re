# HUD-PORT3: PS2 race map (`PS2HudMap=1`)

This replaces the PC round GPS radar with the PS2 gaHudAiMap: a square map centred on the player,
rotated heading-up, with the route line drawn from the course RaceLine markers.

## PS2 contract

Sources: `ps2-research/ui2/minimap.md`, `minimap-format.json`, and the hud-dump1 GS dumps.

* **Transform:** local = 0.4·(Hz·dx − Hx·dz, Hx·dx + Hz·dz), added to the centre (74,392) of the
  640x480 HUD. Clipping is Cohen-Sutherland against ±45 × ±43.
* **Heading:** H = −normalize_xz(forward + 0.1·velocity). Each frame, if Z differs from the
  previous value by more than 0.045, Z steps toward zero by 0.045 (otherwise X does the same), and
  the pair is renormalised (owner +74/+78).
* **Route:** markers in the window max(last−32,0) ≤ i < min(last+32, finish). Each segment is
  stroked on its own (146d80):
  * shadow, width 6, colour (0.2,0.6,0.1)·127, GS alpha 63;
  * front, width 3, colour ·250, GS alpha 125.
* **Finish crossbar:** white (250, GS alpha 125), half-length 12, width 4, placed at the end of the
  finish segment. The length is calibrated to dump 195654; the exact factor 3 × length is not
  recovered.
* **Fixed parts:** the background (22,22,22,31), the chevron and its shadow (+3,+3), and the frame
  and its shadow use the vertex coordinates from dump 195341.
* **GS to D3D:** GS alpha ×2 gives the D3D alpha (0x80 = 1.0); RGB bytes are used as they are
  (untextured).

## PC integration

* **Feed** (`ps2_hud_damage_feed.hpp` `read_map`, read only):
  * The vehicle comes from the same Broker `Car<N>` `gaVehicleOutputData` as the damage feed:
    position +0xec/+0xf4, forward +0xdc/+0xe4, velocity +0x18/+0x20. These are the fields the PC
    GPS (`4a57a0`) reads; on PS2 they sit 4 bytes later.
  * `Race/Car<N>/LastMarker` comes from the Broker.
  * `RaceLine` comes from the marker manager at base+0x2f94e4: lists indexed by pool id, records of
    0x48 bytes, position at +0x38.
  * The finish index is the RaceLine marker nearest to the first `FinishArea` marker, computed once
    per race. The PC has no PS2 `FinishArea/BestMarker` broker value. Without a FinishArea, the
    route runs to the end of RaceLine.
* **Take-over** (`hud_damage_native.hpp`): exact level-0 SHA of `hud-template_001` (radar, 128²)
  or `_007` (pointer, 8²). The map is placed through the radar draw's WORLD·VIEW·PROJ, so the PS2
  640x480 coordinates follow PreserveMargins and the resolution.
* **Layer:** untextured strips (`PS2HudLayer::draw_strips`), drawn after the damage row and before
  PS2Color.
* **Not yet ported:** split crossbars (PS2 split BestMarkers) and opponents' X marks. Fleet races are
  single-car.
* **Log:** `{"type":"ps2_hud_map","feed":...,"layer":...,"strips":N,"last":..,"finish":..,"points":..,"heading":[x,z]}`.
