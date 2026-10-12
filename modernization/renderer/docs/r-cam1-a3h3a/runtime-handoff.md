# R-CAM1-A3h.3a Runtime Handoff

Use the Win32 Release `d3d8.dll` with the exact pristine retail executable. Keep the pilot opt-in:

```ini
[FreeCamera]
Enabled=1
CleanViewPilot=1
CleanViewEnabled=0

[FreeCameraKeys]
ToggleCleanView=H
```

On France1, enter a supported race, activate Freecam, pause through the native game control, then press H once. Confirm the HUD and pause visuals disappear while the world and Freecam continue. Press H again and confirm UI immediately returns. Press F10 while active, resume, Alt+Tab, and exit normally.

The F10 `ui_margins` object should make the result attributable. Check `clean_view_user_requested`, `clean_view_context_valid`, `clean_view_context_reason`, `clean_view_toggle_edge_detected`, `clean_view_initial_armed`, `clean_view_ui_scope_seen`, `clean_view_ui_draw_candidates`, `clean_view_draw_admission_rejections`, `clean_view_last_draw_rejection_reason`, `clean_view_suppressed_draws`, `clean_view_request_disarm_count`, `clean_view_last_disarm_reason`, `clean_view_context_trace_frame`, and `clean_view_context_scheduler_generation`.

PASS requires at least one suppressed verified UI draw, continued suppression on the next verified UI draw, UI restoration on H-off, automatic fail-open/disarm on pause/focus/Freecam/device lifecycle loss, normal world rendering, and clean exit. FAIL if request remains true but the last rejection does not identify the failed gate, any unknown draw is suppressed, or UI stays hidden after the request/context ends. Return the F10 JSONL and results for each check.
