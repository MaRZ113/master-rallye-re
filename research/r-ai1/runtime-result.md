# Fixed mixed-class runtime result — 2026-10-04

**MIXED-CLASS EXISTING PARTICIPANTS — CONFIRMED_BY_RUNTIME**.
The fresh-profile-v2 experiment passed according to the supplied human report,
supported by the active-race JSON/raw capture. This is the existing four-slot
T1 human + one T3 AI proof, not arbitrary classes/counts/registry expansion.

Candidate SHA `bae5de6aa3ba6cfcd08425c5a00341a3c374ec503b4ba944db6fc2c0d6a77a57`.
Capture `20261004-145347_mixed-race`: NumCars4, NumPlayers1, Type2,
AttractModeFalse, NumNetworkPlayers0, NetworkSyncActiveFalse, Track10.
Audited parser reproduces selected complete block and JSON entries exactly.
Raw SHA `1adf91bf8a695c89361135a58a655b13a2dea1af897f584fe1663d2c00cf316d`;
block SHA `28785595677a58f4441df9d06d642081940b155a1f8adf64cf60ebef66cdf5c7`.

| Slot | ID | Class | Family | Driver | PlayerType |
|---|---:|---:|---|---:|---:|
| Car0 | 0 | 0/T1 | Landcruiser | 30 | 1 |
| Car1 | 14 | 2/T3 | Wildcat | 7 | 2 |
| Car2 | 4 | 0/T1 | Chevyblazer | 1 | 2 |
| Car3 | 1 | 0/T1 | Pajero | 2 | 2 |

Independent Wildcat named values2.77 wheelbase,1.66 front track,3.72 diff ratio
match the protected corpus and runtime Vehicles/Car1 values. The capture is
near race start; it alone does **not** demonstrate movement/finish.

The human reports intended body/model materialization, normal AI driving and
physics, collisions/damage, race progress, Wildcat finish, correct result driver
identity/vehicle icon and normal race completion. These observations establish
the bounded gameplay result separately from the Broker state-only verdict.
Stable frontend return and reset/recovery were not explicitly described in the
supplied report and are not independently upgraded here. The generalized
handoff checks frontend return. Separate unpatched stock control: **PENDING**.

Post-results Dump can crash pristine retail through a NULL StringList payload.
This is a [known stock developer-tool bug](../r-ai1-1/observatory-limitations.md),
not evidence of mixed-class instability. The old mixed-return Dump requirement
is withdrawn. Restart the process before another Dump after Race Results.

The static homogeneity model remains valid. Current work is
[R-AI1.1 generalization](../r-ai1-1/findings.md), with a new randomized candidate
and active-race-only handoff; no capacity phase has begun.
