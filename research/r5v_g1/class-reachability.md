# Quick Race class reachability

## Owner and rules

`FUN_00480B60` initializes the Vehicle Select class list and `LockClass` state.
When `Frontend/InQuickRaceMode` is true, T1 is included. The relevant
progression checks are:

| Condition | Quick Race classes exposed |
|---|---|
| `OpenedModes/T3Cup=True` | T1, T2, T3 |
| else `Cheats/UnlockCups=True` or `Cheats/UnlockAll=True` | T1, T2, T3 |
| else `OpenedModes/T2Cup=True` | T1, T2 |
| otherwise | T1 |

This matches the reported fresh-profile observation: only T1 is reachable,
although early T3 IDs such as ID14 have no individual progress predicate.
Therefore “ID14 is not individually locked” never implied “T3 is selectable on
a fresh profile.”

The class arrow handler in `FUN_00481EB0` checks `LockClass` and moves within
the `VehicleList` length. It controls navigation bounds; it is not the source
of campaign unlock state. In non-Quick-Race paths, the screen locks class
navigation and reads class-specific state from `MasterRallye/VehicleClass` or
`RaceData/VehicleClass` according to mode. Those paths are not interchangeable
with Quick Race's open-class list.

## Persistence and unlock source

`Progress/OpenedModes/T2Cup` and `T3Cup` are Bool fields, default false, with
`SavePlayerState=True` in retail `Progress.xml`. The native progression award
path can set these fields after a class cup meets its completion condition.
Cheat fields `UnlockCups` and `UnlockAll` default false and have
`SavePlayerState=False`.

The schema establishes native state and save eligibility. It does not reveal
the on-disk PlayerState encoding. See [`progress-state.md`](progress-state.md)
for that boundary.
