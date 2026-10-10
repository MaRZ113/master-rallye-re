# R-OBS1 validation

Overall: **BLOCKED_ON_BROKER_OPEN_INTEROPERABILITY**, in-game result PENDING.
The menu-less identity correction is source/EXE-confirmed; the Windowed stall's
precise native mechanism is UNKNOWN. See the controlled hook-isolation handoff.

Executed before the independent R-ATTR1 change:

- Renderer Python: 140/140 PASS, 107.708 s.
- Root synthetic: 630/630 PASS, 9.250 s (17 new opener tests).
- Focused opener tests after final elapsed/discovery handling: 17/17 PASS.
- Final regular Win32 Release native suites: 11/11 PASS, 5.49 s, including
  deferred callback reentry, unrelated HWND/command exclusion, bounded queue,
  copied STYLESTRUCT, Stock exclusion, partial hook install rollback, one-time
  hook installation and shutdown, existing hidden-HWND resize/focus suites.
- Compileall and diff-check PASS.
- PE verifier PASS: PE32/I386, required direct exports, no recursive d3d8 import.

An initial root run failed only the existing clean-extraction boundary assertion
because TEMP was within `D:/Game/Master Rallye`. Re-running with TEMP/TMP outside
that tree (`D:/CodexScratch/r-obs1-tests`) passed all 630 tests. No test was weakened.

Final regular R-OBS1-only candidate: `.analysis/handoff/r-obs1/regular/d3d8.dll`,
1,675,264 bytes, SHA256
`afb8b446a354c3eb7a4ce0201d8271093a7410b9608b07af35ecb34c77b8c36c`.
The runtime package preserves this separately before the combined rebuild.
The diagnostic no-hooks identity and final regression results are recorded in
the package manifest. Both packages contain no game EXE/assets.

Read-only Ghidra 12.1.4/bridge exports verified the retail dispatcher, Broker
window helper and main-window owner. No project save occurred. Runtime
Broker-open, Dump completion and hardware display results have not been tested
by the agent. Source changes leave native Dump formatting and accepted camera,
UI and display planners intact; those require the compact live regression.

Final diagnostic follow-up: the first 140-test Python run preceded the final
native fixture regeneration. A later combined run exposed two telemetry
regressions: the hidden-HWND fixture had not flushed the new callback queue,
and the lifetime-budget record was omitted. They are corrected without putting
I/O back in callbacks. The fixture now flushes outside SendMessage, and the
read-only auditor distinguishes delayed physical writes from original observed
sequence numbers. Duplicate sequences, reordered immediate records and reordered
deferred records within a device still fail.

Final combined renderer Python: 145/145 PASS, 109.749 s (141 R-OBS1/base plus
4 R-ATTR1 tests). Final combined native: 12/12 PASS, 7.17 s. Rebuilt independent
R-OBS1-only source snapshot: 11/11 native PASS, 5.69 s; no guard source or call
in that snapshot. It uses the same final diagnostic corrections and canonical
window/presentation implementation, without changing the canonical checkout.

Final no-hooks R-OBS1-only native suites: 11/11 PASS, 5.70 s; PE verifier PASS.
Candidate `.analysis/handoff/r-obs1/diagnostic-nohooks/d3d8.dll`: 1,674,752 bytes,
SHA256 `20255885c28d01449c37637f4ed02dfb0ed9056a8fd719e0b7520f05cceb38ab`.
