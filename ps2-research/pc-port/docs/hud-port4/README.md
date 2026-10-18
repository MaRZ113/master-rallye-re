# HUD-PORT4: PS2 HUD-TEMPLATE art and no PC-only HUD elements

INI keys:
* `PS2HudTemplate=1`: draws the PS2 art for the speed dial, the needle and the race progress bar.
* `PS2HudHidePcOnly=1`: hides the HUD elements that the PS2 HUD does not have.

Both keys are opt-in and default to 0. They need `PS2Hud/PS2HudTemplate.bin` next to `PS2Port.ini`.

## Evidence (ps2-research/hud-dump1, findings.md "HUD-PORT4")

* **Same bank.** PC `Hud0.xml` and PS2 `HUD0.XML` both draw the speed dial, needle, split ticks, finish flag and
  progress bar from the image bank `hud\hud-template`.
  * The PS2 GS dumps match HUD-TEMPLATE.PSB exactly:
    * dial pages 0x2a40..0x2b00 = HUD-TEMPLATE_001..004;
    * 0x2b80 = _005 (bar caps);
    * 0x2bc0 = _006 (needle st 32..48, bar middle, ticks, finish, marker).
  * The PC stores the same 11 images, one texture per image (`hud-template_000..010`). The PC `.dxb` uses the
    same F001/125 format as the PSB, and its authored XY geometry is identical for images 0, 1, 2, 4, 5, 6, 8, 9
    and 10.
* **The PC re-authored the art.** The PC needle is thinner, the dial numerals are smaller and the ring is
  thinner. The PC progress bar is a light outline; the PS2 bar is a thick outline with a dark fill, and the PS2
  finish flag has a coarser checker.
* **PC-only elements.** These eggs exist only in the PC `Hud0.xml`:
  * `SpeedVelocityText`: the "MPH"/"KPH" text under the speed, font 101;
  * `TimeDiffs`: `gaHudTimeDiffsAi`, the opponent list under the rank (the PS2 uses `gaHudTimeDiffs2Ai`);
  * `TimeDiffArrow`: hud-template image 7.

  `GPSBackground` and `GPSNeedle` are also PC-only; PS2HudMap already replaces them. `HudOffCourse` is PC-only
  too but is kept, because it is gameplay feedback.

## Implementation

* **Asset.** `tools/prepare_hud_template_asset.py` builds the asset from the original PS2 HUD-TEMPLATE PSB and
  GXI pages (TNG) and the PC `hud-template.dxb` and `.dxt` files.
  * For every texel of the PC texture: PC uv -> authored xy (PC triangle) -> PS2 uv (PSB triangle) -> GXI texel.
    Raw row 0 is PSB v 1. GXI alpha is already 8-bit (0x80 = half) and is kept as is; HUD-PORT4 doubled it, which
    made the dark dial and bar fills opaque.
  * The output is `PS2HudTemplate.bin` ('MRHT' v2). Each image entry stores its index, the PC size and level-0
    SHA-256, the PS2 texture size, the remap and the PS2 pixels.
  * **Progress car (image 3, HUD-PORT4.1).** The PS2 box is the arrow (-5,-6)..(8,10), the PC box is the car
    (-5,-3)..(11,5). The PS2 arrow is resampled into 16x16. At draw time the PC quad is remapped onto the PS2 box
    through a temporary WORLD (x' = 0.8125x - 0.9375, y' = 2y, in authored units before WORLD), and WORLD is
    restored right after. The tint stays the PC vertex colour (PC and PS2 both tint this white image per car).
  * The runtime checks every entry against the table in `renderer/ps2_hud_template.hpp` (both SHAs).
* **Substitution** (`hud_damage_native.hpp`).
  * Condition: a UI draw (caller 0x56d7c4, FVF 0x142, triangle list, render thread) whose tracked stage0 texture
    is an exact PC hud-template image 0, 2, 4, 5, 6, 8, 9 or 10.
  * The draw is issued with the PS2 texture bound, then the PC binding is restored. Geometry, needle rotation,
    WORLD (PreserveMargins included), colours and blend states stay the PC draw's own.
  * If the restore fails, the feature is disabled. If the draw fails, the PC draw is forwarded unchanged.
  * The feature works only while the last Present had a certified race HUD context.
* **Egg names** (`ps2_hud_eggs.hpp`).
  * Patch 0001 adds `UiMargins::current_entity()`: the egg whose UI packet the baseline consumer hook
    (0x56d110) is consuming. `capture_ui_draw` receives it together with the draw's start vertex.
  * An egg's name is the pool text at egg+0x5c. It is accepted only if all of these hold:
    * the egg registry (base+0x2f96fc, +0x1c) lists this egg under that id;
    * the egg is not retired (flag bit 1);
    * the text is printable.
  * With `PS2HudHidePcOnly=1`, the draws of the three PC-only eggs are not forwarded.
* **Not covered yet**:
  * Fonts. The PS2 uses fonts 102 (small) and 103 (large) where the PC uses 101, 501 and 502. This affects the
    RECORD/SPLIT labels, the gear and "RACE COMPLETE".
  * The finish text style.

## Log

* `{"type":"ps2_hud_template","reason":...,"template":..,"hide_pc_only":..,"substituted":N,"hidden":N}`: logged
  whenever the reason changes.
* `{"type":"ps2_hud_eggs","names":[...]}`: the distinct egg names seen in UI draws during the race. It is logged
  when the set grows and is the runtime proof of the egg-name read.
