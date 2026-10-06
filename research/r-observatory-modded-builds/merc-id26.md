# Mercedes / neighboring registry evidence

CONFIRMED_BY_EXE, exact supplied image only:

| ID | Class | Local | Family / expected CarType / WheelType |
|---:|---|---:|---|
| 24 | T3/2 | 10 | existing stock (canonical map unchanged) |
| 25 | T3/2 | 11 | Trooper |
| 26 | T1/0 | 7 | Mercedes |

Native68E2A0 calls the original full record initializer45A0B0 twice, record
offsets518/54C, IDs25/26, classes2/0, family string arguments at68E4D8/68E4E0.
ID26 is a distinct initialized record, not an alias to ID0. Display literals
MERCEDES, ML-320 and MERCEDES ML-320 also exist in the extension. Native
481E20 ->68E340 special-cases T1/local7 ->26; 481E50 ->68E370 special-cases
ID26 ->T1/local7. Native bounded emulation exercises all27 round trips and
captures both initializer calls. enString/Broker/secondary scene construction
are explicit boundaries, not real gameplay.

Unchanged44A510 reads registry family at owner+24+ID*34 and publishes the same
family to native4ACA40/4ACB40 (CarType/WheelType). Thus Mercedes is the exact
static expected family, with materialized runtime strings still pending capture.
No model/physics/collision/availability/runtime proof is inferred from the name.

Pristine physical record25 is trailing default/uninitialized; only its named
IDs0..24 are accepted by the pristine oracle. Mercedes valid registry is0..26.
No ID shift, future extra vehicle ID assignment or new import occurs here.

Eight physical T1 records0..6 plus26 can support one T1 human and seven unique
T1 AI **when all eight are actually eligible/available**. This is future pool
context, not a randomizer change or runtime eight-T1 proof. An extra future T2
record could similarly enlarge its pool, but no ID is selected. Fresh-profile
T3 availability/reward eligibility and overflow policy remain separate UNKNOWNs.
