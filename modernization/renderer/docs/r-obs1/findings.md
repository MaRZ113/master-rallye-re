# R-OBS1 — Broker opening versus non-Stock display

Current status: **hook-free Broker open and native Dump CONFIRMED_BY_RUNTIME**,
reported by the user in the R-OBS1b closeout request. Windowed/Borderless usability,
cursor auto-hide/Alt+Tab, minimize/restore/Reset and accepted visuals also passed
the user's no-hooks test. The new combined standard build remains **PENDING
HUMAN VALIDATION**. See [R-OBS1b closeout](../r-obs1b/closeout.md).

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

The controlled comparison is now completed by the user: suppressing only the
two renderer thread-message hook installations while retaining the same
window/presentation path restores Broker open and native Dump. This supports
retiring the hooks as the compatibility policy. The exact original blocking
instruction or Win32 deadlock cycle remains **UNKNOWN**, with further root-cause
research deferred. No timeout extension or native Dump patch is the fix.
The historical NULL StringList Dump defect remains independent.
