# Progress relationship

Retail corpus Progress.xml contains 184 Values. WinStatus and UnlockedCars path
families carry SavePlayerState=True; seven cheat-state Values do not. Game.xml
requests Progress as a dependency. This is `CONFIRMED_BY_CORPUS`, independently
anchored to loader provenance assignment and mode-3 filtering.

The supplied frontend/race snapshots show unlock-related keys with SaveFile
PlayerState and Game/PlayerState enabled, while the remaining Progress group has
seven GLOBAL cheat Bool rows. This is existing `CONFIRMED_BY_RUNTIME` evidence
consistent with later profile load overriding the defaults in the same Broker.
It is not proof of a second dedicated profile database or fixed bitset.

Normal progress callers reach `005229B0(PlayerState, 3)` (including `004841B0`
and championship/progress-related callers `004501D0/00450310`). The actual save
population is every eligible PlayerState entry, not just one Progress subtree.

Vehicle-slot implication: registry capacity, frontend enumeration, unlock keys
and persistence selection are separate constraints. Extra slots would need
matching identity/unlock conventions and their runtime consumers; counting
Unlock paths does not prove a new executable slot is supported. No expansion,
unlock patch or profile editor was started here.

Unresolved: every championship completion/reset producer, all course-unlock
consumer limits and profile identity switching behavior. These are future
targeted questions, not claims made from XML names alone.
