# ID25 frontend identity matrix

Each row is a separate lookup channel. A match in one row does not establish
the source used by another.

| Subsystem | Input identity | Mapping/source | ID25 outcome | Uses absolute ID? | Uses VehicleRecord? | Uses runtime name? | Confidence |
|---|---|---|---|---|---|---|---|
| Display name | class-local converted to absolute ID25 | Localization groups 0x33 and 0x34, indexed by absolute ID | STEEL MONKEYS FORKLIFT | Yes | No | No | STRONGLY_SUPPORTED |
| Frontend stats | absolute selected ID25 | Four integer fields in record25 at +0x0C..+0x18 | Astero-derived [6,6,8,8], supplied by E0 profile | Yes | Yes | No | PROVEN |
| Vehicle Select icon | class2 local position and static scene widget | T3_CarN XML widget to carsheet bank index | No T3_Car12 binding; icon absent | Indirectly by static widget order | No | No | PROVEN |
| Race 1P icon | Possibly race display slot 0 | Exact object/source not matched; ProgressCar0 is only a candidate | Owner reports Astero-like graphic | Unknown | No proven record read | No proven name read | UNKNOWN |
| Progress icon | HUD display slot 0..7 | Hud0/Hud1 ProgressCarN to hud-template index 3 | Generic white-car marker; owner describes it as Astero | No | No | No | PROVEN generic source |
| Race Results icon | Race participant absolute vehicle ID | participant ID -> record +0x1C -> Frontend/RaceResults/CarN -> smallcarsheet index | Index 0; Astero-like frame | Yes | Yes, field +0x1C | No | PROVEN index path |

## Future profile status

Only fields backed by a demonstrated source are listed as controllable:

| Candidate profile field | Status | Evidence-based scope |
|---|---|---|
| slot_id / class | PROVEN_READ_ONLY | Existing registry and class/local conversion; no E0.1 extension |
| runtime/model/physics/collision family | PROVEN_CONTROLLABLE | E0 initialized the owned Trooper name and combined it with Trooper model, physics and collision sources; outside frontend identity |
| display_name | PROVEN_READ_ONLY | Localization selector is ID-indexed; no profile-driven language override was implemented |
| stats.speed/acceleration/handling/endurance | PROVEN_CONTROLLABLE | Original initializer populates record fields read by the front end |
| vehicle_select_icon | ASSET_MISSING | No Trooper-specific art/mapping found; frame 25 exists but its identity and slot binding are unproven |
| race_player_icon | UNKNOWN | Exact in-race 1P object and selector unresolved |
| progress_icon | PROVEN_READ_ONLY | Static generic frame 3 is shared by progress markers |
| results_icon | PROVEN_CONTROLLABLE | Record +0x1C drives the numeric smallcarsheet selector for results |

This matrix is a research model, not a schema implementation.
