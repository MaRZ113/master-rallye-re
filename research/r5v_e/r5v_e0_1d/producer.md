# Progress marker colour producer classification

## Classification

The E0.1d investigation originally stopped without identifying a writer. Follow-up [R5V-E0.1d.2](../../r5v_e0_1d_2/race-colour-dataflow.md) statically identifies the upstream source: race participant setup resolves CarID, reads `VehicleRecord[CarID]+0x24..+0x30`, and writes it to `Race/CarN/Colour`. The ABI-safe bypass report confirms the property override/fallback precedence. The isolated ID25 red-tail visual A/B and debugger storage capture remain pending.

| Candidate class | Status | Evidence |
|---|---|---|
| `FIXED_PLAYER1_COLOUR` | Unknown | No Player1-owned value source found. |
| `PARTICIPANT_INDEX_COLOUR` | Plausible, unproven | Consumer formats the property by display slot; no producer/table or runtime slot values captured. |
| `PLAYER_PROFILE_COLOUR` | Unknown | No profile field traced to the property. |
| `NETWORK_PLAYER_COLOUR` | Unknown | No network player field traced to the property. |
| `VEHICLE_DEPENDENT_COLOUR` | Static path supported; ID25 red-tail A/B pending | Setup resolves CarID to VehicleRecord tail and sends its four words to `/Colour`. |
| `RACE_SETUP_COLOUR` | Static path confirmed | Participant setup writes `Race/CarN/Colour` through `FUN_004ACDD0`. |
| `TEAM_COLOUR` | Unknown | No team source found. |
| `OTHER` | Open | Generic schema/struct materialization remains possible. |

## Vehicle profile ownership

Do not add marker tint to `VehicleSlotProfile` yet. The static producer reads a VehicleRecord tail selected by participant CarID, but the isolated ID25 red-tail A/B has not run. Keep the profile model unchanged until that runtime comparison confirms the visible effect.

## User-facing control

No clean semantic control is ready. The slot-0 bypass candidate is a diagnostic only; it hides the property-exists result for one HUD display slot and does not add a supported colour setting. A semantic red control can be designed after the property producer and source owner are known.

## Remaining edge

```text
race participant setup / schema table / profile or palette source
    -> exact writer and backing storage
    -> Race/Car0/Colour
    -> FUN_004A74A0 tint
```

Static writer and source are now known. Runtime backing-storage address/lifetime, Car0..Car3 numeric values, and overwrite timing remain unobserved; the ID25 red-tail candidate is prepared under `research-output/r5v_e0_1d_2/runtime-test/`.
