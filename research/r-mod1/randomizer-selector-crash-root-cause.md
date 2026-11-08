# R-MOD1 v6 randomizer-only crash: callback gateway ABI

## Finding

The first invalid control-flow transition is the `RET` at the end of the v6
choice callback gateway at `0x70000106`. The Quick Race selector calls the
gateway with four `__stdcall` arguments for `MRChooseClassV1` (`hint`, `first`,
`count`, `slot`). The old gateway was:

```text
0x70000100  FF 15 08 00 01 70    CALL dword ptr [0x70010008]
0x70000106  C3                   RET
```

That adds a second return address between the selector and the export. The
callback consequently sees `(selector_return, hint, first, count)` instead of
`(hint, first, count, slot)`. For the captured first AI, its guard sees a
nonzero `hint` and returns the fail-safe class value `-1`. Its `RET 16` then
returns to the gateway, leaving the selector's pushed slot value `1` at the
top of the stack. The gateway's `C3` consumes that value as its return address
and transfers control to `0x00000001`.

The corrected gateway tail-forwards the original call frame:

```text
0x70000100  FF 25 08 00 01 70    JMP dword ptr [0x70010008]
```

Now `MRChooseClassV1` sees the original four arguments, and its stdcall
`RET 16` returns directly to the selector after the `CALL 0x70000100`. The
callback still returns only a class index or the stock-fallback sentinel;
native Quick Race code continues to own physical CarID and DriverID selection.

## Runtime evidence alignment

The available v6 decoded JSON reports the randomizer-only configuration
(`config_flags=5`: Randomizer and Logging; Opponent Extender off), `start_phase=0`
and `EIP=exception_address=1`. Its saved stack at `ESP=0x001AFC80` begins:

```text
[ESP+00] FFFFFFFF  saved EDI
[ESP+04] 00000001  saved ESI / first AI slot
[ESP+08] 00000004  saved EBP
[ESP+0C] 001AFCA0  saved pre-PUSHAD ESP (ESP + 0x20)
```

This is the selector's `PUSHFD/PUSHAD` save frame after the bad gateway `RET`
has consumed slot `1`; it matches the statically reconstructed stack exactly.
The record's `ExceptionInformation=[0,1]` labels a read access to address `1`,
which is inconsistent with an instruction-fetch fault at EIP `1`. That access
mode discrepancy is retained as an evidence limitation rather than silently
rewritten. The decoded record has no symbolic stack-frame entries (`frames=[]`);
the captured x86 register context and raw stack words are the available crash
stack evidence. The root-cause attribution rests on the emitted gateway ABI
and captured return target/save-frame shape.

The human-supplied text names both the 436-byte raw crash log and its decoded
JSON. In the current handoff, only the JSON exists in the ignored v6 candidate
directory; the raw `.bin` was not found in the attachment or available project
paths. Consequently no raw-sidecar SHA is claimed. The compact regression
fixture under `tests/synthetic/fixtures/` preserves only the copied fields
needed for the stack correlation and records that limitation.

## Why the other paths are not the root cause

- The independent ONE–SEVEN UI path uses the opponent-limit gateway with no
  arguments. Its `CALL [cell]; RET` wrapper does not shift any arguments.
- The Randomizer-only capture had the Start guard disabled, so this fault does
  not originate in `MRCanStartQuickRaceV1`, native setup, or prepared-roster
  validation.
- The callback rejects the shifted `hint` before obtaining the race singleton,
  reading the player slot, querying unlocks, or drawing from the native RNG.
  Those functions therefore cannot be the first failing transition in this
  captured path.
- Historical R-AI1.2 used an argument-aware loader thunk that copied the four
  arguments into a direct call to the export and cleaned its own frame. The
  R-MOD1 simplification introduced the extra call frame.

The current source also corrects the `0x004B0310` prototype to the audited
no-argument cdecl progress-state singleton. Other callback native boundaries
remain matched to retail epilogues: race singleton `0x004ADA50` and RNG
singleton `0x004D1E90` are no-argument cdecl; slot getters `0x004AC660` and
`0x004AC730` are thiscall/`RET 4`; unlock lookup `0x004AFB70` is thiscall/
`RET 4`; RNG range `0x004D1DF0` is thiscall `(low, high)`/`RET 8`.

## Regression and candidate boundary

`test_choice_gate_forwards_actual_stdcall_frame_and_rejects_old_call_ret_gate`
symbolically executes the actual emitted selector argument setup and gateway
bytes. It proves the corrected gateway delivers `(0,1,3,1)` and returns to the
selector, while the old gateway presents shifted parameters and returns to
EIP `1`. The same test correlates the captured v6 save frame. Retail ABI byte
checks cover the native singleton/getter/unlock/RNG returns.

The candidate builder now emits
`.research-output/r-mod1/first-integrated-candidate-v7/`. The v6 artifact is
preserved as the failed runtime reference. The v7 artifact is a static,
fail-closed test candidate until the owner retests Randomizer-only Quick Race
and confirms the game remains stable. This patch does not change opponent
count policy, Start admission, grid limits, renderer proxy behavior, Vehicle
SDK integration, or the original executable on disk.
