# Progress-marker colour producer

## Current classification

**UNKNOWN; human debugger trace pending.** The corrected bypass has not yet established runtime precedence, and no runtime colour storage pointer or writer was captured. The known visual report is that red XML alone leaves the marker aquamarine/cyan-like.

| Candidate classification | Status | Evidence needed |
|---|---|---|
| `FIXED_PLAYER1_COLOUR` | Unknown | Writer/source is a fixed Player1-specific value. |
| `PARTICIPANT_INDEX_COLOUR` | Unknown | Writer selects from a participant-indexed palette/table. |
| `PLAYER_PROFILE_COLOUR` | Unknown | Source is a player profile field. |
| `NETWORK_PLAYER_COLOUR` | Unknown | Source is network participant/player state. |
| `VEHICLE_DEPENDENT_COLOUR` | Unknown | Writer consumes vehicle ID, class, or model family. |
| `RACE_SETUP_COLOUR` | Unknown | Source is a race setup descriptor. |
| `TEAM_COLOUR` | Unknown | Source is team identity/palette. |
| `OTHER` | Open | Trace to the actual semantic input. |

## Known consumer boundary

`FUN_004A74A0` formats `Race/Car%d/Colour` from HUD display slot `this+0x18`. It fetches the property value and copies four components into its HUD object at `+0x3C..+0x48`. That consumer path does not read a `VehicleRecord`, vehicle class, or vehicle family. This establishes only that the consumer is not directly vehicle-indexed; it does not prove that upstream setup is vehicle-independent.

No numeric Car0..Car3 values, alpha meaning, storage lifetime, writer, participant mapping, or producer order is known. Do not add this tint to `VehicleSlotProfile`. No user-facing colour control is implemented. The slot-0 bypass is diagnostic infrastructure only.

## Required closure

After the corrected candidate turns the marker red, use the clean baseline at `0x004A7689`, identify the property value buffer, and catch its writer with the procedure in [manual-x32dbg.md](manual-x32dbg.md). Follow the first meaningful write to its semantic source and check whether it uses a vehicle identity. Only then choose a producer-level control.
