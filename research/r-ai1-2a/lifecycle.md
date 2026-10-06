# One Challenge generation and its lifetime

| Point | Exact owner / behavior |
|---|---|
| Enter screen | Vtable690434 ->45E4F0 initializes selection/unlocks; bridge at45E511 clears prior transient selection |
| Details | Initialization45EA40 or arrow45EAFF invokes45EB30;45EC35 reads authored AI then calls DLL prepare |
| Generate | MRChallengeV1(1,100+event,human,authoredAI), exact record/context validation; load current INI once, existing Cycle and stock eligible pool |
| Redraw/refresh | Same event/human/authored key returns cached result; model mover44C4C0 never calls generator |
| Change event | 45EAC3..45EAFC updates instance+10; next prepare invalidates old key and generates once |
| Start | 45EAAF calls44FEC0 before requesting screen10;45010E bridge calls MRChallengeV1(1,1,1,1), consumes cache with event RaceID-25 and exact authored human |
| Loading / publication | Original CarID setter, registry CarClass, DriverID, NumCars2/NumPlayers1 setup remain native |
| Retry | RaceRetry vtable690A74 ->47E020, choice1 ->45D910(10); no44FEC0 or generator call, current Race/CarN reused |
| Back in Challenge | 45EA9A requests screen2 through reset bridge; clears cache before original transition |

The cache contains event/human/authored/chosen ID, policy and generation serial;
no persistent file state. Entry and Back explicitly clear it. A different
identity key invalidates it. Completing an attempt may retain dormant process
cache memory while native Race state is used by Retry; returning to a newly
initialized Challenge screen clears it before any new details or Start. No
consumer in another mode uses this cache. OS process exit also discards it.

Config reload: a prepared Stock/Mixed/Diverse selection stays authoritative even
if its INI changes. Same-screen redraw and Start never read INI again. Back/reenter
or a different event starts a new generation using the current file. Original
Stock->Mixed changes likewise wait for a new selection boundary.

Stock invokes pass-through diagnostics once without class or vehicle RNG;
native driver RNG at Start remains stock-exact. Mixed uses the existing class
and vehicle draw algorithms. Diverse uses the existing eligible-class shuffle
and vehicle draw, not a new probability policy. Exactly ONE generation group
does not mean exactly one individual RNG call (Diverse shuffles classes).

Start with no matching prepared record, unknown event, invalid record, unsupported
split/network context or unknown EXE fails Stock and does not late-randomize.
Eligibility is resolved at prepare against the authored human, never stale
Race/Car0 from an earlier race. Invalid record/context at a recognized prepare
boundary clears selection. Out-of-range event commands fail Stock; retained
cache memory cannot be consumed by a different event or invalid context.
