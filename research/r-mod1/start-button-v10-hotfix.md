# R-MOD1-D v10 — Start gate and roster observation

> Historical implementation record only. V10 later failed human runtime
> during race loading because the observer wrapped a `RET 4` Broker getter and
> corrupted its argument stack. V11 removes that hook; see
> [`v11-observer-hotfix.md`](v11-observer-hotfix.md).

## v9 failure and corrected behavior

The v9 candidate reached the game and installed its complete bundle, but
Start logged `ROSTER DENIED reason=race-numcars-or-numplayers-out-of-bounds`
for requested four AI / expected five cars. The old `MRValidatePrepared...`
path treated an immediate post-`FUN_0047B780` Broker read as authoritative and
returned through the parent callback epilogue instead of reaching the stock
frontend transition. This explains the inert Start button; it does not prove
that the native participant pipeline cannot create five cars.

The old summary printed `counts.snapshot.num_cars/num_players`. When the raw
values failed validation, `analyze_native_roster()` returned its default
snapshot, so those printed zeros were not necessarily the raw native getter
results. v10 keeps `native_num_cars` and `native_num_players` separately and
logs them directly. The v9 `actual=0` line therefore cannot by itself tell
whether the getters returned zero, a count was pending, or the observer used
an incorrect context.

## Native publication and read sequence

Exact-retail function evidence:

| Address | Evidence |
|---:|---|
| `0x0047B780` | Quick Race setup reads the selected opponent count, adds one, and calls `0x004AC3D0` to publish `Race/NumCars`; it then performs native player/AI roster selection. |
| `0x004AC3D0` | Setter resolves the property path using the Race object key at `this+0x38`, then passes the value to native Broker setter `0x004D8000`. |
| `0x004AC040` | Getter resolves the same `this+0x38` property path and calls Broker value accessor `0x004D6760`. |
| `0x004AC100` | Equivalent getter for `Race/NumPlayers`, using the Race object key at `this+0x48`. |
| `0x0047AD11` | Stock continuation after the setup call. It obtains the transition owner and passes state `10` to `0x0045D910`. |
| `0x0045D910` | Stores the requested transition state in the frontend transition object; it does not synchronously construct the race actors. |
| `0x00408660` | Later race-scene setup resolves `Race/NumCars`, reads it through `0x004D6760`, and uses the result as the bound for constructing per-slot vehicle-sound objects. |

The original Start callback calls setup once and then executes the transition
continuation. The native setter is a Broker write, while the first later scene
consumer is a separate path that reads the published count. Static analysis
does not establish the precise scheduling/cache reason for the v9 immediate
observation. It does establish that a pre-transition read is not a safe
criterion for canceling setup and that the scene later has its own NumCars
consumer. The v10 observer is installed at that later call site.

## v10 operation

The Start hook at `0x0047AD0C` preserves the pre-start count/mode/capability
checks. If admitted, it saves flags/registers around the phase marker, calls
`FUN_0047B780` exactly once with the original call-site context, marks setup
returned, restores caller state and unconditionally jumps to `0x0047AD11`.
The original transition call at `0x0045D910` remains owned by stock code.
Five through seven AI remain refused before setup; four AI requires explicit
experimental opt-in and an expected total not exceeding the native Car0..Car7
bound. No post-setup counter value vetoes Start.

The read-only observer replaces the five-byte call at `0x0040869B` (original
`E8 C0 E0 0C 00`, target `0x004D6760`) with a call to an external stub. The
stub:

1. Replays the native Broker value getter with the original ECX and stack
   argument.
2. Preserves the returned EAX, flags and general registers around the
   diagnostic callback.
3. Returns to the original scene function without changing its cleanup.

The callback runs only for admitted experimental four-AI Quick Race after the
native setup phase. It logs raw NumCars and NumPlayers. It reads participant
slots only when raw NumCars is within 1..8; an invalid NumPlayers value does
not erase otherwise safely bounded raw slot telemetry. The observer never
changes a Broker value, rejects a roster or blocks gameplay. The line is
evidence of what this later native consumer sees; human observation is still
required to establish active AI actors, movement, Results and return.

## Runtime log repair

The old file handle combined `FILE_APPEND_DATA | GENERIC_WRITE`; ordinary
`WriteFile` could use the initial file pointer and overwrite earlier lines.
The v10 logger opens with `FILE_APPEND_DATA | FILE_READ_ATTRIBUTES` (no
`GENERIC_WRITE`), serializes writers with an SRW lock, writes each sanitized
line plus CRLF in one call, and rotates at 64 KiB to one `.1` backup. The x86
Windows harness checks CONFIG, START and ROSTER records remain intact and
chronological.

## Evidence status

- Exact-retail disassembly and generated bytes: `STATICALLY_VERIFIED`.
- Native logger behavior in the Windows x86 harness: automated build/run
  required for each candidate build.
- Five-active-participant gameplay, AI movement, Results and return on v10:
  `PENDING_HUMAN_RUNTIME`.
