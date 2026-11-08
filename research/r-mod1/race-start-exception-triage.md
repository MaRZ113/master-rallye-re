# R-MOD1 — Randomizer selector AV and separate Start-hook status

## Randomizer-only v6 crash: root cause identified

The owner supplied a decoded v6 crash record for the `randomizer-only`
configuration. It reports `0xC0000005`, `EIP=exception_address=0x1`,
`ESP=0x001AFC80`, `ESI=1`, `EBP=4`, `EDI=0xFFFFFFFF`, `config_flags=5`, and
`start_phase=idle`. The opponent extender was disabled, so the Start guard was
not installed. The saved stack is the selector's `PUSHFD/PUSHAD` frame after
the bad choice-gateway `RET` consumed AI slot 1. The emitted old gateway is
`FF 15 08 00 01 70 C3`: it creates a nested call frame for the four-argument
`WINAPI MRChooseClassV1`, shifts its parameters, and then returns through the
slot value. The fix is the ABI-preserving tail gateway `FF 25 08 00 01 70`.
See [randomizer selector crash root cause](randomizer-selector-crash-root-cause.md)
for the stack proof, evidence limits and before/after bytes.

The human-provided text states that both a raw 436-byte-record log and JSON
were supplied. Only the JSON is present in the current handoff; the raw `.bin`
was not found, so its hash has not been independently verified. The decoded
record's `ExceptionInformation=[0,1]` says read access to address 1, which is
inconsistent with an instruction-fetch fault at EIP 1. This discrepancy is
retained; the callback-gateway root cause is supported by the exact emitted
ABI and captured stack layout, not by rewriting the access-type field.

The decoded first-chance register context is `EAX=FFFFFFFF`, `EBX=0`,
`ECX=94CAD48D`, `EDX=30000`, `ESI=1`, `EDI=FFFFFFFF`, `EBP=4`,
`EFLAGS=10246`, `ESP=001AFC80`, `EIP=1`. Its `frames` array is empty, so there
is no symbolic call-stack list to report. The 32 captured stack DWORDs are
preserved in the regression fixture; the first four match the selector's saved
register frame and pre-`PUSHAD` ESP.

## Separate opponent Start-hook report

An earlier v5 attempt also reported a Quick Race Start AV. That report had no
phase/EIP capture. The new v6 crash reproduces with Randomizer enabled and the
opponent Start guard disabled, so it establishes an independent randomizer
failure. It does not qualify the opponent-extender-only or combined Start
paths. No Start admission-policy change was made; recheck those configurations
after the owner confirms the v7 Randomizer-only path.

## Static Start-hook and native ABI audit

The retail callback has already set `ECX=ESI` at `0x0047AD0A`; the original
call at `0x0047AD0C` is `E8 6F 0A 00 00`, targeting native setup
`0x0047B780`, and returns to `0x0047AD11`. The setup routine begins with
`PUSH ESI`; its observed terminal paths restore ESI and use plain `RET`.
It takes no stack arguments. Thus the gate's single direct call to setup
preserves the stock call semantics.

Historical v6-v9 Start gate behavior balanced `PUSHFD/PUSHAD` around DLL
callbacks, called setup once, then ran prepared-roster validation and could
execute the parent's `POP ESI; ADD ESP,30; RET 4` epilogue instead of the
stock transition. That post-setup veto was removed in v10 after the owner's
four-AI Start attempt was denied on an immediate Race-counter observation.

## v10 Start-button correction

Exact-retail disassembly shows setup `FUN_0047B780` publishes
`Race/NumCars=selected_count+1` through `0x004AC3D0`, then the original callback
continues at `0x0047AD11` and schedules state 10 through `0x0045D910`. The old
v9 diagnostic printed values from a default roster snapshot when raw counters
were invalid, so `actual=0` does not establish the raw getter result.

In v10 the allowed path calls native setup exactly once, preserves caller
registers/flags/stack around phase markers, and unconditionally reaches the
original continuation. The only Start denial remains the pre-start bounded
capability/configuration check. A separate observer wraps the original
`FUN_004D6760` call at `0x0040869B`, the later race-scene `FUN_00408660`
NumCars consumer. It replays the getter, logs raw NumCars/NumPlayers and safely
bounded CarN fields, and never vetoes or mutates gameplay. See
[`start-button-v10-hotfix.md`](start-button-v10-hotfix.md) for the native
publication/consumer trace and logger fix.

The retail preimage audit also confirms the currently declared helper ABIs:

| Address / helper | Retail terminal bytes | Declared convention |
|---|---|---|
| integer getters `0x004AE030`, `0x004AE090`, `0x004AE150` | plain `RET` | cdecl, no stack arguments |
| Boolean getters `0x004AE0F0`, `0x004AE2D0` | plain `RET` | cdecl, no stack arguments |
| Quick Race vehicle getter `0x004ADFB0` | `0x004ADFD7: C2 04 00` | stdcall, one 32-bit argument |
| race slot getters `0x004AC660`, `0x004AC730`, `0x004AC5C0` | `C2 04 00` on terminal paths | thiscall receiver plus one stack argument |
| race singleton `0x004ADA50` | plain `RET` | cdecl, no stack arguments |

`tests/synthetic/test_r_mod1_native_plan.py` checks these bytes and the exact
hook/call/continuation bytes against the pinned pristine EXE. It also checks
that the emitted gate has exactly one native setup call and that the diagnostic
markers preserve ESP, flags and ECX around that call. These checks keep the
Start path separate from the fixed Randomizer callback path.

## Diagnostic instrumentation in v6

The Start policy and admission checks remain unchanged through v9. The v10
generated gate
calls `MRSetStartPhaseV1(4)` immediately before the native setup call and
`MRSetStartPhaseV1(5)` immediately after it returns; each callback is wrapped
in `PUSHFD/PUSHAD`, then restores both. The existing callbacks mark guard entry,
allow/block outcome, validator entry and validator accept/reject.

When `[Logging] Enabled=true`, the runtime core opens
`MRallyeRandomizer-crash-v1.bin` beside the game EXE and registers a vectored
exception handler plus a top-level exception observer outside the loader lock.
Access violations are recorded and always continue through normal exception
search. The prior top-level filter is called if one existed; the instrumentation
does not suppress the game exception.

Each fixed 436-byte `RMCRASH1` record includes:

- record kind: session, first-chance access violation, or unhandled access violation;
- exception code/flags/address and up to 15 exception parameters;
- x86 EIP, ESP, EBP, EAX, EBX, ECX, EDX, ESI, EDI and EFLAGS;
- 32 raw DWORDs from the captured ESP and up to 16 EBP/return-address pairs;
- randomizer/opponent/logging flags, last Start phase, opponent count, track,
  race mode, Ghost, SplitScreen, player physical ID and player class.

The packaged `MRallyeRandomizerCrashDecode.py` emits JSON and rejects partial
records. A controlled x86 harness raises a caught access-violation exception,
checks the emitted record and confirms the exception remains catchable. This
validates the recorder but does not substitute for capturing the game's
Quick Race crash.

## Human retest gate

Use v7 in a disposable game copy. Run its exact-build verifier and suspended
preflight first. The minimal first retest is `profiles/randomizer-only.ini`
with a normal supported count (1–3 AI); do not use higher counts. If it passes,
compare stock-only, opponent-extender-only and combined profiles at the same
count and with the same mode, track, vehicle, Ghost and SplitScreen settings.
The UI stack fix is unchanged from v6 and was separately reported by the owner
as working through Seven while refusing unsupported starts.

For each run preserve the diagnostic log and decode it with:

```powershell
python MRallyeRandomizerCrashDecode.py MRallyeRandomizer-crash-v1.bin `
  --output r-mod1-crash.json
```

If the Randomizer-only crash recurs, preserve both raw `.bin` and JSON and
compare the callback-gateway EIP/stack to the v6 fixture. For opponent-enabled
tests, use `start_phase_name` to distinguish guard, native setup and prepared
validation. If no log exists, report that separately; do not treat it as a
successful race. A successful menu launch or loader log alone is not gameplay
proof.
## v10 runtime failure and v11 response

The owner reports a v10 race-loading AV at `0x004D684E` while writing through
`0xFF821F54`; the phase was `native_setup_returned`. The supplied crash record
also reports `EDX=0x004086A0`, the original continuation after the native
getter call. The v10 wrapper changed the direct `CALL 0x004D6760` call frame,
so the getter treated that continuation address as its output pointer. This is
an independent race-loading failure, not the v6 selector AV or the v9 inert
Start failure.

V11 removes the observer and leaves `E8 C0 E0 0C 00` at `0x0040869B` exactly
as retail. The Start gate is unchanged: one setup call followed by the stock
transition, with no post-setup counter veto. First v11 runtime retest must
record any new exception addresses and independently verify participant
materialization; the old v10 EIP must not be assumed to recur.
