# PORT3 fix8: PS2Port.ini v2 and PS2ContentFixes

Includes fix7 (UFO OFF retail dome order).

## Config v2

`renderer/ps2_config.hpp` routes all 55 `[PS2Port]` reads in 12 modules. Final keys and mapping:
`docs/config-v2.md`; new `PS2Port.ini.example`; the user's Pristine INI migrated in
`docs/config-v2/PS2Port.ini.migrated-pristine` (same behaviour + `PS2ContentFixes=1`).
`RaceFleet` drives every former race/X-Trail/pilot switch; `Diagnostics` drives every
per-feature log and F10 capture flag except the mirroring-forcing geometry probe. Historical
keys are read only when their v2 key is absent, so old INIs and test fixtures keep working.
Test: `config_v2_contract` (v2 precedence, umbrellas, legacy fallback, caller defaults).

## PS2ContentFixes=1 (default 0 = original PS2 content)

Corrected private assets (research and generator: `crew-face1/`), pinned in
`renderer/ps2_content_fixes.hpp`, loaded in place of the original pinned profile asset with
identical counts/mesh order/modes/textures, so all keyed tables stay valid; a missing or
mismatching corrected file keeps the original and logs `ps2_content_fix` status
`content_fix_unavailable`:
- NAVARA-CREWFACE1 (race CAR): co-driver face triangles moved from the lamp mesh to the
  underdash2 carflat mesh, as in every other crewed family.
- TATA-WINDOW1 (race CAR): the always-drawn cracked right-window copy (root.22) becomes zero-area.
- KAMAZ-COMPLETE-WINDOW1 (menu model): same for root.20.
- KAMAZ-CAR-WINDOW1 (race CAR): same defect, confirmed by the user.
Test: every corrected asset decodes only under its own pin, with original counts, modes and texture
bindings; the original never passes under the corrected pin.

These are deliberate, opt-in deviations from original PS2 content.
