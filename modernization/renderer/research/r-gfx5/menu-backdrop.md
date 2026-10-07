# Menu backdrop boundary and replacement seam

**BACKDROP_ASSET_EXTENSION_REQUIRED.** No runtime side-fill, horizontal stretching, UI clipping or texture replacement is enabled. Central art and all original assets remain unchanged.

The read-only [manifest](menu-backdrop-map.json) follows retail XML egg -> en2d Model Name -> DXB tag125 image bank -> exact DXT tile file/content hash. These are asset semantic identities, distinct from an unproven native draw identity.

| Screen XML | Egg / resource | Authored matrix / priority |
|---|---|---|
| MainMenu | Background / frontend/backgrounds/bg_newmainmenu | Identity / 6 |
| QuickRace | Background / frontend/backgrounds/bg_quickrace2 | Identity / 6 |
| QuickModeSelect | Background / frontend/backgrounds/bg_quickmodeselect | Identity / 6 |
| RaceResults | BG / frontend/backgrounds/bg_raceresult | Identity / 6 |

Each bank references six different tiled DXT textures (two rows, widths256/256/128). No clean repeatable side layers or hidden widescreen art are established. The decoder verifies DXT20-byte header, dimensions, exact BGRA payload size, full file/upload hashes and alpha values. The manifest deliberately does not invent a generic DXB geometry/UV decoder.

The known candidate route is DrawTextPacket VA0056D110/RVA0016D110, FVF0x142/stride24, dynamic glyph/quad VB, final DrawPrimitive return0016D7C4. This shared route also draws text/buttons/decorations. Candidate caller, primitive order, matrix or tile dimensions alone cannot promote UI_MENU_BACKDROP. Existing menu F10 confirms this packet caller and alpha-blended SRCALPHA/INVSRCALPHA draws, but it does not identify which native texture generations correspond to these six assets. Exact tile-specific UV/quad bounds and upload/generation correlation remain UNKNOWN.

Replacement seam: the manifest reserves UI_MENU_BACKDROP only for the XML-bank-content chain and supplies full BGRA hashes for future upload association. An eventual runtime resolver must match content plus current generation and bank/quad association; absent proof yields UNKNOWN and unchanged forwarding. A future extended asset preserves central logical [0,0,640,480] at unit scale and fills canvas[-half,0,640+half,480], half=(480*aspect-640)/2. At4:3 half=0, exact stock behavior. The same contract serves both UI modes, without moving buttons inward. It is infrastructure/evidence, **not a full replacement loader or active native draw classifier**.

Stage E may therefore report this explicit art boundary; do not call black-side coverage fixed. Priority after human code acceptance is R-CAM1 -> F-PHOTO1 -> HD UI restoration/side-extension artwork. No art generation or asset rewriting in this pass.
