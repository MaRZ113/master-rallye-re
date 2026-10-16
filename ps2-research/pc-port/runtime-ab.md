# PILOT1.3 France1 `bush01` four-mode A/B

Use the same PS2-enabled `d3d8.dll`, France1 course, Free Camera bookmark,
view direction, FOV, resolution, and graphics settings for all four captures.
Keep `Diagnostics=1` so device setup logs the selected mode once and modes
1–3 log the first exact target draw once per device. Restart the game for every
mode: CPU upload mirroring must be active before the course vertex and index
buffers are created.

## State policy

| `FoliageMode` | Alpha test | Alpha blend | Source / destination blend | Depth write | Override mask |
|---:|---|---|---|---|---:|
| 0 | Stock | Stock | Stock | Stock | `0x00` (no request) |
| 1 | `FALSE` | `TRUE` | `SRCALPHA` / `INVSRCALPHA` | `FALSE` | `0x1F` |
| 2 | `FALSE` | `TRUE` | `SRCALPHA` / `INVSRCALPHA` | Preserve current PC value | `0x0F` |
| 3 | Preserve current PC value | Preserve current PC value | Preserve both current PC values | `FALSE` | `0x10` |

Mode 1 is the previously tested approximation. Mode 2 keeps the alpha/blend
part and removes the depth-write override. Mode 3 keeps the PC alpha/blend
state and changes only depth writes. The native-state transaction reads,
validates, writes, rolls back, and restores only states named by the mask.

## Capture sequence

1. In a separate test installation, manually place the PS2-enabled DLL and
   `PS2Port.ini` beside `MRRRenderer.ini`. Do not replace the pristine install.
2. Set `FoliageMode=0` and `Diagnostics=1`; launch France1 and load the saved
   Free Camera bookmark. Capture the target bush and its neighboring trees.
3. Change only `FoliageMode` to `1`, restart, and capture from the same
   bookmark. Repeat for modes `2` and `3`.
4. Keep the four screenshots and renderer logs together. Each mode should
   report the same geometry digest and current resource generations. The
   `ps2_port_mode_selected` record logs the selected mode and configured mask
   once per device. For modes 1–3, the single
   `ps2_port_draw_identity` record includes `mode`, `mode_name`,
   `requested_mask`, the actually applied `applied_mask`, `override_applied`,
   and whether a failed pre-draw apply was restored. Expected masks for modes
   0–3 are `0`, `31`, `15`, and `16` respectively. Mode 0 does not mirror
   buffers or classify a target draw, so it has no `ps2_port_draw_identity`
   event; its selected-mode record shows mask 0 and no applied override.
5. Compare silhouette, occlusion by nearby trees, alpha edges, and ground/tree
   overlap. If mode 2 is visible while mode 1 is not, depth-write behavior is
   implicated; if mode 3 is visible while mode 0 is not, alpha/blend behavior
   is implicated. Mixed results can indicate an interaction. These are
   diagnostic observations, not proof of a unique renderer root cause.

Do not change textures, sorting, draw count, camera bookmark, or other game
settings between modes. The pilot retains the PC `bush01-tga` texture and does
not reproduce PS2 GS blending exactly. Neither the build nor these captures
establish PS2 visual parity.

## Runtime evidence already supplied

The user reports that a PS2-enabled run produced 5,364 successful target
identity events, with F10 frame 7608 showing the exact draw
`DrawIndexedPrimitive(4,11940,28,22944,48)` and `override_applied=true`. The
reported state trace shows the temporary alpha/blend/depth-write changes and
restoration succeeding. Stock frame 4311 contains the same draw without an
override. The target occurred at draw 46 of 704, with many later depth-writing
draws. The user observed that the foreground bush became mostly invisible,
with partial visibility around and through neighboring foliage.

This establishes the reported live target and current visual symptom. It does
not distinguish draw ordering from alpha/texture-stage interaction. PILOT1.3
is intended to isolate those variables. The underlying captures were supplied
as runtime observations and are not bundled with this source handoff.
