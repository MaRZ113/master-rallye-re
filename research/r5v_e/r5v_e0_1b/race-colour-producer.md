# Race progress marker colour producer

## Consumer path

Retail `FUN_004A74A0` (`0x004A74A0`) updates the generic HUD progress marker. Assembly at `0x004A7631..0x004A7644` reads the HUD object field `this+0x18`, formats literal `Race/Car%d/Colour` (`0x006E51A8`), and queries the property. The property getter at `0x004D7340` returns four 32-bit components; instructions at `0x004A7689..0x004A769D` copy them to consumer state `this+0x3C,+0x40,+0x44,+0x48`. The ghost branch writes white RGB and alpha `0.5` (`0x3F000000`). The ordinary path copies these floats to the render object around `0x004A76FA..0x004A770B`.

The storage is therefore a four-component float vector at the consumer boundary. The exact property values written upstream and their alpha convention for ordinary cars are not established by this trace.

## Producer search and result

Bridge string metadata reports one direct code reference to `Race/Car%d/Colour`: the read in `FUN_004A74A0`. The HUD schema function `FUN_004ABCE0` registers `/Colour` alongside HUD properties; it does not contain evidence of the value producer. Inspected `DataScene/RaceTest/*.xml` files define `Race/Car/PlayerType` and `Race/Car/InputType` and contain no matching per-slot colour values. `Hud0.xml`/`Hud1.xml` give `ProgressCar0..7` different `ObjectColour` defaults, but those are HUD fallback/config values, not proof of the runtime race property source.

The owner's earlier runtime observation was “aquamarine” and the marker did not change when ID25's SmallCarSheet selector changed from 0 to 29. This shows independence from that vehicle icon selector only. It does not reveal the underlying float vector or identify the property producer.

| Hypothesis | Status | Evidence |
|---|---|---|
| Fixed Player1 colour | UNKNOWN | No source field or producer traced |
| Participant-index palette | UNKNOWN | Slot-indexed key is consumed, but palette producer not found |
| Vehicle-dependent colour | UNKNOWN | No VehicleRecord read in this HUD consumer; upstream relationship remains untraced |
| Controller/profile/team colour | UNKNOWN | No upstream source traced |

**Classification: UNKNOWN.** The only proven intermediate is a `Race/CarN/Colour` property consumed as four float components. A safe Player1-only input/control point has not been identified, so the requested red marker candidate is not built. Do not add colour to `VehicleSlotProfile` on current evidence.

## Evidence scope

Raw Ghidra Bridge export snapshots for `FUN_004A74A0`, `FUN_004ABCE0`, and related HUD code, plus the exported retail string-reference index, are retained outside Git under `.research-output/r5v_e0_1b/bridge/`. Ghidra assembly/P-code supports the consumer claim; no ReAgent reconstruction was used in this phase.
