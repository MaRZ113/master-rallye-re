# Randomize the human player's vehicle

## Native identity flow

In Quick Race, `FUN_0047B780` reads the selected player's absolute physical
vehicle ID through `FUN_004ADFB0(0)` before it calls the AI chooser. It writes
that ID to `Race/Car0/CarID`, reads the selected physical record's class from
the VehicleRecord table at record stride `0x34`, then publishes
`Race/Car0/CarClass`. The later materializer derives CarType, WheelType,
physics family, assets and colour from the physical registry record. `DriverID`
and `PlayerType` are separate identity axes.

The Vehicle SDK's read-only J.2 analysis identifies `FUN_00480B60` as the
Vehicle Select initialization owner. It reads the active `PlayerID`, restores
that player's physical selection through `FUN_004ADFB0`, and resolves the
physical ID back to class/local ordinal before the scene publishes its
highlight. Frontend name/model writers are independent from Race/CarN identity;
setting one Broker field alone would produce a misleading preview.

Challenge already has a useful lifecycle precedent. Its screen prepares one
absolute opponent ID and publishes that same prepared identity to the preview;
Start consumes the cache instead of rerolling. Back/event change invalidates
the cache, Retry reuses the current race. That pattern is suitable evidence for
a **prepared player selection**, but it is not itself a general player-car
implementation.

## Recommended contract

Choose a human physical CarID once at an explicit event/lobby boundary, save
it as a prepared selection keyed by player, mode and event/competition
identity, then use that exact ID both in presentation and native participant
construction. Never draw a second ID when Start is pressed. Retry reuses it.
The player remains Car0 / PlayerType=human; no controller, DriverID or player
ownership field is randomized.

Recommended first slice is **Quick Race, same-class only**:

1. Enter the existing player selection/lobby initialization path.
2. Resolve and validate one available/materializable physical ID under the
   configured Player policy.
3. Publish the same physical ID through the native Vehicle Select/Quick Race
   identity writers, class/local reverse mapping, preview model and text.
4. At `0x0047B780`, make `FUN_004ADFB0(0)` return/use the already prepared ID
   before Car0 CarID and derived CarClass publication.
5. Freeze through race, restart and current session; replace only at the next
   new Quick Race boundary.

Before broadening to cross-class choices, prove what class controls the Quick
Race rules title and Stock AI pool. The current AI class policy reads the
player's class as its native input; a randomized player car must not silently
rewrite a separately configured AI policy.

## Modes and persistence

Per-mode Player policies are preferable to one global switch. In Cup and
Master Rallye, a cross-class forced/random vehicle can conflict with the
selected competition class even though the physical car materializes. A new
Cup/new Master competition may prepare a player ID once, but a current roster
and saved Master Rallye must stay immutable across stages and Resume. Invitation
uses its special T3 event rules. Challenge must keep authored event semantics
and preview/race identity coherent, using a key that includes the selected
event and authored player identity.

Do not change `MasterRallye/CarN`, `RaceData/CompetitorN` or an active
`Race/CarN` because the INI changed mid-event. A config edit applies at the
next supported preparation boundary.

## Failure behavior and proof plan

Reject an unknown physical ID, inactive/unregistered addon, unavailable
resource family, invalid class mapping or mode-incompatible choice before
publishing preview state. Emit a clear configuration diagnostic and let the
native mode follow its ordinary path; do not show one car and enter another.

Minimum PoC: deterministic fixed same-class player ID in Quick Race; verify
Vehicle Select class/local ordinal and name/model, preview, Broker Car0
CarID/CarClass/CarType/WheelType, one normal race, Retry, and a return/new
selection. Then test one T1/T2/T3 stock ID in each mode whose native rules
permit it. Challenge requires a separate authored-event preview/race pair.

**Status:** feasible with localized patches. Confidence is high for the Quick
Race read/write seam and medium for a general multi-mode policy. Cross-class
campaign semantics and exact frontend confirm/commit ordering need targeted
verification. No player-randomization code was added.
