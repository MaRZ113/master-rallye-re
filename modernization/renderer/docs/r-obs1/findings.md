# R-OBS1 — Broker opening versus non-Stock display

Status: **BLOCKED_ON_BROKER_OPEN_INTEROPERABILITY** for the complete reported
stall. Two targeted corrections and an actual no-hook isolation DLL are provided.
There is no live Broker/Dump verdict for this candidate yet.

`CONFIRMED_BY_SOURCE`: Borderless removes the main HWND's menu in
`NativeWindows::apply`. Observatory previously required the Game → Reset/Exit
menu during discovery and again immediately before sending the opener. A valid
menu-less main window therefore failed discovery/validation. This explains that
specific Borderless refusal; it does **not** explain a three-second dispatch
stall in Windowed with an intact menu.

The fallback now requires exact pristine retail, independently verified live
opener capability, the native renderer singleton's +0x20 owner matching global
VA `0x006F9D80`, vtable VA `0x0069228C`, and owner+0x5C matching the selected
HWND. PID, exact title, visible window and executable profile are still checked.
Other profiles retain the established menu requirement; arbitrary HWND/PID or
command IDs are never exposed.

`CONFIRMED_BY_EXE`: global dispatcher VA `0x005B0990` / RVA `0x001B0990`, case
0x27, invokes Broker opener VA `0x0065E990` / RVA `0x0025E990`. The opener calls
window helper VA `0x0064EF10` / RVA `0x0024EF10`, which registers a class and
calls CreateWindowExA. Broker-local command 2 is a separate later route. The
new read-only Ghidra queries are bounded in the accompanying research ledger.

`CONFIRMED_BY_SOURCE`: non-Stock installs thread-local pre/post message hooks;
Stock does not. Previously selected messages synchronously allocated JSON,
inspected window/native owner state, captured stack traces and wrote session
logs from those callbacks. Those operations are now deferred. Their presence
was a credible reentrancy/latency suspect, but neither a specific deadlock cycle
nor the precise native blocking instruction has been established.

The exact unresolved question: with the same window/presentation planner and
updated verified opener, does the Windowed/Borderless stall persist when only
the two message hooks are omitted? Compare the separately identified DLLs in
[runtime-handoff.md](runtime-handoff.md). Until that comparison, hooks remain
**UNKNOWN** as the runtime cause. No timeout increase or native Dump patch was
used to claim a fix. The historical NULL StringList Dump defect is independent.
