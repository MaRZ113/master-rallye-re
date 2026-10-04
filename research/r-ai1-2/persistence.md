# Native roster lifetime and persistence

| Mode | Classification | What remains native |
|---|---|---|
| QuickRace | NO_PERSISTENCE_NEEDED | Race/CarN remains for current race/Restart; a new 47B780 invocation generates again |
| Challenge | NO_PERSISTENCE_NEEDED | Current fixed-event race state and Restart; new event constructor is the boundary |
| RallyeCup | STOCK_STATE_ALREADY_PERSISTS_RANDOMIZED_ROSTER, in-process cup lifetime | RaceData/CompetitorN identities reused by subsequent stages |
| Invitation | STOCK_STATE_ALREADY_PERSISTS_RANDOMIZED_ROSTER, in-process three-stage event | Shared cup progression owner, event Race IDs36..38 |
| MasterRallye | STOCK_STATE_ALREADY_PERSISTS_RANDOMIZED_ROSTER, static/native-transfer evidence | Native MasterRallye fields and PlayerState save/load; fresh-process human proof pending |

No sidecar is required by the traced identity path; none is implemented.
No original save format is changed. This is not a claim that Cup/Invitation
serialize full rosters across process exit.

## Cup and Invitation

45BE10 invokes 45ABC0 once during new event creation. 45B170 advances the
event RaceID, calls 45B3F0 for scoring/bests and 45BF60 for conditions, then
continues without calling the roster builder. It handles three-stage ranges
10..12,13..15,16..18,19..21,22..24 and Invitation36..38.
44A320/44A710 republish active identities from RaceData/CompetitorN; they do
not reroll. The frontend's new-selection path calls 45AA00 reset and
45AAD0 human setup before creating a new event.

RallyeCup.xml saves six human class-choice fields; frontend.xml saves current
cup/class metadata. They do not declare competitor identity persistence.
Do not infer a disk-resumable Cup roster merely from those metadata fields.
Leaving/resuming distinctions must follow native UI lifetime; a new event
creation rerolls, an existing stage/restart does not.

## Master Rallye

452590 establishes competition class and calls 451DD0 only for NEW competition;
then 452640(0) saves. 452370 advances stages and saves via 452640 without
calling 451DD0. 465F00 Resume invokes 452FE0 and continues if GameSaved is
true; it does not create a new roster.

452640 copies RaceData CarID, CarClass, DriverID, RaceTime, TotalTime,
RacePosition, TotalPosition and human Player flag to MasterRallye/CarN.
It stores Stage/GameSaved and dispatches PlayerState writing through
522D80 -> 5229B0 -> 52D700. MasterRallye.xml declares these identity/progress
entries SavePlayerState=True. The existing serializer preserves typed values.
452FE0 copies identities back to RaceData and restores class, stage,
split-screen and difficulty. There is no class-pool normalization on load.

Native serialization includes stock Car0..5 keys. Those saved tails are
documented as existing serialization, not six active participants; this
phase never creates or tests an active Car5.

New native emulation executes the real 452640/452FE0 control flow with typed
Broker and XML/file boundaries. Identity equality through that transfer is
static evidence. **Actual save -> close process -> fresh process load ->
continue remains a required human runtime gate.**

Config is read only at the first AI of a newly generated roster. Editing it
mid-cup/career leaves the current roster untouched. Next new competition/race
uses the new config. Loading a saved Mixed roster under Stock keeps the saved
IDs, matching native lifecycle; Stock does not convert the save.
