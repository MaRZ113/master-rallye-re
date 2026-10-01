# Progress marker colour producer classification

## Classification

**UNKNOWN.** The game visibly displayed an aquamarine/cyan-like Player1 progress marker in the prior owner test, but no numeric runtime value or upstream writer was captured. The consumer maps a HUD display slot into `Race/CarN/Colour`; the relationship between that slot and a player/profile/palette is not enough to identify ownership.

| Candidate class | Status | Evidence |
|---|---|---|
| `FIXED_PLAYER1_COLOUR` | Unknown | No Player1-owned value source found. |
| `PARTICIPANT_INDEX_COLOUR` | Plausible, unproven | Consumer formats the property by display slot; no producer/table or runtime slot values captured. |
| `PLAYER_PROFILE_COLOUR` | Unknown | No profile field traced to the property. |
| `NETWORK_PLAYER_COLOUR` | Unknown | No network player field traced to the property. |
| `VEHICLE_DEPENDENT_COLOUR` | Unknown | Consumer does not read a VehicleRecord, but upstream dependence was not traced. |
| `RACE_SETUP_COLOUR` | Unknown | No value writer or source object recovered. |
| `TEAM_COLOUR` | Unknown | No team source found. |
| `OTHER` | Open | Generic schema/struct materialization remains possible. |

## Vehicle profile ownership

Do not add marker tint to `VehicleSlotProfile`. The consumer does not read vehicle ID, class, runtime family, or `VehicleRecord` while loading the colour. No upstream evidence proves vehicle dependence. Keep the semantic model unset until dynamic tracing identifies whether it belongs to a participant, player HUD profile, race palette, or another owner.

## User-facing control

No clean semantic control is ready. The slot-0 bypass candidate is a diagnostic only; it hides the property-exists result for one HUD display slot and does not add a supported colour setting. A semantic red control can be designed after the property producer and source owner are known.

## Remaining edge

```text
race participant setup / schema table / profile or palette source
    -> exact writer and backing storage
    -> Race/Car0/Colour
    -> FUN_004A74A0 tint
```

The storage address, lifetime, writer, source object, slot/index rule, Car0..Car3 values, and overwrite timing remain unobserved.
