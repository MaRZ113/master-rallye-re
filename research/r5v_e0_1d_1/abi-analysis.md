# Full exists-getter ABI audit

## Evidence and identity

Retail `MRallye.exe` SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The E0 test baseline used to build the diagnostic is a distinct, previously runtime-confirmed candidate with SHA-256 `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`. Both contain the original call bytes at `004A7659..004A766F`; the generator accepts only the E0 baseline hash.

Evidence sources:

- Ghidra Bridge raw assembly for `FUN_004A74A0`, `FUN_004D8EC0`, and `FUN_004D7470`.
- Ghidra P-code for `FUN_004A74A0` and `FUN_004D7470`.
- Direct bytes read from the original retail executable.
- Ghidra Bridge context identifies `004A7661` inside `FUN_004A74A0`; the attempted `xrefs-to 0068E300` query reports no function there because the address is currently an unallocated tail, not an existing function.

The raw exports are ignored under `research-output/r5v_e0_1d_1/ghidra/`. Ghidra 12.0.4 was invoked through the installed local Ghidra Bridge against an isolated copy of the existing retail analysis project. No original binary or saved project was modified.

## Caller and stack layout

The instructions immediately around the patched call are:

| Address | Instruction | ABI consequence |
|---|---|---|
| `004A7655` | `LEA EDX,[ESP+0x58]` | Forms the stack-resident property path/object pointer. |
| `004A7659` | `PUSH EDX` | Adds the single argument that must be cleaned. |
| `004A765A` | `CALL 004D8EC0` | Pushes the return address; `004D8EC0` returns with plain `RET`, so the path argument remains. |
| `004A765F` | `MOV ECX,EAX` | Moves the returned object pointer into the implicit object register. |
| `004A7661` | `CALL 004D7470` | Enters the exists getter with return address at `[ESP]` and the original path pointer at `[ESP+4]`. |
| `004A7666` | `TEST AL,AL` | Consumes the returned exists flag. |
| `004A7668` | `JZ 004A76A0` | Preserves the existing fallback path when the property is absent. |

At `004D8F6B`, `FUN_004D8EC0` executes plain `RET`, with no immediate cleanup. In stack-relative terms, it removes its own return address and leaves the original pushed argument at the caller's top of stack.

At `004D7470`, the getter begins `MOV EAX,[ESP+4]`, then saves/uses `ECX` as its object pointer (`MOV ESI,ECX`). It uses the stack argument, computes a boolean result into `AL`, and reaches the common epilogue at `004D756B..004D7570`:

```asm
004D756B  MOV AL,DL
004D756D  ADD ESP,0x20
004D7570  RET 4
```

P-code shows the stack-space load for the argument and the byte-sized boolean result. The immediate stack cleanup is explicit in raw assembly. This is a `thiscall`-shaped callee: object pointer in `ECX`, one 32-bit stack argument, callee cleanup of four bytes, boolean in `AL`. The probable argument is a pointer to the formatted property-path object; its exact C++ source type is not asserted.

## Argument/register map

| Source | Callee input/use | Destination/result | Confidence and evidence |
|---|---|---|---|
| `EDX = &stack_path` at `004A7655`, pushed at `004A7659` | First callee `004D8EC0` leaves it in place; `004D7470` reads `[ESP+4]` | Query/path argument to the exists getter | High; raw assembly and P-code stack-space data. |
| `EAX` returned by `004D8EC0` | Copied to `ECX` at `004A765F`; getter copies `ECX` into `ESI` | Implicit object/`this` pointer to `004D7470` | High; raw caller and callee assembly. |
| `ESI+0x18` at helper entry | Read by `CMP dword ptr [ESI+0x18],0` | HUD display-slot selector; zero is Car0 | High for field read; semantic label follows the established HUD consumer analysis. |
| Getter result | `MOV AL,DL` at `004D756B` | `AL` exists flag consumed by `TEST AL,AL` at `004A7666` | High; raw assembly and P-code. |

## Stack proof for both helper paths

Let `S` be ESP immediately before the original `PUSH EDX`. The original sequence evolves as follows:

1. `PUSH EDX` makes `ESP=S-4` and stores the path argument there.
2. `CALL 004D8EC0` temporarily pushes its return address. Plain `RET` restores `ESP=S-4`; the path argument remains.
3. `CALL 004D7470` pushes the consumer continuation, so at getter entry the return is `[ESP]` and the path argument is `[ESP+4]`.
4. `RET 4` pops the consumer continuation and advances four more bytes. Control reaches `004A7666` with `ESP=S`.

The corrected helper is itself called at `004A7661`, so it enters with exactly the same return/argument layout. Its slot-0 `RET 4` reaches `004A7666` with `ESP=S`. Its nonzero `JMP` tail-enters `004D7470` without pushing another return address; the original getter's `RET 4` also reaches `004A7666` with `ESP=S`.

It leaves `ESI` unchanged, leaves `ECX` unchanged on the tail path, returns `EAX=0` on the bypass path, and does not depend on flags after returning. The consumer immediately tests `AL`.

## Legacy failure

The old helper used plain `RET` for slot 0. That returned to the consumer with ESP still four bytes below the expected value, leaving the property argument unconsumed. Its nonzero path used nested `CALL 004D7470`; that adds a second return address, but the getter's `RET 4` cleans the stack as though the original argument directly followed its return address. The resulting nested path also corrupts the stack. These static stack effects explain why the old diagnostic was invalid and why its race-load crash carries no evidence about colour precedence. The exact later crash instruction was not captured.

## ReAgent / Ghidra agreement

ReAgent was not used in this microphase. There is no reconstruction conflict to report. Raw Ghidra assembly is authoritative for the instructions and return immediate; P-code supports the stack argument and `AL` dataflow. The candidate helper itself is checked byte-for-byte by the generator and synthetic tests; it has not been executed or runtime-confirmed.
