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

R-OBS1 originally provided a bounded deferred message buffer and an internal
no-hooks diagnostic build for a controlled comparison. The user's successful
no-hooks runtime result supersedes that temporary implementation in R-OBS1b:
the two callbacks, installer/uninstaller, hook owner, buffer and build switch
are removed from production. Present-time cursor polling and shutdown restore
remain. Native Reset/window/resize diagnostics remain; historical pre/post
message records are no longer generated or fabricated from snapshots.

R-CAM1-A3c state/patching logic, GameFov, UI/carousels, MenuFreezeFix, AF/MSAA,
reflections, foliage and native Dump implementation are unchanged. Exclusive
stays deferred. No Freecam work belongs to this phase.
