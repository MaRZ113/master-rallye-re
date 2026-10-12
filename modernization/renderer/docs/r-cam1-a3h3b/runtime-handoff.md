# R-CAM1-A3h.3b Runtime Pilot

Use the newly built Win32 Release `d3d8.dll` with the supported pristine retail EXE. Keep the pilot opt-in (`CleanViewPilot=1`, `CleanViewEnabled=0`, H toggle).

1. Start a France1 race, activate Freecam with F8, pause normally, and press H.
2. Confirm that HUD/pause UI disappears while the world remains visible and Freecam still moves.
3. Press F10 once while CleanView is active; return that one frame JSONL plus its matching session JSONL.
4. Press H again and confirm UI returns, then exit normally.

The F10 `ui_margins` record is the focused validation. It should show `clean_view_context_valid=true`, `clean_view_scheduler_phase` as `current_inflight` or `current_completed`, matched scheduler generation/Trace frame/thread/device, an active native UI scope, positive `clean_view_suppressed_draws`, and no unknown/non-UI draw suppression. If suppression stays at zero, use `clean_view_context_reason_detail`, `clean_view_first_draw_rejection_reason`, `clean_view_last_draw_rejection_reason`, and the individual `clean_view_reject_*` counters to identify the exact failed predicate. H-off must restore UI immediately. A normal exit is required.

This is one focused pilot, not a multi-capture campaign. Synthetic/build validation does not establish in-game suppression; runtime status remains pending the pilot.
