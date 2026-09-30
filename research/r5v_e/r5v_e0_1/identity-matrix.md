# ID25 frontend identity matrix

Each row is a separate lookup channel. A match in one row does not establish
the source used by another.

| Subsystem | Input identity | Mapping/source | ID25 outcome | Uses absolute ID? | Uses VehicleRecord? | Uses runtime name? | Confidence |
|---|---|---|---|---|---|---|---|
| Display name | class-local converted to absolute ID25 | Localization groups 0x33 and 0x34, indexed by absolute ID | STEEL MONKEYS FORKLIFT | Yes | No | No | STRONGLY_SUPPORTED |
| Frontend stats | absolute selected ID25 | Four integer fields in record25 at +0x0C..+0x18 | Astero-derived [6,6,8,8], supplied by E0 profile | Yes | Yes | No | PROVEN |
| Vehicle Select icon | class2 local position and static scene widget | T3_CarN XML widget to carsheet bank index | No T3_Car12 binding; icon absent | Indirectly by static widget order | No | No | PROVEN |
| Race 1P icon | Race participant ID | TimeDiffs/gaHudTimeDiffsAi -> CarID -> record +0x1C -> embedded image selector | Forklift frame 29, owner-confirmed with selector diagnostic | Yes | Yes, field +0x1C | No | RUNTIME_CONFIRMED |
| Progress marker artwork/tint | HUD display slot 0..7 | Generic hud-template frame 3; updater consumes Race/CarN/Colour Vector4-like value | Generic marker; ID25 selector diagnostic left its aquamarine appearance unchanged | No vehicle-record read in this consumer | No | No | Artwork and tint consumer PROVEN; upstream color producer/semantics UNKNOWN |
| Race Results icon | Race participant absolute vehicle ID | participant ID -> record +0x1C -> Frontend/RaceResults/CarN -> smallcarsheet index | Forklift frame 29, owner-confirmed with selector diagnostic | Yes | Yes, field +0x1C | No | RUNTIME_CONFIRMED |

## Future profile status

Only fields backed by a demonstrated source are listed as controllable:

| Candidate profile field | Status | Evidence-based scope |
|---|---|---|
| slot_id / class | PROVEN_READ_ONLY | Existing registry and class/local conversion; no E0.1 extension |
| runtime/model/physics/collision family | PROVEN_CONTROLLABLE | E0 initialized the owned Trooper name and combined it with Trooper model, physics and collision sources; outside frontend identity |
| display_name | PROVEN_READ_ONLY | Localization selector is ID-indexed; no profile-driven language override was implemented |
| stats.speed/acceleration/handling/endurance | STATICALLY_PROVEN; RUNTIME_PENDING | Original initializer populates record fields read by the front end; isolated E0.1b stats candidate awaits human bar inspection |
| vehicle_select_icon | ASSET_MISSING | No Trooper-specific art/mapping found; frame 25 exists but its identity and slot binding are unproven |
| race_player_icon | RUNTIME_CONFIRMED | Owner observed frame 29 in the top-left participant icon with the +0x1C diagnostic |
| progress_icon | PROVEN_READ_ONLY | Static generic frame 3 is shared by progress markers |
| progress_marker_colour | UNKNOWN / NOT IN VEHICLE PROFILE | `Race/CarN/Colour` consumer is proven; producer and player/participant/vehicle semantics are unresolved |
| results_icon | PROVEN_CONTROLLABLE | Record +0x1C drives the numeric smallcarsheet selector for results |

This matrix is a research model, not a schema implementation.
