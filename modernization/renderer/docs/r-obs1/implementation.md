# R-OBS1 — bounded opener and callback work

Starting checkout: `master`, clean HEAD
`5a177d7c504ff2aae3c5c4359541ecb3f1b773fb` in `master-rallye-re-general`.
No new branch/worktree, retired-tree edits or push.

Observatory sends one allowlisted `WM_COMMAND 0x27`, with the original 3000 ms
SendMessageTimeout. It clears LastError before dispatch and preserves its actual
code and elapsed time. Zero/error 1460 mean uncertain completion; other Win32
errors remain failures. A bounded discovery grace (at most five seconds, at most
52 polls) may find an audited Broker HWND after timeout. It never sends a second
opener or command 2. A synchronous dispatch with no verified window is not open
success. Ambiguous windows, process exit and target identity changes reject.

The structured result records PID/HWND/command, code, elapsed time, process-alive
state (including unknown), found Broker HWND and `dump_sent=false`. The public
error handler retains this result instead of translating it into a generic
file-permission error. `OPEN_COMPLETED`, `OPENED_LATE`,
`OPEN_TIMEOUT_COMPLETION_UNKNOWN`, `OPEN_FAILED`, `TARGET_INVALIDATED` are
distinct. Existing already-open Broker reuse and native Dump dispatch remain.

Message callbacks now copy only audited scalar events and STYLESTRUCT payloads
to a 64-record fixed buffer with a 512-event lifetime budget. They perform no
JSON allocation, disk write, window snapshot, native owner read or stack capture.
Unrelated HWNDs and commands immediately return. The original hook chain and
lightweight cursor ownership handling remain. FP environment is preserved.
Present flushes telemetry outside the message callback. Records carry original
sequence/tick/reset epoch; window snapshots explicitly describe **flush time**,
not historical message-time geometry. Queue overflow is counted, not unbounded.
Nested flush is suppressed and new events wait for the next flush.

The two hooks install once. Partial install attempts roll back available hooks;
successful shutdown unhooks ownership before native release. Production Win32
calls use a MessageHookApi seam for install/failure/rollback/shutdown tests.
`MRR_DIAGNOSTIC_NO_MESSAGE_HOOKS` is an OFF-by-default build control, never an INI
option. Its separate candidate keeps the same styles, HWND, menu, window-size
and D3D presentation planner. Callback cursor reactions are absent by design,
so the no-hook DLL is an isolation tool, not an accepted shipping replacement.

R-CAM1-A3c state/patching logic, GameFov, UI/carousels, MenuFreezeFix, AF/MSAA,
reflections, foliage and native Dump implementation are unchanged. Exclusive
stays deferred. No Freecam work belongs to this phase.

Deferred records retain observation sequence, so their physical JSONL write
order may differ from immediate Reset events. The auditor reports both orders;
only explicit deferred window-message records receive this treatment. The
512-event budget notification is emitted once at flush, never in a callback.
