# Challenge Clone Army feasibility — research only

## Current stock owner

The exact retail exports identify `FUN_0044FEC0` as the Challenge race
constructor. It reads an authored human/opponent vehicle pair from the
Challenge event table and builds the stock event participants. Its current
path supports the authored human plus one opponent, with an additional human
participant in the split-screen branch. The bounded implementation has no
seven-AI participant loop.

The Challenge frontend renderer `FUN_0045EB30` publishes the authored
opponent presentation through the existing Challenge identity fields, including
`Frontend/Challenge/Car2Text` and the opponent preview model. F3 maintains a
prepared physical opponent identity so preview and race consume the same
choice. G1 does not modify that cache or any Challenge operation.

## Feasibility result

Neither requested clone-army variant is currently safe to implement from the
available evidence. Repeating a CarID is not enough to create seven native
participant records. Event completion predicates, attempt/restart behavior,
progression, Results, replay, and per-participant DriverID/controller
ownership have not been traced for a seven-opponent Challenge. The existing
constructor and preview expose a one-opponent authored model, and no runtime
proof shows that the event rules accept a larger roster.

Variant A (clone the authored opponent) is the narrower future experiment.
Variant B (choose one random shared model) would additionally need a prepared
selection state that feeds the exact same physical ID to preview and race.
Neither is included in G1.

## Smallest future proof of concept

After Quick Race duplicate behavior is qualified, use a disposable,
non-progressing test event and a single authored opponent. First trace every
Challenge read/write for participant count, event completion, restart, Results,
and progression. Then test a two-AI clone while preserving separate CarN,
controller, and DriverID state and verifying preview identity. Only after
that end-to-end control passes should the experiment increase the opponent
count. The owner remains responsible for course start placement and RaceLine
clearance; this research makes no terrain or spawn-safety claim.

