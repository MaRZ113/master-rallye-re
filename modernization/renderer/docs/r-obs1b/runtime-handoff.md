# One combined candidate — minimal smoke test

The separate hook-free Broker/Dump and Restart/idle Attract tests already have
human confirmation. This test qualifies the **new combined DLL**, still PENDING.

1. Close the game and back up the previous accepted d3d8.dll. Preserve your INI.
2. Install the single R-OBS1b + R-ATTR1 package's root d3d8.dll.
3. Launch pristine retail with `[Display] Mode=2`.
4. Open Broker through the updated Observatory; perform a NEW native Debug/Dump.
5. Close Broker, enter Quick Race and verify player control.
6. Restart the same race twice; both remain ordinary player-controlled races.
7. Open Broker again and, if safe in the active state, obtain a fresh Dump.
8. Check Alt+Tab/cursor, F10 and normal quit. Optionally repeat Broker/Dump in Mode=1.

The session must show `legacy_loading_attract_guard.applied=true`; otherwise
the session cannot validate R-ATTR1. Quality metadata must show
`thread_message_hooks_enabled=false` and `display_watch=disabled_by_standard_policy`.
No pre/post renderer window-message records are expected. No diagnostic build
flag is needed. A successful first race alone does not qualify Restart.

Report **Broker opening + fresh Dump** and **two ordinary Restarts** separately,
plus cursor/Alt+Tab/F10. Legitimate idle Attract was independently confirmed;
an optional idle check on the combined candidate is useful, and if omitted
should be recorded as NOT_TESTED for this binary rather than assumed passed.

No automatic deployment was performed. Unknown EXEs receive no Loading guard.
Exclusive remains deferred; do not use this closeout to test camera features.
