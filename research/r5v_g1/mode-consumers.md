# Mode consumer map

The per-vehicle availability helper has one direct retail code reference, at
`0x004819CE` inside the generic Vehicle Select update path. The table separates
that proven consumer from mode-specific fields and avoids treating “no direct
xref found” as proof that a mode bypasses all validation.

| Mode/context | Class state | Per-vehicle gate | Mode/event identity | Verdict |
|---|---|---|---|---|
| Vehicle Select / Quick Race | Quick Race class list from `FUN_00480B60` | Direct call to `FUN_0045A150` at `0x004819CE` | `Frontend/InQuickRaceMode`, saved `Frontend/QuickRace/Car0` | Both class and car gates are confirmed in this path. |
| Practice | UNKNOWN; a separate Practice class-gate path was not isolated | No separate direct gate xref identified | Exact Practice-to-screen dispatch not isolated here | The generic Vehicle Select call is proven; Practice-specific entry/validation remains UNKNOWN. |
| Rallye Cup | `RallyeCup/VehicleClass` and cup open state | No separate direct call identified | `RallyeCup` stores class-specific player car fields | Event state is separate; additional gate UNKNOWN. |
| Invitation | `OpenedModes/Invitation` and `UnlockedCars/Invitation` exist | No separate direct call identified | Invitation has its own event/player selection state | Flag presence does not prove every consumer; additional gate UNKNOWN. |
| Master Rallye | `MasterRallye/VehicleClass` and class-specific car identity | No separate direct call identified | `MasterRallye` stores `CarID` fields | Master selection/progression is separate; full availability call chain UNKNOWN. |
| Challenge | Challenge access has its own cheat/progression fields | No separate direct call identified | Authored Challenge event records select their own opponent context | Do not infer the generic player gate controls an authored Challenge vehicle. |
| AI / Quick Race opponents | Selected class and a pool assembled in `FUN_00458090` | Pool reads selected reward flags directly for late IDs | AI roster setup invokes the pool builder | Separate AI consumer; map only, unchanged by G.1. |
| Network / multiplayer | Network player selection fields exist | Not audited as a progression consumer | Network mode has separate player/car fields | UNKNOWN; no online test or support claim. |

The existing Quick Race opponent pool conditionally adds T3 IDs 21..24 from
the corresponding unlock flags and does not add ID25 in the traced code. This
is a source-level observation only and is not an AI-pool feature request.
