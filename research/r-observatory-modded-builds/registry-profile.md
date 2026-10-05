# Build-specific registry oracle

Exact executable profile -> committed registry profile -> ID/class/local/family.
The canonical stock map in research/r-ai1/vehicle-class-map.json is reused,
with its pristine source identity checked; no duplicate parser or stock table.
[registry-profile.json](registry-profile.json) holds only build-specific additions.
Pristine excludes25/26; merc-id26 adds25 and26 without replacing neighboring IDs.
Future deliberate entries can add another class/local/family without changing
the generic mapping/checker logic. Nothing is automatically registered.

`vehicle(profile, id)` and `absolute_id(profile, class, local)` are strict build
oracles. The focused `check-vehicle` command validates exact capture profile,
hash/size/freshness, all four active participant ID/class/type/driver/families,
target identity and Vehicles/Physics state. Raw sidecar and selected native Dump
are verified before the oracle is called. Only known active-race labels are
accepted, and this handoff is exactly one human +three AI, not capacity research.

Verdict is **BROKER_STATE_MATCH_ONLY**, runtime_full_pass=false. Visibility,
independent physics/collision and successful race lifetime need human evidence.
No Mercedes physics constants are invented. Existing R-AI proof checkers retain
their own exact research candidate gates; they are not made into unknown-build
randomizer checkers. Use this focused build-aware checker for Mercedes.
