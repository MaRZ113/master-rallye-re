# Unlock and progression writers

| Writer | Proven behavior | Limits |
|---|---|---|
| `FUN_0045B5B0` | Common progression award path. Counts class-specific `WinStatus` via `FUN_0045BA50`. At 2/3/4 wins it sets the class CupCar1/CupCar2/CupCar3 flag; above 4 it opens the next class cup and corresponding Master mode. | The writer thresholds and flag indices are statically traced; the full natural campaign route was not runtime-tested in G.1. |
| `FUN_0045BA50` | Counts the five result slots for the current `RaceData/VehicleClass`; this count feeds the award logic. | Counts are evidence for the writer condition, not a complete narrative of race-order/game-mode eligibility. |
| `FUN_00453D10` | Writes one of `T1MasterRallyeCar`, `T2MasterRallyeCar`, `T3MasterRallyeCar` (indices 9..11) from a Master/progression path. | The full threshold/ordering condition was not recovered to a runtime-ready exact recipe. |
| `FUN_00450310` | Reads `Progress/WinStatus` ordinal 104 (`Won_Challenge11`) and writes the `ChallengeCar` flag (index 12) in its challenge-completion path. It also reads a separate completion/sentinel value at ordinal 93 (`Won_Challenge`). | This is a code-path relation, not a claim that every Challenge awards the same vehicle. |
| `FUN_00480B60` | Recomputes `Bonus1` from `FUN_00481FD0` completion scan or the `UnlockCars`/`UnlockAll` cheats. | `Bonus1` is derived/recomputed here; no separate ordinary reward setter was found in the bounded xref set. |
| `FUN_004AFC00` | Resets the `UnlockedCars` group. | Reset behavior only. |
| `FUN_00458090` | Quick Race AI pool builder consults selected `UnlockedCars` flags to append late/special T3 IDs. | AI pool use is mapped for evidence only; no AI behavior changes are part of G.1. |

The generic Broker reader is `FUN_004AFB70(index)` and the indexed setter is
`FUN_004AFAF0(index,value)`. Direct callers of the setter include the
progression award, Vehicle Select's Bonus1 recomputation, reset, Master
progression, and Challenge completion functions listed above. No native setter
for `Bonus2` was found among the audited direct xrefs. Thus ID25 has a known
predicate but its ordinary producer is UNKNOWN in this phase.

For CupCar flags, `FUN_0045B5B0` derives the unlock from persisted win state
rather than storing only a transient menu decision. The exact binary save
encoding remains unknown; the XML marks both win history and unlock flags for
PlayerState persistence.

The statically traced thresholds are:

| Wins for current class | Written `UnlockedCars` flag |
|---:|---|
| 2 or more | `class * 3 + 0` (CupCar1) |
| 3 or more | `class * 3 + 1` (CupCar2) |
| 4 or more | `class * 3 + 2` (CupCar3) |
| more than 4 | open the next cup and the corresponding Master mode |

The observed class-to-next-mode mapping is class 0 → T2 Cup + T1 Master,
class 1 → T3 Cup + T2 Master, and class 2 → Invitation + T3 Master. A separate
numeric mode-selector-5 branch sets the Invitation vehicle flag; the event
name represented by that numeric mode is not asserted here.
