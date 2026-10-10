# R-OBS1 — separate live verdict

Use pristine retail, the updated Observatory package or canonical
`tools/runtime/mr_observe.py`, and the candidate DLL identified in validation.
Close the game before replacing a DLL; retain the accepted DLL separately.
Keep all other renderer settings constant. No deployment/game launch was done
by the agent. Do not test Exclusive.

First use the regular R-OBS1 candidate with `[Display] Mode=1`:

1. Open Broker Editor once through Observatory `[1] Broker Editor`.
2. Verify prompt opening and game responsiveness.
3. Run original Debug → Dump (or Capture Snapshot after verifying Broker).
4. Confirm a fresh complete Dump/capture; close Broker, reopen once.
5. Check Windowed resize and F10.

Repeat essential open/Dump/close with Mode=2. Stock Mode=0 remains the baseline.
This yields **two separate results per mode**: native Broker opening and actual
fresh Dump completion. A sent command, timeout, DLL build or existing old Dump
does not constitute PASS.

If either non-Stock mode still stalls, restart the process and compare:

| Configuration | DLL | Display.Mode |
| --- | --- | --- |
| A | regular R-OBS1 | 0 |
| B | regular R-OBS1 | 1 |
| C | diagnostic no-hooks R-OBS1 | 1 |
| D | regular R-OBS1 | 2 |
| E | diagnostic no-hooks R-OBS1 | 2 |

The no-hooks candidate changes only installation of the two thread hooks;
window/presentation handling and updated Observatory are held constant. It
does not prove cursor behavior while Present is stopped. It is not the preferred
daily DLL. The previous accepted DLL may be used as an additional comparison.

Save Observatory's `Tool opener:` result and session trace. New queued records
for `WM_COMMAND`, wparam 39, bracket the main WndProc with observed ticks.
If the native handler never returns, buffered telemetry may not flush; absence
of a record is not proof that the native handler was not entered. Report the
candidate/mode, elapsed delay, Broker appearance, continued game response,
fresh Dump, close/reopen, resize and F10 independently.

R-OBS1 is runtime PASS only when regular Windowed and Borderless both open Broker
without the reported stall and create fresh valid Dumps. No retry after an
uncertain opener is automatic. Let any pending native command finish or close
the process before a controlled fresh attempt.
