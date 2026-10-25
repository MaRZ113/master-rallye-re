# R5V-J.2 Critical Hotfix — Vehicle Select stack ABI

## Runtime failure and disposition

The first J.2 Vehicle Select re-entry candidate, launcher SHA256
`c10c27a72387004a3696a1eab3d25f24e777ea2c566bf0a5f642f68e1085765c`,
**FAILED_BY_HUMAN_RUNTIME**: opening Vehicle Select crashed. Its bundle remains
preserved in the ignored `j2-reentry/runtime-candidate` directory as a failed
candidate. This report does not assign a crash address because no exception
trace was supplied.

The J.1 two-addon loader/runtime baseline and the previously verified J.2
SplitScreen, Cup and Master Rallye captures remain valid. The failure is
localized to the J.2 constructor hook stub, not a reason to change J.1 or
vehicle resource state.

## Retail ABI evidence

The exact retail Ghidra exports under
`.research-output/vehicles/unlock/ghidra-export/` show these relevant native
sequences:

* `FUN_00480B60` at `0x00480B60` reaches the hook at `0x00481152` after native
  physical-ID restoration and sparse class/local mapping. The displaced
  instruction is `PUSH 0x006b74f8`; continuation is `0x00481157`.
* `0x004D0580` initializes a Broker path using `ECX` as the local path-object
  address and one stack path argument. Its epilogue is `POP ESI; RET 4`.
* `0x004D8EC0` returns the Broker container in `EAX`; its epilogue restores
  `EDI/ESI/EBX`, removes its own `0x20` bytes of locals and ends in plain `RET`.
* `0x004D8000` is the value setter (`ECX` is the container; stack arguments are
  path/index pointer and value). Its epilogue restores `EDI/EBX/ESI/EBP`,
  removes `0x24` local bytes and ends in `RET 8`.

The existing constructor provides an independent local-address oracle at
`0x00481130`: after its path push, `LEA ECX,[ESP+0x18]` addresses the Broker
path object at `S+0x14`, where `S` is ESP at the hook entry.

## Corrected stack model

For each YValue and XValue publication:

| Point | ESP relative to hook-entry `S` | Path-object calculation |
|---|---:|---|
| Hook entry | `S` | constructor local is `S+0x14` |
| `PUSHFD` | `S-4` | flags preserved |
| push path argument | `S-8` | `LEA [ESP+0x1c]` = `S+0x14` |
| `CALL 0x004D0580`, `RET 4` | `S-4` | argument removed by native callee |
| post-init `LEA` | `S-4` | `[ESP+0x18]` = `S+0x14` |
| getter + setter | returns to `S-4` | getter `RET`; setter `RET 8` consumes two staged args |

The failed stub used post-init displacement `0x14`, producing `S+0x10`, four
bytes before the initialized object. The repaired stub changes exactly those
two instructions to `8D 4C 24 18`; both pre-initializer `8D 4C 24 1C`
instructions remain unchanged.

After the second setter, `POPFD` restores ESP to `S`. The stub replays the exact
displaced `PUSH 0x006b74f8`, returning ESP to `S-4`, then jumps to
`0x00481157`. EDI (scene object) and ESI remain intact: the stub does not write
them, and the audited native helpers save/restore their nonvolatile registers.
EAX/ECX/EDX are volatile; the continuation immediately reconstructs ECX and
does not consume the stub's EAX/EDX values. The stub preserves incoming flags.

No separate x86 unwind record is generated for the short in-memory stub.
Normal execution has a verified balanced stack; exceptional unwinding from
inside a called native helper is not claimed as a supported path. The launcher
installs operations while the game thread is suspended, before normal
initialization resumes.

## Verification contract

`verify_republish_stub()` decodes the actual emitted bytes, rejects unknown
instructions, computes rel32 targets, and symbolically tracks pushes, helper
calls and callee stack cleanup. It requires both initialized Broker paths and
both post-init consumers to resolve to `S+0x14`, checks all six call targets,
PUSHFD/POPFD balance, setter cleanup, entry ESP before replay, the exact
replayed PUSH, and the continuation. The bundle builder invokes this verifier;
bundle verification regenerates and checks the same bytes.

The regression test mutates both repaired post-init displacements back to
`0x14` and requires verification to reject the stub. This prevents the previous
candidate's known crash-causing encoding from passing static verification.

## Repaired candidate

The repaired candidate is separate from the failed directory:

```text
.research-output/vehicles/sdk/j2-reentry/repaired-candidate/
```

It is derived from the exact verified J.1 246-operation bundle and appends the
same two J.2 operations, for 248 total. The original executable on disk remains
the pristine 3,121,214-byte retail file. Candidate hashes and test output are
recorded in [`critical-hotfix/`](critical-hotfix/) and the
[human retest instructions](human-qualification-handoff.md).

Static verification is **not** a runtime pass. J.2 remains
**READY FOR HUMAN RUNTIME** until a fresh-process test opens Vehicle Select,
switches classes and confirms ID27/ID26 re-entry without crashing.
