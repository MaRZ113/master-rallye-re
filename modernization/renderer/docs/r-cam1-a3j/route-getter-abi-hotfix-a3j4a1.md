# R-CAM1-A3j.4a.1 — RaceLine Getter ABI Hotfix

**Status:** `ABI_HOTFIX_READY_FOR_RUNTIME`. The stack/register defect is repaired and covered by Win32 x86 call-contract tests plus production-DLL disassembly checks. The recovery crash is not declared fixed until the user completes one ordinary stock recovery run with this DLL.

## Exact retail contract

Target: pristine retail `MRallye.exe`, PE32/I386, ImageBase `0x00400000`, size 3,121,214, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

The retail caller at `0x004CCCA6` forms `[ESI+0x54]`, pushes the reference pointer, calls `0x004E51C0`, then moves that helper result to `ECX` before calling `0x004E4D20` at `0x004CCCB1`. The helper returns with ordinary `ret`, so the pushed reference is still the getter's stack argument.

The exact getter starts:

```asm
004E4D20  mov eax, [esp+4]  ; reference/index argument
004E4D24  mov edx, [eax]
004E4D26  mov eax, [ecx+4]  ; ECX is the native object input
...
004E4D3C  ret 4
004E4D3F  xor eax, eax
004E4D41  ret 4
```

This establishes that incoming `ECX` is required, incoming `EAX` is dead (the getter overwrites it before reading it), its return is in `EAX`, and both normal and NULL-result exits pop the one argument. The full getter bytes and the retail caller context/target are checked by `test_physics_probe_retail.py` against the exact executable.

## Defect and corrected bridge

The previous bridge called the getter without forwarding the reference argument and ended with plain `ret`. The getter therefore read the bridge return address as its parameter; its `ret 4` then consumed the wrong stack word, and the bridge's plain return treated the original argument as a return address. This was a concrete ABI defect consistent with the reported recovery-time crash, but only runtime retest can establish whether it was the crash cause.

The corrected bridge duplicates `[ESP+4]`, leaves `ECX` untouched, places the exact retail target in `EAX`, and calls it. Disassembly proves the getter does not use incoming `EAX`. After the native `ret 4`, it saves flags and all general registers, calls the observer with the saved native `EAX`, restores the complete native result, and returns with `ret 4` to consume the original caller argument. Native exceptions are not intercepted or translated.

```text
Original:
caller ESP=S, [S]=arg
  CALL getter -> getter ESP=S-4: [ret-to-caller] [arg]
  getter RET 4 -> caller ESP=S+4

Patched:
caller ESP=S, [S]=arg
  CALL bridge -> bridge ESP=S-4: [ret-to-caller] [arg]
  PUSH [ESP+4] -> duplicate arg; CALL getter -> getter sees [ret-to-bridge] [arg-copy]
  getter RET 4 -> bridge ESP=S-4, with original [arg] still at [S]
  save result/observe/restore -> bridge ESP=S-4
  bridge RET 4 -> caller ESP=S+4
```

Thus the bridge exits with the same `ESP` as the original getter call. `ECX` is preserved as the native object input; observer clobbers cannot replace `EAX`, `ECX`, `EDX`, callee-saved registers, or `EFLAGS` from the getter.

## Regression coverage

`route_getter_abi_tests.cpp` is a Win32 x86 harness using the same naked-assembly sequence with only the fixed retail callee and production callback replaced by controlled local test functions. The fake callee reads `[ESP+4]`, records `ECX`, returns a known value or NULL, sets observable flags/registers, and uses `ret 4`. The harness compares direct and bridged calls for argument, output registers, flags, and caller stack; the observer deliberately clobbers volatile registers/flags and must run exactly once. It repeats 130 calls with distinct arguments to expose stack drift. The NULL result is delivered to the observer and rejected by the production `pointer_shape` predicate used before native route dereferences.

Because the production bridge calls the fixed absolute retail VA, the test harness cannot point that compiled function at its local fake callee. The accepted equivalent arrangement is therefore: the harness exercises the same explicit x86 instruction sequence with a local target, and `test_route_getter_bridge_disassembly.py` resolves the production symbol through the Win32 linker map and byte-checks the built DLL for argument forwarding, the `0x004E4D20` target, result/flags preservation, observer call target, and final `ret 4`.

Before installing the optional route getter hook, runtime now checks the exact caller context, the getter's entry bytes establishing the `[ESP+4]` argument and `ECX` object input, and both native `ret 4` exits. A mismatch fails closed with a specific reason (`route_getter_context_mismatch`, `route_getter_entry_abi_mismatch`, `route_getter_success_ret4_mismatch`, or `route_getter_null_ret4_mismatch`). The route-getter patch remains conditional on both `[PhysicsObserver] Enabled=1` and `RoadTargetPreviewEnabled=1`. With road preview disabled, the existing three physics call hooks remain selected and no route getter callsite is patched. Exact pristine hash/context gates, quiescence, patch ownership, rollback, restoration, and module pinning are unchanged. No additional native hook site was added.

## Safety and deferred findings

The observer still only reads game state. The NULL result is rejected as `native_raceline_object_pointer_invalid`; no invalid pointer is treated as a RaceLine merely because the ABI is corrected. No Broker, controller, chassis, wheel, or physics field is written. Teleport remains unimplemented. The earlier 32-entry clear-writer diagnostic buffer saturation remains deferred and is not part of this hotfix.

## One-session runtime handoff

1. Back up the currently installed stable `d3d8.dll`, then install the rebuilt Win32 Release DLL and fully restart pristine retail Master Rallye.
2. Enable `Trace.Enabled=1`, `[PhysicsObserver] Enabled=1`, and `RoadTargetPreviewEnabled=1` in the existing renderer config.
3. Start offline France1, drive briefly, trigger one ordinary native vehicle recovery, wait for it to finish, then confirm driving continues without a crash.
4. Optionally activate Freecam and capture one F10 frame; exit normally and provide the session JSONL plus the frame JSONL if captured.

Expected diagnostics retain the existing event names with phase `R-CAM1-A3j.4a.1`. Require successful setup, normal teardown/restoration, existing physics observer activity, and a route getter event/snapshot only if recovery actually reaches the getter. A NULL or malformed result must be rejected with a precise reason. A valid route snapshot is diagnostic evidence only and is not authorization to teleport.

**Primary acceptance:** ordinary stock recovery completes and the game remains stable. This acceptance is pending human runtime validation.

## Build evidence

The current ignored local artifact is `modernization/renderer/.build-msvc/Release/d3d8.dll`, 2,121,728 bytes, SHA-256 `53a1de53047134791e9e811dc7a727d90ab92f247088ab4c012f661c2a89891d`. Proxy verification reports PE32/I386, the expected `Direct3DCreate8`, `ValidatePixelShader` and `ValidateVertexShader` exports, and no recursive `d3d8.dll` import.

Automated validation: native CTest **18/18**, renderer Python suite **166/166**, root synthetic suite **630/630**, `compileall` passed, exact-retail executable checks **4/4**, and production bridge disassembly checks **2/2**. `git diff --check` passed. The x86 ABI harness exercises direct versus bridged calls, NULL forwarding/rejection, output registers and flags, exact post-call ESP, observer call count, and 130 repeated calls. These results are build/test evidence only; no repaired-build game session has been captured yet.
