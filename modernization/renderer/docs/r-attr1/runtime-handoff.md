# Independent R-ATTR1 and combined smoke test

Use the combined candidate, pristine retail EXE and normal user INI. Preserve
the accepted DLL separately and replace it only with the game closed. Do not
use the R-OBS1-only/no-hooks DLL for the Attract test: those intentionally do
not include this guard. No game files were deployed or launched by the agent.

First inspect the new session's `legacy_loading_attract_guard`:
`exact_retail=true`, `phase_verified=true`, `context_verified=true`,
`quiesced=true`, `applied=true`, `owned=true`, `rollback_verified=true`.
If admission is rejected, report the exact reason; do not treat the fix as
installed or retry it during the race. Unknown builds receive no guard.

R-ATTR1 test, separately from Broker opening:

1. Enter a normal offline Quick Race and verify player control.
2. Restart; verify player control and ordinary race presentation.
3. Restart again; verify the same.
4. Return to frontend and start another Quick Race.
5. Verify it remains a normal player race. Where Broker capture is available,
   check Race/AttractMode=False during these ordinary race loads; record the
   actual native Race/Type without assuming a required numeric type.

Legitimate main-menu idle Attract is a **separate check**: allow the original
idle timer to trigger its demonstration, verify AI/demo behavior, then leave
it normally. If this is not exercised, report idle runtime as NOT_TESTED;
the native idle branch has static and emulation preservation evidence only.
The guard must never globally clear Attract or disable explicit native demos.

One short combined Windowed sequence:

Quick Race → Broker open once → original Debug/Dump → close Broker → Restart
→ verify player control → Broker open once → a NEW complete Dump → F10 → quit.
Repeat essential Broker open/Dump/close in Borderless. Preserve settings and
keep Exclusive deferred. Check live resize, focus/minimize/restore, cursor,
accepted carousels/HUD/preview and ordinary shutdown briefly.

Report two independent verdicts:

- **R-OBS1**: Windowed and Borderless Broker opening, responsiveness,
  actual fresh Dump, close/reopen. Save `Tool opener:` outcomes and traces.
- **R-ATTR1**: guard installation, two Restarts and another race remain normal;
  legitimate idle Attract still works (or explicitly NOT_TESTED).

An R-ATTR1 success cannot close a Broker stall, and a successful Broker/Dump
cannot prove the Restart guard. Old Dump data, a successful build, or the first
ordinary race alone close neither issue. R-CAM1-A3d stays paused until acceptance.
