# R5V-J.2 runtime evidence — 2026-10-09

## Capture integrity and provenance

The supplied `2026-10-09.zip` was read from the Observatory capture folder.
All 19 JSON/raw pairs were checked against the actual archive bytes, including
raw sidecar SHA256 and byte length. No raw captures are copied into this
worktree. The machine-readable report is
[`runtime-evidence-2026-10-09.json`](runtime-evidence-2026-10-09.json).

| Item | Verified value |
|---|---|
| Archive SHA256 | `62b02155b8e4d89bbbdc316541a7f9d96ba030c5511df428008516a7047544b0` |
| Capture pairs | 19 / 19 verified |
| Disk executable | exact pristine retail, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, size 3,121,214 bytes |
| Effective live Dump walker | `native-hardened-null-safe-stubs-v1`, SHA256 `16d85b7cae971b50f0ad1fd33425bae992cc758c0416c856199eb5ea3dfe2fe9` |
| Dump verification | verified in all supplied captures; post-Results safety true |
| Observatory | 0.2.3-beta |

## Confirmed runtime results

**SplitScreen composition — CONFIRMED_BY_RUNTIME.** The supplied
`R5VQ-quickrace-splitscreen` capture contains two human participants at once:
Car0 is physical ID27/T2, `R5VQualifier` model and wheel family, with magenta
record colour; Car1 is physical ID26/T1, `Mercedes` model and wheel family,
with red record colour. This demonstrates independent addon identities in the
same SplitScreen race.

**Rallye Cup roster persistence — CONFIRMED_BY_RUNTIME.** The Cup captures
advance from `RACE 1/3` to `RACE 2/3`. CarIDs, classes, and DriverIDs remain
identical across the stages. ID27 remains an AI at the same slot with native
DriverID 7. No per-stage reroll is inferred or required.

**Master Rallye fresh-process persistence — CONFIRMED_BY_RUNTIME.** The initial
stage-0 race/capture is from PID 42244. The stage-1 capture is from fresh
process PID 41800. The full live and native Master Rallye CarID/DriverID roster
is unchanged, including physical ID27 at the same slot with DriverID 4. The
native Dump variant was verified throughout.

**Original launch without loader — HUMAN_CONFIRMED_UNINSTRUMENTED.** The owner
reports launching the original game without the runtime loader, seeing no
addon vehicles and a normal stock save environment. This is retained as a
human observation only; there is no new instrumented stock-launch capture.

## Vehicle Select re-entry evidence and limit

The after-race reset capture reports `Frontend/QuickRace/Car0=27`,
`CarModel=7`, `selectedCar=7`, and `XValue=0` while `PlayerID=0`. The earlier
valid ID27 Vehicle Select snapshot reports `CarModel=27`, `selectedCar=27`,
`XValue=7`, but it has a different active PlayerID. The stored Quick Race
values retain ID27 (and ID26 for the other player) in both relevant snapshots.
Consequently the snapshots identify a Vehicle Select scene restoration
divergence, but do not prove loss of the stored physical ID or a cross-player
state failure.

The native owner is constructor `FUN_00480B60`, which restores the active
player's stored physical ID through `FUN_00481E50` before the final J.2 XY
publication hook. The first J.2 candidate was **FAILED_BY_HUMAN_RUNTIME**:
Vehicle Select crashed. An emitted-byte ABI audit found two post-
`0x004D0580` object pointers using `[ESP+0x14]` after `RET 4`; the stack-fixed
candidate uses `[ESP+0x18]` for both and was human-tested crash-free. That
stack fix did not close ID27 restoration: ID26 restores, while ID27 still
returns as Navara. A separate exact-bundle audit traced this to the inherited
ID27 reverse-map arm writing T2/local7 into the T1 field at `this+0x14`
instead of T2's `this+0x18`. The new root-cause candidate corrects that one
displacement and remains pending human validation. These findings do not
invalidate the prior J.1/J.2 gameplay captures.

## Evidence boundaries

Broker state proves IDs, classes, DriverIDs, runtime family fields, roster
continuity, and verified Dump fingerprints. It does not by itself prove visual
rendering, successful driving, control independence, or that the new J.2
reverse-map correction works. Existing human gameplay reports and the newly
received captures are preserved separately; no J.2 re-entry runtime pass is
claimed here.
