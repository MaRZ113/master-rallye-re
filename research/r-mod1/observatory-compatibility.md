# R-MOD1-OBS — Observatory compatibility diagnosis

## Status and evidence boundary

This is a static compatibility audit and a human diagnostic handoff. No crash
record containing exception EIP, code, stack, or native caller was supplied in
this work item or found in the active R-MOD research output. Therefore the
reported Broker Editor failure's exact runtime cause is **UNKNOWN**. The report
does not assign a Dump-walker failure to an Editor-open crash.

The owner reports the R-MOD v11 four-AI / five-total Quick Race behavior as
human-confirmed. That gameplay evidence remains independent from this
Observatory compatibility test. The historical candidate manifest remains a
build-time manifest and is not rewritten to claim it had runtime evidence
when it was produced.

## Operations are separate

| Operation | Audited route / behavior | Current conclusion |
|---|---|---|
| Observatory Status / process verification | Read-only process identity, mapped image and required live anchors | Must be tested by itself; it does not invoke the native Broker Editor or Dump. No R-MOD operation overlaps the Broker Editor/Dump anchors. |
| Open Broker Editor | Retail command route reaches opener `0x0065E990`; editor dispatcher is `0x0065EC40`. The open-only route registers `__NO_SAVE` / `__NO_CHANGE` metadata in shared in-memory broker bookkeeping. | Not the Dump walker. R-MOD v11 does not patch the opener, dispatcher, manager accessor, or their direct callers. No EIP/call stack is available to identify a runtime fault. |
| Native Debug → Dump | Editor command case 2 calls manager accessor `0x004D8EC0`, walker `0x00601D00`, then Debug sink formatter `0x004D0620`. | R-MOD leaves this native route and walker stock. Test only after editor-open-only is safe. Do not run a Results Dump unless the effective live walker variant has verified Results safety. |

`tools/runtime/broker_observatory.py` verifies the live main image and anchors;
its Status/capture path uses read-only process access. It does not invoke the
native Dump command. The `open_broker_editor` capability checks the editor route
anchor, while `native_dump` separately verifies the walker and, when hardened,
both approved trampolines. A Status failure is therefore not evidence that the
game's Editor opener crashed.

## Patch and address collision audit

The exact R-MOD v11 plan has seven image operations:

| R-MOD operation | VA | Length |
|---|---:|---:|
| OEP bootstrap | `0x005C4602` | 5 |
| Quick Race selector init | `0x0045810B` | 7 |
| Quick Race selector loop | `0x00458379` | 9 |
| Quick Race selector end | `0x004582D5` | 7 |
| Opponent list append | `0x00479DCB` | 8 |
| Opponent arrow bound | `0x0047A32C` | 3 |
| Quick Race Start guard | `0x0047AD0C` | 5 |

None overlaps the Broker Editor opener/dispatcher (`0x65E990` / `0x65EC40`),
Dump walker (`0x601D00..0x602300`), either historical NULL-sensitive Dump
instruction, or either historical trampoline address. The historical guard
instruction preimages in the exact retail image are:

```text
VA 0x0060201E: 8B 7B 04 3B 7B 08
VA 0x00602153: 8B 10 8B C8 FF 52 0C
```

R-MOD v11's remote code/data reservations are `0x70000000..0x70010000` and
`0x70010000..0x70020000`; these do not collide with historical trampoline VAs
`0x0068E6D0` and `0x0068E6F0`. Those old trampoline VAs are not reused. The
pristine bytes at those historical locations are zero padding, but that fact
alone does not authorize reuse. No compatibility patch is added because the
current evidence does not establish that a patch is necessary.

## Are the J.1 NULL guards relevant?

They guard only two nullable payload paths *inside native Dump*:

- StringList: NULL payload at `0x0060201E` branches to the existing empty-list
  cleanup.
- XmlData: NULL getter result at `0x00602153` branches to existing no-root
  cleanup.

They do not alter Broker Editor construction, its open-only metadata
registration, or Observatory Status. Historical J.1 runtime evidence covers
survival/continuation for the qualified hardened Results Dump case; it does not
prove universal Dump safety or an Editor-open fix. The current R-MOD process
has a stock walker. Observatory must report that effective stock variant and
must not grant hardened Results-Dump safety from the pristine on-disk hash
alone.

If an isolated native Dump later fails at one of the known NULL dereferences,
the narrow J.1 guards become relevant. First rebase their two call-free stubs
into a newly audited free interval within the R-MOD remote code allocation,
then add the two image operations to the single R-MOD planner with exact
preimages, dependencies, overlap checks, and live post-install verification.
Do not copy the historical caves or add a second injector. If the crash is in
the Editor opener/dispatcher, these Dump guards are not a supported remedy.

## Passive Race-state reader

The retail Broker partial layout is known: singleton pointer at `0x006F9410`,
entry vector pointers at manager `+0x04/+0x08/+0x0C`, entry stride `0x1C`,
path ID at `+0`, payload at `+4`, and type tag at `+8`. The string pool has a
manager global at `0x006F93D4`; IDs are sequential intern IDs, not hashes.
However, a complete bounded read-only ID-to-path enumeration and all required
typed payload layouts have not been implemented and independently tested in
the R-MOD worktree. `Race/CarN` may also be XmlData roots rather than recursively
enumerable Broker subtrees. No Race-state inspector is claimed or shipped.

The current supported observation path remains the audited native Dump text
buffer reader when Status verifies the process and the native Dump capability
allows that effective walker state. No native getter is called remotely;
Observatory does not inject or write process memory.

## Minimal human isolation protocol

Use the existing v11 candidate. Its packaged profiles enable exception
logging; the logger is diagnostic and does not install a Broker hook. Keep the
candidate's INI/profile hash and the exact retail EXE hash in the run notes.
For each row, start a fresh process and preserve any
`MRallyeRandomizer-crash-v1.bin` before the next run.

| Run | Runtime | Action, in order |
|---|---|---|
| A | pristine retail, no launcher | Start, open no Editor, close normally. Separately record whether the report reproduces on the control. |
| B | v11 `profiles/stock-features-disabled.ini` (logging-only bootstrap) | Connect Observatory and run Status only. Do not open the Editor or Dump. |
| C | v11 same logging-only profile | Open the Broker Editor in the frontend only. Do not invoke Dump. Record whether the window opened, game remains responsive, and first exception record if it crashes. |
| D | v11 same logging-only profile | If C is safe, repeat Editor open-only while at the Quick Race frontend, then during an active normal-count Quick Race; close each window without invoking Dump. |
| E | v11 normal feature profile matching the reported configuration, with Logging enabled | Repeat Status, then Editor open-only as separate actions. The packaged `randomizer-only.ini`, `opponent-extender-only.ini`, and `both-normal-counts.ini` each enable logging. Compare against B/C to identify which R-MOD hooks are required for reproduction. |
| F | only after Editor open-only is safe | Invoke native Debug → Dump once during a normal active race; save the native diagnostic log and Observatory raw sidecar separately. Do not run it on Results with the stock walker. |
| G | Results | Test normal game Results visually. Invoke native Dump only if Status attests the exact approved hardened in-memory walker and both trampolines; this v11 candidate does not install that variant. |

Decode each R-MOD exception log with the candidate's
`MRallyeRandomizerCrashDecode.py`. Preserve exception code/parameters, EIP,
ESP, registers, captured stack words, and phase. Resolve the first non-R-MOD
return address against the exact retail image before naming the native caller.
If the process hangs without an access violation, collect a debugger break/hang
stack instead; no AV record is expected for a pure hang.

## Current disposition

- Observatory Status compatibility: **STATICALLY COMPATIBLE; HUMAN RETEST
  PENDING**.
- Broker Editor open: **ROOT CAUSE UNKNOWN; isolate with open-only test**.
- Native Dump: **stock live variant; J.1 guards are Dump-only and not installed
  by v11**.
- Passive Race-state reader: **NOT IMPLEMENTED**.
- Native compatibility changes: **none justified before exception evidence**.
- Candidate: existing `first-integrated-candidate-v11`, with no change to its
  seven operations or five-participant gameplay behavior.
