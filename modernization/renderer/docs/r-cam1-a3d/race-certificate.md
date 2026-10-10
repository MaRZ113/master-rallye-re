# Current race certificate

The observation state machine does not itself authorize writes. Production
`live_race_certificate()` rereads three independent layers on the renderer thread:

1. **Storage:** unique `RaceLimits` registration, actor name, retirement bit,
   exact actor AI slot and retail AI vtable; guarded read-only memory access.
2. **Native liveness:** actor's embedded node is present exactly once in the seven
   live lists and absent from pending. Arrays/resources are read only after this
   proof. Requested scene generation is not an early rejection condition.
3. **Temporal permission:** current owner attachment lifetime, initialized state,
   successful native root/HUD job completion, explicit parent edge, current race
   lifecycle and no revocation fence or permanent integrity failure.

Then all nine typed Broker values must exist: Type, NumPlayers, NumNetworkPlayers,
NetworkSyncActive, AttractMode, GhostPlayback, PlaybackReplay, FinishingType and
NumCars. No native getters/interners are called. Cached key IDs are validated
against current pool text; native object addresses are never cached by the reader.
Exactly one human, no network/replay/ghost/attract, FinishingType 0, bounded matching
participant arrays and each participant RaceState 2 are required.

`CONFIRMED_BY_EXE`: QuickRace producer VA `0x0047B780` / RVA `0x0007B780`
reads `Frontend/QuickRace/Mode` and writes Race/Type (setter `0x004AC1C0`,
property `+0x10`, key `Race/Type` at `0x004ABCE8`). The branch at
VA `0x0047B8F0` / RVA `0x0007B8F0` explicitly recognizes mode 1 and bypasses
the AI chooser; other modes take that path. Thus Type 1 is not inherently Attract.
The current certificate accepts Type 1 **only with one total car**, Type 2 with
1..8 actual ready participants. Attract remains an independent mandatory false
boolean. Earlier mode-map examples were not an exhaustive enumeration.

Course admission requires the owner-creating job's copied scene
`RaceTest/France1` and source `DataScene/RaceTest/France1.xml`, flags 1/0.
The resource is identified in existing `research/general-re/grid8/canonical-courses.md`;
the native request builder at `0x00522330` constructs `DataScene/` plus scene plus
`.xml`. Numeric 9269 in the poisoned capture is **not** promoted to a proven source
name: its queue payload was lost. Actual current queue text must prove the source.
This relationship remains an explicit first-flight observation, not a reason to
accept other scene names speculatively.

Finally the sole camera at manager `0x006F94DC` / RVA `0x002F94DC` must equal the
renderer holder `0x006F9CF0` / RVA `0x002F9CF0` selected frame. Exact pristine SHA,
ImageBase `0x00400000`, current thread, one shared hook/device and intact patches
are mandatory. A readable camera, source90, RaceState2 or final Hud/Hud0 alone
cannot certify a race. Unknown EXEs can retain compatible existing renderer
features, but Freecam stays OFF.

Tests call the production certificate predicate and reader, including Type1 one-car,
Type2 bounded counts, missing/wrong typed fields, malformed registry/lists, stale
generation/owner, failed child, same-course restart, Reset and destruction negatives.
Synthetic positive certificates are not a claim that the new DLL has flown in-game.
