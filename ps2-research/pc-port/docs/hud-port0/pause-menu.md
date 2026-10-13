# Bounded PS2 pause-menu comparison

Pause implementation is excluded from HUD-PORT0 and the first plate proposal.
The current native PC pause/replay/Freecam suppression policy remains intact.

Fresh original HUD0 XMLs show a concrete styling difference:

| Authored field | PS2 | Original PC |
|---|---|---|
| Pause/confirm tile bank |`Frontend/new/Tiles/textboxalpha`|`Frontend/Tiles/textbox`|
| Tile owner |`enUITileBox`|`enUITileBox`|
| Tile Width/Height |18/5|18/5|
| Source horizontal/vertical tile count |3/3|3/3|
| Pause chooser owner |`gaFrontendPauseMenuAI`|`gaFrontendPauseMenuAI`|
| Pause chooser position |(320,337)|(320,337)|
| Enabled/list/index/text keys |Race/PauseMenu/Enabled,List,Index,Text|same authored keys|

PS2 exact resource `\TNG\DATAPSM\FRONTEND\NEW\TILES\TEXTBOXALPHA.PSB`
and `TEXTBOXALPHA_000.GXI` were freshly addressed through PackFS and parsed.
Their hashes/counts/texture alpha range are in `source-evidence.json`.
The resource name and stored alpha establish neither active GS blend state
nor the exact pause display. No paired current PS2/PC pause screenshots or live
PS2 pause packets were captured here. Item strings,controllerbuttonicons,
selection/highlight behavior and selected localized font mapping remain UNKNOWN.

Changing just the tile bank could affect other frontend consumers. A future
pause experiment requires exact paused-game scene/chooser ownership and safe
native widget mapping, separate from race HUD mapping. The global H policy
deliberately treats runningrace,ordinarypause,replaypause and pausedFreecam
differently; it must not be replaced with texture or broad2Dcall suppression.

