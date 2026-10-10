# R-CAM1-A3c: fixed native observation sites

These are ten fixed exact-retail process-memory interception sites, with no
generic detour engine, function-entry relocation or on-disk EXE patch. Seven
five-byte relative CALLs and three aligned scene-job vtable words are replaced.
The class vtable pointer and job memory remain untouched.

| Event | Intercept VA / RVA | Original target | Native cleanup | Observer extent |
|---|---|---|---|---|
| Request after ID store | `005223D3 / 001223D3` | `004D11D0` | RET4 | before; tail-forward |
| Queue | `00522455 / 00122455` | `0052D550` | RET12 | before; tail-forward |
| Commit | `0052D6A4 / 0012D6A4` | `00522680` | RET4 | before and after original |
| RaceLimits attach | `0048E717 / 0008E717` | `004F5950` | RET8 | before and after initializer |
| Pending-to-live transfer | `004F6202 / 000F6202` | `004F62E0` | RET4 | after original |
| Retirement after bit set | `004F584E / 000F584E` | `004F6310` | RET0 | before; actor = ESI-18 |
| Destruction before unregister/free | `004F5786 / 000F5786` | `004F6310` | RET0 | before; actor = ESI |
| Open error, virtual +4 | `00691B14 / 00291B14` | `0052D5E0` | RET0 | before; tail-forward |
| Read/decode error, virtual +8 | `00691B18 / 00291B18` | `0052D600` | RET0 | before; tail-forward |
| Execute, virtual +C | `00691B1C / 00291B1C` | `0052D620` | RET0 | before and after entire callback |

`CONFIRMED_BY_EXE`: caller register/argument preparation, whole CALL boundaries,
targets, cleanup instructions, and eight surrounding contexts are pinned in
`RACE_OBSERVER_CONTEXTS` and the exact-build inspector. The scene-job vtable
words originally contain `E0D55200`, `00D65200`, `20D65200`. Installation checks
surrounding bytes twice, including after suspending other existing threads.
The inspector now verifies 86 instruction/data anchors. Existing GameFov
`006532DD` and scheduler completion `005B0166` are not intercepted by this pilot.

`CONFIRMED_BY_SOURCE`: input/output state is saved through PUSHFD/PUSHAD and
aligned FXSAVE. Observer callbacks run with DF clear, an initialized x87 and
default MXCSR; native FP state is restored before forwarding and after observing.
Post wrappers duplicate exactly the original stack arguments, load all saved
input registers/flags, call the native target once, then preserve its observable
registers, flags and FP outputs. The original caller's arguments are removed
with the matching RET n. No speculative return-address substitution is used.
The original callee sees a bridge return address in post wrappers; reviewed
callees use their ordinary arguments and returns, not return-PC inspection.

Installation pins the proxy module for process lifetime, suspends bounded existing
threads, rejects an instruction pointer inside any changed site, preflights all
bytes and overlap, then applies protection/write/readback/flush/protection changes.
Failure rolls back installed units in reverse. The thread enumerator is bounded
to 64; enumeration, suspension or context failures reject installation. It does
not claim a universal thread-creation lock. Source-supported game events are
expected on the device thread; unexpected event threads quarantine observation.
Code exchange and logging do not hold the epoch lock across native execution.

Owned bytes are revalidated at events and F10. A foreign hook is never overwritten
during removal. Removal requires the original device thread and no active execute
wrapper. Otherwise callbacks become read-only no-ops, originals and bridge storage
remain valid, and the pinned module cannot disappear. Unknown rollback bytes are
reported as `install_failed_rollback_unverified_restart_required`; pinned code
alone cannot guarantee that an unverified partial CALL is executable. This is
not reported as successful installation or guaranteed stock forwarding.

Native fixtures execute the actual production bridge functions for RET0/4/8/12,
including disabled callbacks, multiple calls and nested execute. They compare
ECX, EDX, float argument bits, nonvolatile registers, stack balance, EAX/EDX,
EFLAGS, x87, eight XMM registers and MXCSR, and check callback stack alignment.
Fault injection tests partial writes, protection/flush failures, rollback and
foreign ownership. These tests do not prove live installation in the game.
