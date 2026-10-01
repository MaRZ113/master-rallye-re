# ID25 frontend identity matrix

Each row is a separate lookup channel. A match in one row does not establish
the source used by another.

| Subsystem | Input identity | Mapping/source | ID25 outcome | Uses absolute ID? | Uses VehicleRecord? | Uses runtime name? | Confidence |
|---|---|---|---|---|---|---|---|
| Display name | class-local converted to absolute ID25 | Localization groups 0x33 and 0x34, indexed by absolute ID | STEEL MONKEYS FORKLIFT | Yes | No | No | STRONGLY_SUPPORTED |
| Frontend stats | absolute selected ID25 | Four integer fields in record25 at +0x0C..+0x18 | Owner-confirmed bars follow diagnostic [3,4,6,10]; Trooper configuration retained | Yes | Yes | No | RUNTIME_CONFIRMED presentation control |
| Vehicle Select icon | class2 local position and static scene widget | T3_CarN XML widget to carsheet bank index | No T3_Car12 binding; icon absent | Indirectly by static widget order | No | No | PROVEN |
| Race 1P icon | Race participant ID | TimeDiffs/gaHudTimeDiffsAi -> CarID -> record +0x1C -> embedded image selector | Forklift frame 29, owner-confirmed with selector diagnostic | Yes | Yes, field +0x1C | No | RUNTIME_CONFIRMED |
| Progress marker artwork | HUD display slot 0..7 | Generic hud-template frame 3 | Generic marker artwork shared across vehicles | No vehicle-record read in this consumer | No | No | PROVEN |
| Progress marker tint | HUD display slot from `this+0x18` | `FUN_004A74A0` conditionally copies `Race/CarN/Colour` over the widget's loaded tint | Owner reports aquamarine appearance; ID25 SmallCarSheet selector change leaves it unchanged; E0.1d XML/bypass candidates await runtime | No VehicleRecord read in this consumer; upstream writer not traced | No in consumer | No in consumer | Static consumer PROVEN; XML/property precedence, source, numeric values, and semantic owner UNKNOWN |
| HUD progress widget colour config | Per-widget `ProgressCarN` | `Hud0/Hud1.xml` `ObjectColour` loaded by `FUN_004A72A0`; tested one-player RaceTest loaders use Hud0 | Static palette exists; the XML-only and slot-0 bypass tests are prepared but not run | No | No | No | CONFIG INPUT PROVEN; runtime precedence and race-property producer UNKNOWN |
| Race Results icon | Race participant absolute vehicle ID | participant ID -> record +0x1C -> Frontend/RaceResults/CarN -> smallcarsheet index | Forklift frame 29, owner-confirmed with selector diagnostic | Yes | Yes, field +0x1C | No | RUNTIME_CONFIRMED |

## Future profile status

Only fields backed by a demonstrated source are listed as controllable:

| Candidate profile field | Status | Evidence-based scope |
|---|---|---|
| slot_id / class | PROVEN_READ_ONLY | Existing registry and class/local conversion; no E0.1 extension |
| runtime/model/physics/collision family | PROVEN_CONTROLLABLE | E0 initialized the owned Trooper name and combined it with Trooper model, physics and collision sources; outside frontend identity |
| display_name | PROVEN_READ_ONLY | Localization selector is ID-indexed; no profile-driven language override was implemented |
| stats.speed/acceleration/handling/endurance | RUNTIME_CONFIRMED | Original initializer populates fields read by the front end; E0.1b owner test confirms four independently changed bars |
| vehicle_select_icon | ASSET_MISSING | No Trooper-specific art/mapping found; frame 25 exists but its identity and slot binding are unproven |
| race_player_icon | RUNTIME_CONFIRMED | Owner observed frame 29 in the top-left participant icon with the +0x1C diagnostic |
| progress_icon | PROVEN_READ_ONLY | Static generic frame 3 is shared by progress markers |
| progress_marker_colour | UNKNOWN / NOT IN VEHICLE PROFILE | E0.1d still has no writer, source owner, runtime float values, or tested precedence. Do not model as a vehicle field unless vehicle dependence is proven. |
| results_icon | PROVEN_CONTROLLABLE | Record +0x1C drives the numeric smallcarsheet selector for results |

This matrix is a research model, not a schema implementation.
