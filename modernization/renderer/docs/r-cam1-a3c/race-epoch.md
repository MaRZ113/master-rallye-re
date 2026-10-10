# R-CAM1-A3c: observed scene generations

Status: **BLOCKED_ON_RACE_EPOCH_CORRELATION**. This is an implemented read-only
lifecycle observer, not a Freecam candidate. `authorizes_camera_writes()` always
returns false. `correlated_owner_candidate` is a diagnostic supporting signal;
it is not a certificate.

The pristine image was reverified: SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
3,121,214 bytes, ImageBase `0x00400000`. All RVAs below subtract that ImageBase.
Unknown executables keep native forwarding and existing feature-local policies,
but receive no new lifecycle hooks or game-storage reads.

`CONFIRMED_BY_EXE`: the observer sees an actual request at CALL
`0x005223D3` / RVA `0x001223D3`, immediately after the store at `0x005223D0`.
This avoids treating the early return of request function `0x00522330` as a new
load. ESI is the scene manager; EDI points to the requested interned ID. Both
are checked against guarded native storage. Every observed store advances a
64-bit generation and revokes the previous success, including same-scene restarts.

At `0x00522455` / RVA `0x00122455`, the coordinator binds the scene job to that
request before the original queue operation. The job's class, source ID and two
byte flags are recorded; callback entry checks them again. Scene/source text is
copied into fixed buffers at enqueue so old events do not depend on later ID
resolution. There are 64 job entries and 128 recent transitions. History survives
F10 and Reset; normal ring overwrite is counted. Counter overflow, job capacity,
wrong threads, nesting, missing hooks and impossible orders revoke or quarantine.

`CONFIRMED_BY_SOURCE`: callback entry is `EXECUTING`, never success. The commit
observer calls `0x00522680` once and reads the result **after it returns**.
The native Boolean must be nonzero and the committed ID must equal the queued
scene ID. Only the later return of `0x0052D620` can record successful completion.
Default/fallback, missing commit, file-open error `0x0052D5E0`, and read/decode
error `0x0052D600` leave success revoked. Pending-list relocation has no success
transition. An old/duplicate/unknown callback cannot reactivate an epoch.

Job addresses are not generations. A terminal address reused at enqueue obtains
a new observer serial, is explicitly marked reused, and remains unqualified.
A nonterminal address reused, or a missing event, quarantines the observer. This
conservative policy needs native destruction/lifetime proof before relaxation.

Each RaceLimits attachment at `0x0048E717` / RVA `0x0008E717` gets a new owner
serial. The native initializer must return before initialization is recorded.
Construction inside the current executing job records that job's lifetime.
Construction after its return records **zero** execution-job lifetime: no guessed
association based on proximity, Source90, RaceState2, or the unchanged course.
The later transfer at `0x004F6202` / RVA `0x000F6202` supplies live admission.
Old-owner retirement during a new job's unload is recorded without incorrectly
failing that new job. Current-owner retirement/destruction immediately revokes.

Before probing participant arrays, the reader requires a current observed owner
generation/lifetime, unique RaceLimits registration, exactly one reciprocal
live-list membership, no pending membership, clear retirement flag, matching
slot-0 AI pointer and vtable. It bounds N to 1..8 and reads all seven N*4 arrays
and required boundary resources. Participant RaceState2 and the typed offline
context are supporting signals only. Reset revokes and requires a newly observed
lifecycle; release disables observation and removes owned hooks when safe.

The exact remaining relationship is whether France1 RaceStarter initialization
`0x0048E2D0` creates/attaches RaceLimits **within** the corresponding execution
`0x0052D620`, or during a subsequent native actor update. A3b did not establish
this ordering. If it is a later update, a verified link from that new owner to the
completed job is still needed; its pointer and current request number cannot
substitute for that link. Current France1 resource identity also needs reconciling
with captured native scene/source names; no numeric TrackID is assumed. The
[single restart capture](runtime-test-plan.md) records both sides of this question.

## String-pool correction retained separately from A3b

A3b's read-policy paragraph says “record text pointer +8”. The audited allocator
indeed stores text at header+8, but this is **not** the pointer stored in the ID
vector. `0x004D45C2` forms header+8, `0x004D45CB` pushes that text address, and
`0x004D4D00` appends the caller's pointer. `0x004D4CD0` returns the vector item
unchanged. Therefore the reader dereferences the ID-vector item directly as NUL
text. Adding eight again would skip the first eight characters. The new
[bounded excerpts](../../research/r-cam1-a3c/lifecycle-excerpts.json) and native
reader tests cover this correction; historical A3b notes are unchanged.

Broker reads resolve existing text IDs and validate vector bounds, entry ID,
tag 0/2 and payload. They never call native intern/getter routines. All nine
context paths are exact retail literals: Type, NumPlayers, NumNetworkPlayers,
NetworkSyncActive, AttractMode, GhostPlayback, PlaybackReplay, FinishingType,
NumCars under `Race/`. Missing entries or wrong tags reject supporting context.

No actual game run with this observer has occurred. Source inspection and native
fixtures do not establish the successful runtime ordering or a Freecam certificate.
