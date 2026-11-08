# G2 native ownership and ABI

The plan is pinned to the pristine retail image SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. It does not change the EXE on disk. The G2 native plan composes the 17 verified G1/F3 operations unchanged with two non-overlapping operations in the existing pre-constructor in-memory integration.

## Quick Race flow

The existing native getter `FUN_004ADFB0` reads `Frontend/QuickRace/Car0` when called with player index 0. The setter `FUN_004ADF50` writes that same Broker field. The retail x86 bodies establish the conventions: getter is `__stdcall` with `RET 4`; setter accepts `(player_index, physical_car_id)` and is `__stdcall` with `RET 8`.

`FUN_0047AB30` is the Quick Race Vehicle Setup/Vehicle Select constructor. At `0x0047AC50`, retail calls the getter and then publishes its result to `Frontend/VehicleSelect/CarModel`; it also initializes the player-1 model separately. G2 replaces only the player-0 getter call. The 21-byte helper duplicates the original player-index argument, replays the getter, calls the G2 callback with `(current_id, phase=0)`, then returns using `RET 4`, matching the original call frame.

At constructor entry the callback snapshots the accepted config, prepares one stock physical ID, and, for Forced/Random, calls the native setter and verifies it with the getter before returning the selected ID for Vehicle Select publication. Stock and invalid requests preserve the original value. The Quick Race setup owner `FUN_0047B780` reads `Car0` at `0x0047B78A` before publishing `Race/Car0/CarID` and deriving class from the physical VehicleRecord. G2 wraps that same native getter call with phase 1; the callback consumes the cached identity and, when needed, writes and reads back `Frontend/QuickRace/Car0` before native setup continues. Retail still owns Race CarClass derivation, model/resource family, wheels, participant allocation, controller, PlayerType, DriverID, physics, and results.

The helper preserves the getter result in EAX and leaves the original getter's one-argument caller cleanup intact. The callback uses Win32 `WINAPI` with two 32-bit arguments (`RET 8`); the helper removes those arguments through the callee and returns to the original caller with `RET 4`. Both patch sites verify their exact five-byte retail CALL preimages. The generated plan checks operation overlap and preserves every G1 operation byte-for-byte.

## Selection lifetime

Phase 0 prepares a new generation only when the Quick Race Vehicle Select constructor is entered. Ordinary redraws, focus movement, and Start do not call the phase-0 site. Phase 1 and a repeated native setup/Restart consume the existing cached identity; the prepared record is not cleared at first consumption. A later phase-0 entry uses the latest accepted config and can prepare a new choice. A live INI change therefore affects the next entry, not a prepared current choice.

## Navigation boundary still to qualify

The constructor and setup publication sites are proven from the exact retail call flow. The left/right input owner and its write to `Frontend/QuickRace/Car0` / `VehicleSelect/CarModel` are not yet traced. The native Quick Race setter is also used elsewhere, so globally intercepting it would be broader than this phase's evidence supports. Consequently, the test candidate does not add a global setter hook or claim that navigation is locked.

At the entry screen, verify the visible selected name/model and Broker `VehicleSelect/CarModel`; after Start, compare those with `QuickRace/Car0` and `Race/Car0/CarID`. If manual navigation can change the displayed selection while G2 later reasserts a different cached ID, stop the test and report the exact visible ID and Broker values. Do not treat that as a pass. The smallest next research task is to trace the Quick Race Vehicle Select left/right input callback from its scene AI binding to the write that changes the player-0 selected ID, then choose a narrowly scoped native lock or a policy that consistently follows that selected ID.

## Other modes and player 1

The generic initializer `FUN_00480B60` is a separate owner: it reads `Frontend/VehicleSelect/PlayerID` and has mode-specific Master Rallye and Cup/Invitation state paths. G2 does not patch it. Rallye Cup, Master Rallye, Invitation, Challenge, Practice, Checkpoint and SplitScreen player-1 assignments remain native and are not G2 claims. Challenge preview/race synchronization and all F3 mode hooks remain as before.
