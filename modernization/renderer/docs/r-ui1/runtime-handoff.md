# R-UI1 Runtime Validation

Use the current test build and the existing display settings. Set `[Widescreen] InterfaceMode=2` (`PreserveMargins`) and keep the accepted Windowed or Borderless mode unchanged. Use 1920×1080 for the primary comparison.

## Vehicle Select

Open a long vehicle list. Capture a stable selection, then move one item at a time through the beginning, middle, and end. Repeat with faster forward movement, reverse movement, and any list wraparound. Compare the yellow selection frame with the selected small thumbnail and the large 3D preview. Confirm that the list continues to scroll and no thumbnail disappears.

## Race Select

Repeat on a long course/leg list. Check the frame, selected course image, description, and any neighboring cards while moving forward and backward. Confirm that the visible selected card and the game's displayed course data remain in agreement.

## Other screens and gameplay

Check Main Menu, game-mode selection, options, vehicle-class selection, and animated menu decorations. Start a Quick Race, inspect the HUD, pause and resume, and change cameras. PreserveMargins should retain its previously accepted HUD/menu behavior. Then check Centered4x3 and Stock for regressions.

If a carousel still misaligns, trigger the existing F10 capture while the selected frame and adjacent cards are visible. Capture the three-frame window on each affected screen and attach the resulting current-build session JSONL plus a screenshot. For movement provenance, capture once while stationary and again immediately after one forward and one reverse step. Keep Race Select and Vehicle Select captures separate.

The `ui_packet_lifetime` record associates `entity`, `packet`, point storage, content storage, mode, anchor ID/source/direction, current historical rule, UI epoch, and engine XY with up to eight enclosed `draw_observations`. Compare `packet_x/y`, caller RVA, FVF, requested/applied margin, `native_world_x/y`, and `effective_world_x/y` between the card and frame candidates. `carousel_owner_status=not_proven` is expected until source or capture evidence establishes membership. The diagnostic does not read selection indices.

PASS for visual behavior requires both carousel families to align while scrolling, with no list/input/preview regression. If the visual defect remains, the capture should show whether the mismatch tracks a retained anchor, a different draw path, or unchanged paired transforms. Do not infer selection-index corruption from an empty highlighted slot alone.
