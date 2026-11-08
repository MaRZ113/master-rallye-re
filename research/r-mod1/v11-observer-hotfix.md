# R-MOD1-D v11 — remove the ABI-breaking scene observer

## Runtime failure

The owner reports that v10 installed all eight image operations, reached race
loading, and then crashed. The binary crash record's latest session was PID
15920. First-chance and unhandled records agreed on:

```text
exception_code=0xC0000005
access=write
EIP=0x004D684E
invalid_address=0xFF821F54
ESP=0x001AFC0C
EDX=0x004086A0
ECX=0xF633E88B
start_phase=native_setup_returned
opponent_count=4 track=10 mode=2
```

The exact crash-record bytes were supplied with the owner's report; the
sidecar files were not present in the worktree at the time this closeout was
prepared. The register/disassembly evidence below is therefore recorded from
the supplied report and independently checked against the retail image.

## ABI root cause

Retail at `0x0040869B` directly calls native Broker getter `0x004D6760` and
continues at `0x004086A0`. The getter reads its argument from `[ESP+4]`, writes
through that pointer, and returns with `RET 4`.

In stock code, a direct CALL pushes its return address. At callee entry,
`[ESP]` is `0x004086A0` and `[ESP+4]` is the caller-provided pointer. V10
replaced that call with CALL-to-observer; the observer then issued another
CALL to the getter. At nested callee entry, `[ESP]` is the observer return and
`[ESP+4]` is the outer CALL return, `0x004086A0`, instead of the pointer.
Getter instructions then read executable bytes as a pointer and faulted while
writing. The reported `ECX=0xF633E88B` equals the little-endian dword formed
from bytes `8B E8 33 F6` at `0x004086A0`, further matching the corrupted
argument path.

The `RET 4` cleanup balances stack depth but cannot repair the wrong argument.
Extra PUSHAD/PUSHFD preservation around this wrapper would not fix the layout.

## Correction

V11 removes `post-init-roster-observer` from the production operation plan,
remote code template, bootstrap export resolution, runtime DLL exports and
callback implementation. The retail bytes at `0x0040869B` remain:

```text
E8 C0 E0 0C 00
```

The plan contains seven operations. No new instrumentation is added. CONFIG
and START remain the only runtime log records; use Observatory or a separately
audited debugger point for roster telemetry.

The v10 Start correction is preserved: bounded prechecks remain before setup,
the native setup function is called exactly once, and allowed starts continue
to `0x0047AD11`. No post-setup counter veto is reintroduced. The append-only
runtime logger remains unchanged.

## Five-participant boundary

Historical R-AI2 full-runtime qualification used guarded replacements at
`0x0047B88A` and `0x0047B8DD` plus its exact 131-byte count shim. The v11 plan
does not contain those operations. This hotfix does not import a separate
capacity patch. The Four UI selection and v11 Start path still need a human
test to prove the combined bundle materializes five actors.

## Validation gate

The exact retail call bytes, no-hook operation table, nested-call argument
model, seven-operation plan, launcher preflight, runtime DLL export set and
deterministic candidate reconstruction are checked before v11 handoff. V11
is not runtime-qualified until the owner confirms normal 1–3 AI behavior and
the experimental four-AI/five-total race, movement, Results and frontend
return.
