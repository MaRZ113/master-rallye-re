# HUD-PORT2: PS2 damage row and damage notification (`PS2HudDamage=1`)

This is the first PS2 HUD widget pair. The PS2 port draws it as its own layer before Present, from
the game state, and it replaces only the exact PC damage row.

## PS2 contract (ps2-research/hud-dump1/findings.md)

* **Colour per channel** (R5900 `1412f8`): h = 1 - clamp(d), then the PS2 bands below. The colour
  is applied only when d rises by more than 0.001 (PS2 1414e8). A new race resets it.

  | d | colour |
  |---|---|
  | < 0.2 | white |
  | 0.2–0.4 | green |
  | 0.4–0.6 | yellow |
  | 0.6–0.8 | orange (1, .75, .3) |
  | ≥ 0.8 | red |

  The PC (`4a4420`) uses 0.25 bands, has no orange and adds black.
* **Slot drawing:** the icon image is drawn tinted, then frame image 5 in white. The images come
  from HUD-DAMAGE.PSB on pages HUD-DAMAGE_000/001. The PS2 VRAM holds these pages with their rows
  reversed, so the decoder reverses the rows and the PSB UVs are used as they are. Bilinear
  filtering, half-texel inset (PS2 region clamp).
* **Notification** (`142ab0`/`142b90`, HUD0.XML `DefaultEggName`): one notice per colour change,
  with the icon scaled ×1.5. Phases, at 50 Hz:
  1. Birth: 25 frames, fades in, stays in place.
  2. Life: 30 frames.
  3. Death: 25 frames, slides 75 authored units down and fades out.

  When a notice starts dying, the next one is born, so at most two are visible. The anchor is the
  PS2 offset (-15, -40) from the tyres slot (PS2 egg 565,340 vs row 580,380). The PC has no
  notification.

## PC integration

* **Feed** (`renderer/ps2_hud_damage_feed.hpp`, read only):
  1. Find N, the single `Race/Car<N>/PlayerType == 1`.
  2. Look up the Broker key `Car<N>`. It must have tag 10 and type `gaVehicleOutputData`.
  3. Read the vehicle: steering +0x104, engine +0x100, gear +0x108.
  4. Read the wheels: suspension and tyres are each the max of four floats.

  These are the same fields the PC row reads in `4a4540`. Pool ids are cached per race generation.
* **Take-over** (`renderer/hud_damage_native.hpp`, patch 0001 `draw_primitive_at`):
  * Applies to a UI draw (caller 0x56d7c4, FVF 0x142, TRIANGLELIST) when stage0 is one of the six
    PC `hud-damage_00k` textures. The match uses the exact level-0 SHA, cached per resource
    generation, on a lockable 32x32 32-bit texture.
  * It requires the previous Present to have had a live feed.
  * The draw is not forwarded. Its final WORLD (after the PreserveMargins UiWorldScope), VIEW,
    PROJECTION and viewport are kept, so the PS2 row sits where the PC row would.
* **Layer** (`PS2HudLayer`): drawn first in the Present chain, before PS2Color, PS2Output and
  PS2MotionBlur. It covers all native state with a capture and restore. It draws nothing in a frame
  where the PC drew no damage row (hidden HUD, menus, attract demo, Clean View).
* **Assets:** `tools/prepare_hud_damage_asset.py` extracts the pinned TNG payloads into
  `.assets/hud/`. The kit ships them as `PS2Hud/PS2HudDamage000.gxi` and `PS2Hud/PS2HudDamage001.gxi`.
* **Log:** `{"type":"ps2_hud_damage","feed":...,"layer":...,"quads":N,"suppressed":N,"values":[...]}`
  on each change of reason.
