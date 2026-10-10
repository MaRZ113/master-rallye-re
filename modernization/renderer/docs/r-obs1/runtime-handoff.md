# Current Broker handoff

The user confirmed native Broker opening and fresh Debug/Dump with the separate
R-OBS1 no-hooks candidate, plus supported display/cursor/lifecycle behavior.
That isolation candidate is now superseded by the standard hook-free source
policy. Do not require a diagnostic CMake flag or compare old DLLs for normal use.

Use the one combined candidate and [R-OBS1b smoke test](../r-obs1b/runtime-handoff.md).
The updated Observatory still verifies exact main HWND ownership (including
menu-less retail Borderless), sends opener 0x27 once, handles uncertain timeout
and bounded late discovery, and sends Dump command 2 only to the verified Broker.

Broker open and actual fresh native Dump must both pass in the combined session.
No renderer pre/post window-message records are expected. Native Reset/resize,
F10, window snapshots and Observatory dispatch results remain useful. Further
instruction-level investigation of the old hook-enabled stall is deferred.
