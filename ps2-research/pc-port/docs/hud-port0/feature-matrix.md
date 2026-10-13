# PS2 versus PC feature matrix

Screenshots were inspected at their original paths. They are user-supplied views,
not a synchronized cross-platform capture: time, vehicle pose, projection and
presentation sizes differ. Sponsor banners are not used as platform evidence.
Screenshot appearance is `SCREENSHOT_CORRELATION`; source XML/PSB facts below
are `CONFIRMED_BY_BYTES`. Runtime packet observations are separately labeled.

| Element | PS2 evidence | PC evidence | Future port / immediate limitation |
|---|---|---|---|
| Tachometer plate | `HUD-TEMPLATE.PSB`, key/image0, eight source triangles/four 64x64 texture quadrants, local bounds `[-64,-63,64,65]`; HUD0 `SpeedDial` at `(557,98)` | HUD0 `SpeedDial` references `hud\\hud-template`, key0, authored `(565,75)`; original plate `hud-template_000_000.dxt` is128x128 | **First candidate:** private PSB-derived plate at the existing PC draw/placement. Need exact semantic native widget + compiled sprite/UV correspondence. Do not globally replace a shared texture. |
| Needle / tachometer feed | `gaHudAiSpeedNeedle`; initialized from dial broker coordinates; key2/local bounds `[-8,-55,8,9]` | Same authored owner family and key2; original PC needle texture16x64 | Retain original PC needle/data updates in first pilot. Both authored dial configs have angles−110..70°, max8000revs, zero needle offset. Complete PS2 per-frame rotation math and PC-to-PS2 RPM units are not revalidated. |
| Speed / gear | Separate `enUIText` + `gaHudAiSpeedCounter` / `gaHudAiGearCounter`; FontNo103 /102; gear offset `(35,-24)` | Same separate counter owners; FontNo502 /501; gear offset `(36,-23)` | Keep native feeds. Full font replacement needs numeric-to-bank resolution, glyph metrics/locale and packet ownership. Neither screenshot gear value nor authored `Speed Display in KPH=False` establishes final runtime units. |
| Minimap versus GPS | Model-Null `Map`, `gaHudAiMap`; direct logical center `(74,392)`,90x86 clip, RaceLine segments, participant positions, heading transform and stroked packets | `GPSBackground` key1 and `GPSNeedle` key7 at `(65,60)`; GPS owner config names RaceLine, `Use FlowSystem=False` | **Behavioral HUD port**, not an image swap. Requires live PC vehicle position/heading, LastMarker/finish/splits/opponents and route identity. PC runtime offsets cannot be borrowed from PS2. |
| Race progress | `gaHudAiRaceProgressBar`, key8 at `(320,55)`;40middle pieces authored; car/split/finish owners | Same authored owner families/key assignments and40middle pieces; bar at `(320,30)` | Reuse native progress feed after widget mapping. PS2 full dynamic strip extent, tint and queue composition remain unknown. Source mesh/image count is not native draw count. |
| Position / rank | Default `HUD/newhud` in recovered rank constructor; complete decimal key mapping, not four-glyph HUD-NUMS; authored `(22,401)` | `GameRank` + `gaHudRankAi`, authored `(20,410)`; native semantic owner not named by capture | PS2 font/sprite assets exist; safe styling needs active rank owner/key commands, suffix localization and current layout. Screenshot numeral resemblance is not packet identity. |
| Time / record / split | Separate owner/UIText records, timer at `(494,430)`, FontNo103; localized labels distinct from changing numbers | Timer at `(490,440)`, FontNo502 and separate native time owners | Keep PC timing calculations; replace presentation only after font/key and widget mapping. Unit/format/locale semantics are not recovered just by `00:00:00`. |
| Damage/status icons | `HUD-DAMAGE.PSB` siximages/12triangles; five named symbols plus overlay; X440,475,510,545,580/Y380 | Same five named source icons/overlays, Y390; `gaHudAiCarDamage` controller; separate32x32PC textures | Suitable later asset/layout pilot. Need damage-state/overlay mapping and exact target entity, preserving dynamic tint/blink. Green PS2 engine screenshot alone does not identify a numerical damage threshold. |
| Pace notes | `PACENOTES.PSB`,24images/48triangles; authored `(320,418)`; image index versus gameplay enum unresolved | Same owner family at `(320,406)`, native fade/drop settings | Assets transferable locally; triggering, enum and fade semantics not closed. Excluded from first pilot. |
| Anchors / aspect | Code-defined640x480 logical domain; ordinary sprite localY flip and half-pixel bias; final video/display composition partial | Native PC UI projection captured at640x480; current PreserveMargins uses verified render-local WORLD/projection behavior | Preserve PC coordinates first. Do not fit screenshot ratios or force PS2video/interlace factor into PC. Future widescreen policy must compose with existing PreserveMargins, not duplicate it. |
| Pause menu | PS2 authors `Frontend/new/Tiles/textboxalpha` | PC authors `Frontend/Tiles/textbox`; same chooser key names and tile count | Source styling differs; exact paired pause appearance/current strings and controller icons unknown. Research only; no pause implementation. |

Sources: [original PS2 contract](ps2-contract.md), [PC boundary](pc-integration.md)
and compact hashes/records in [source-evidence.json](source-evidence.json).

Inspected image provenance:

| Image | Dimensions | SHA256 |
|---|---|---|
| `MRallye_7qd231CnzV.png` |640x480|`f1a6efe13e2077be0c1294206310a49421036c14a51333fc0d588971b3e44f9e`|
| `Master Rallye_SLES-50906_20261013143351.png` |1318x981|`41d062fce138cb8c451c9026489419037a825e531954dfe5694d781301be479d`|
| `pcsx2-qt_ohPs8K5SFG.jpg` |1303x981|`a4bc2e95dcbf5f7c8fbba0ca19ab23c740025838fe0861e79e0c83eec1a74845`|

The screenshot files remain external; no screenshot or proprietary sprite
image is included in this research directory/handoff.

