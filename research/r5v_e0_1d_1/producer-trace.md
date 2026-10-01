# Progress-marker colour producer

## Current classification

**Runtime precedence: established by user report. Exact runtime pointer/writer capture: pending. Static source: traced in R5V-E0.1d.2.** Red XML alone left the marker aquamarine/cyan-like; the ABI-safe bypass produced the normal XML fallback, and the red XML fallback appeared red. See [R5V-E0.1d.2 dataflow](../r5v_e0_1d_2/race-colour-dataflow.md) for the raw static path from VehicleRecord tail through `Race/CarN/Colour`.

| Candidate classification | Status | Evidence needed |
|---|---|---|
| `FIXED_PLAYER1_COLOUR` | Unknown | Writer/source is a fixed Player1-specific value. |
| `PARTICIPANT_INDEX_COLOUR` | Unknown | Writer selects from a participant-indexed palette/table. |
| `PLAYER_PROFILE_COLOUR` | Unknown | Source is a player profile field. |
| `NETWORK_PLAYER_COLOUR` | Unknown | Source is network participant/player state. |
| `VEHICLE_DEPENDENT_COLOUR` | Static path supported; visible ID25 A/B pending | Race setup resolves participant CarID to VehicleRecord tail and emits its four words as `Race/CarN/Colour`. |
| `RACE_SETUP_COLOUR` | Static path confirmed | Race participant setup materializes the property through the shared vector setter. |
| `TEAM_COLOUR` | Unknown | Source is team identity/palette. |
| `OTHER` | Open | Trace to the actual semantic input. |

## Known consumer boundary

`FUN_004A74A0` formats `Race/Car%d/Colour` from HUD display slot `this+0x18`. It fetches the property value and copies four components into its HUD object at `+0x3C..+0x48`. R5V-E0.1d.2 traces upstream race setup from participant CarID to VehicleRecord tail and then into that property. The HUD consumer itself remains display-slot indexed.

No numeric runtime Car0..Car3 values, backing storage lifetime, or exact dynamic write order is known. Static setup call sites and alpha=1 corpus evidence are documented in E0.1d.2. Do not add this tint to `VehicleSlotProfile` until the isolated ID25 red-tail diagnostic confirms its visible effect. No user-facing colour control is implemented. The slot-0 bypass is diagnostic infrastructure only.

## Required closure

If the E0.1d.2 red-tail candidate does not produce the predicted marker change, use the clean baseline and the exact fallback procedure in [R5V-E0.1d.2 MANUAL_X32DBG.txt](../r5v_e0_1d_2/MANUAL_X32DBG.txt). The static producer is already vehicle-record indexed; the remaining dynamic trace is for unexpected runtime behavior, storage identity, or write ordering.
