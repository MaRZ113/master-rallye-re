# Next PS2 phase

Recommend **PS2-UI2: dynamic HUD ownership / minimap**, not a PC HUD port.
The fixed asset layer is now deterministic and useful; the strongest remaining
gap is how owners select these image banks and place course-dependent overlays.
The screenshots show a route minimap that is not explained by either the
striped world-map texture or the fixed circular radar bank.

Bound the next pass to gaHudLoader/scene selection, gaHudAiMap, GPS/vehicle
markers, gaHudAiRaceProgressBar and gaHudAiSpeedDial/Needle. Start from the
exact ELF addresses/vtables in `elf-ui-map.md`, authored HUD0/HUD1 values and
the complete NEWHUD glyph map. Resolve active-bank selection and local/image/
entity/viewport coordinates before trying to reproduce a whole HUD frame.
Prove course-path ownership and transformations with runtime evidence; retain
unknowns for screen centering, split screen, tint and draw order.

Use the existing master worktree and `ps2-research/` conventions. Preserve the
hash-locked PackFS/PSB regression baseline. Do not turn the present screenshot
correlation into confirmation of an exact emulator build or frame trace.

GRASS1/BUSH1 have clean alpha cutouts and are credible later GRASS1 inputs;
WATERSURFACE2 and the static environment captures now have verified byte
metadata. Their rendering code paths have not been analyzed and are weaker
next steps than closing the identified dynamic UI gap. No next phase was
started by PS2-UI1.
