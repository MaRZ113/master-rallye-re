# R-CAM1-A3b: RaceLimits lifetime and missing live epoch

**Status: `BLOCKED_ON_LIVE_RACE_OWNERSHIP`. No production race predicate is certified.**
Addresses are exact pristine retail VAs; RVAs subtract `0x00400000`.
The [scope map](../../research/r-cam1-a3/camera-scope-map.json) pins central bytes
and records candidate fields. Static existence, type and registration are not
interchangeable with an active offline Quick Race certificate.

## Verified registration and type

`CONFIRMED_BY_EXE`: RaceStarter initializer `0x0048E2D0` creates an actor,
interns the literal `RaceLimits` at `0x006E42A0` / RVA `0x002E42A0`, calls
rename `0x004F59F0` at `0x0048E6E5`, constructs gaLimitsAI `0x004CD870`
at `0x0048E706`, then attaches slot 0 through `0x004F5950` at `0x0048E717`.
Attachment stores the AI pointer at actor `+4`, then invokes initializer virtual
`+0x14` with the actor argument. AI vtable is `0x0069152C` / RVA `0x0029152C`;
initializer is `0x004CDF00`, update `0x004CD9B0`.

Actor manager global `0x006F96FC` / RVA `0x002F96FC` owns a name registry at
`+0x1C`. Register `0x0050E450` indexes actor `+0x5C` (an interned name ID)
into a four-byte bucket-pointer vector. A bucket contains a vector of actor
pointers; names need not be unique. Rename unregisters via `0x0050E650` before
changing the name, then registers again. Lookup `0x004F5EB0` returns a bucket's
first actor; merely calling it is not a uniqueness/type/lifetime proof.

The AI owns participant count `+0x2C` and seven N-sized arrays at
`+0x20/+0x24/+0x30/+0x34/+0x38/+0x3C/+0x40`. Its initializer requires road
boundary resources and may retire the actor on failure. Update increments
`+0x44` and enumerates participants, but does not itself establish a race phase.

## Retirement precedes destruction

`CONFIRMED_BY_EXE`: `0x004F5840` sets actor byte `+0` bit 2 at `0x004F5849`
and queues actor node `+0x18` for retirement. Registration/allocation can still
exist at that time. Actor update skips bit 2. Manager live priority lists and
pending-admission list are separate from the name registry.

Actor destructor `0x004F5780` unregisters before destroying its AI slots.
gaLimitsAI destructor `0x004CD920` rewrites the derived vtable at `0x004CD926`,
frees all seven arrays, and only then writes base vtable `0x0068F490` at
`0x004CD999`. The freed array pointers are not zeroed in that body.
Readable pointers and the expected derived vtable can therefore coexist during
destruction. A candidate must validate live-list membership, registration
uniqueness, no retirement flag and a consistent owner epoch; never probe arrays
first on the strength of a vtable alone.

## Participant phase is a supporting signal

`CONFIRMED_BY_EXE`: RaceStarter update `0x0048E820` writes
`Race/Car%d/RaceState` (literal `0x006B0F70` / RVA `0x002B0F70`). When its
`+0x10` flag is false, previous startup counter below 10 yields value 1; counter
10 or higher yields 2 (`0x0048E855..0x0048E85D`). The other branch writes 0.
RaceStarter retires after 23 updates. Normal finish policy `0x00489EC0` writes
3 for a finished participant; alternate finish policies are separate.

This explains writes of 0/1/2/3. It does not make value 2 an independent,
current-scene gameplay certificate. No retail `Race/State` global is assumed.
Existing [participant research](../../../../research/r-ai2/participant-pipeline.md)
and [runtime closeout](../../../../research/r-ai2/runtime-closeout.md) establish
ordinary Quick Race configuration/context, not a live Freecam eligibility predicate.

## The concrete missing fact: current successful scene/owner epoch

`CONFIRMED_BY_EXE`:

1. Scene request `0x00522330` stores requested scene ID at manager `+4`
   (`0x005223D0`) and sets countdown `+0x0C=3` (`0x0052241E`).
2. It constructs job vtable `0x00691B10` and queues work through `0x0052D550`
   → `0x005FC950`; this path requests deferred dispatch.
3. Job manager global is `0x006F9D28` / RVA `0x002F9D28`, vtable
   `0x006921A4`. Main update dispatches it at `0x005B008C`, then decrements
   the scene countdown. The countdown is not a load-result flag.
4. Success callback `0x005FCAD0` invokes job virtual `+0x0C` at `0x005FCB1B`
   → `0x0052D620`. That scene job unloads at CALL `0x0052D633`, parses, then
   commits success/default via `0x00522680` at CALL `0x0052D6A4`.
5. **File-open failure** in `0x0054A360` branches at `0x0054A400` to
   `0x0054A45F` → `0x005FCA50`. That moves the job to another list and invokes
   virtual `+4` → error logger `0x0052D5E0`. It returns without running scene
   job unload/commit. Read/write error similarly invokes virtual `+8`.

`STATIC_INFERENCE`: a failed same-scene request can retain the previous committed
scene ID, previous registered RaceLimits and previous participant RaceState.
An empty pending list after error dispatch does not prove successful loading.
No durable successful-load/owner-generation certificate was established by this
audit. List relocation alone is not success: both failure and execute paths
relocate the job. The known native paths distinguish callbacks, but the proposed
read-only predicate has not established a safe persistent distinction.

The exact missing fact is **which side-effect-free state identifies the current
successfully initialized live race owner after request, completion or failure,
including a same-course restart**. Until established, the production gate stays
absent rather than accepting stale state. Frontend, preview, loading, teardown,
replay, attract, network, split-screen and unknown builds remain unauthorized.

## Bounded reads required for the eventual predicate

Use guarded reads of existing string-pool records, not side-effecting native
getters. Pool global `0x006F93D4`, its ID vector `+4`, and record text pointer
`+8` resolve already-present names. Broker manager `0x006F9410` has 0x1C-byte
entries: path ID `+0`, payload pointer `+4`, tag `+8`; Boolean tag 0 and integer
tag 2 payload layouts are established by native setters. Getters may intern or
grow vectors and must not be called by this observation.

Required context includes the committed France1 owner, Type2, one human, zero
network players, FinishingType0, and explicit replay/attract/network/ghost
exclusions. Missing, malformed or incorrectly typed entries reject. Do not guess
interned IDs or derive France1 from an unaudited TrackID number.
`CONFIRMED_BY_EXE`: `BeenInRace` is set true early in RaceStarter initialization
at `0x0048E30E` / RVA `0x0008E30E`, before RaceLimits creation. Scene request
clears it at `0x005223B8` / RVA `0x001223B8` only on one branch: a nonzero
result from probe `0x005D1660` skips that read/clear block. Thus it is not an
established all-request invalidation or successful-load readiness certificate.

The smallest next verification is specified in the [handoff](runtime-test-plan.md):
observe the request/commit/error distinction and owner membership as one bounded
restart sequence. Existing camera-only F10 logs cannot establish this relation.
