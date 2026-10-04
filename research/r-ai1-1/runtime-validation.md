# Generalized existing participants — human runtime result

2026-10-04: **GENERALIZED PLAYER-INDEPENDENT MIXED-CLASS EXISTING PARTICIPANTS
CONFIRMED_BY_RUNTIME**. This records one full race, not repeated RNG variation.
The tested image was the original R-AI1.1 MIXED candidate, SHA256
`f9e8e556842602252ec39b2174e796f6cb67651d8f573f2565f9d2e5569bd9ac`.

## Raw-bound active state

Capture label `mixed-random-race-1`, timestamp `20261004-163242`; source size
3,121,214, module base `0x400000`, sink vtable `0x69CEA8`, freshness
`post_baseline_complete_dump_proven`. The pinned Observatory parser reproduced
the JSON entries and selected block from the raw sidecar. Raw SHA256
`f36a80ab256e5acdfb0859c5e4594152e5e6125331a9c4a9fd4a40631c3f79a3`;
selected block SHA256
`4d9a599d3c7692494fa29b39552c15a60c929210d37b5406d13f54ec2f3952f6`.
The offline oracle returns **BROKER_STATE_MATCH_ONLY**.

NumCars4, NumPlayers1, Type2, AttractMode=False; normal offline Quick Race.

| Slot | ID | Class | Family | PlayerType | DriverID |
|---|---:|---|---|---:|---:|
| Car0 | 0 | 0 / T1 | Landcruiser / TOMMEK DIRTBEAST | 1 human | 30 |
| Car1 | 15 | 2 / T3 | Simmbugghini | 2 AI | 3 |
| Car2 | 17 | 2 / T3 | Kangoo | 2 AI | 0 |
| Car3 | 7 | 1 / T2 | Navara | 2 AI | 1 |

CarType/WheelType and the three previously established named-physics canaries
match the corresponding stock family for every slot. Path presence alone is
not actor proof. Captures remain ignored; only this evidence summary is tracked.

## Human observations

The user reports all three AI drove normally; physics, contacts, damage and
collisions behaved normally. The full race finished. Race Results showed normal
driver identities and correct vehicle icons, with stable frontend lifecycle.
These observations supply the actor/lifecycle evidence that the Broker checker
cannot establish. Fixed R-AI1 remains separately runtime-confirmed.

At this first-race checkpoint, repeated variation and hardening were untested.
They subsequently passed [final runtime closeout](runtime-closeout.md): four
fresh generations and one Restart reuse capture in one hardened process.
This earlier race alone does not show variation or validate hardening.
R-AI1.1 is now **CLOSED / CONFIRMED_BY_RUNTIME**; uniformity remains unproven.
