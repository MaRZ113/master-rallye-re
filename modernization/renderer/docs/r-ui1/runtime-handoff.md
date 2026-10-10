# R-UI1-D2 Runtime Validation

Use the current Win32 Release proxy build and verify its SHA256 against the validation record before copying it beside the game. Set `[Widescreen] InterfaceMode=2` (`PreserveMargins`), keep the accepted Windowed or Borderless mode unchanged, and use 1920×1080. Keep `[Trace] Enabled=1` and `FrameSummaries=1`. Do not enable a carousel-specific override; none is implemented.

The purpose of this short run is to validate repeated F10 capture re-arming and obtain comparable Race Select / Vehicle Select draw evidence. Do not restart Master Rallye or recreate the D3D device between captures unless the game becomes unusable. F10 uses the existing Trace capture. The UI session events and matching Trace frame records share `capture_id` in the form `d<device>-f<Trace frame>`; each F10 capture has its own fresh UI budgets and closes at its matching Present. Use each row's `trace_frame` for frame joins. The legacy packet `first_frame` and `frame` fields describe UI anchor lifetime bookkeeping.

## Capture A — Vehicle Select with visible misalignment

Open Vehicle Select, scroll until the yellow frame appears over an empty or visibly misaligned slot, then stop moving and press F10 once. Let the capture close at Present. Record the capture ID and label it `A-vehicle-bug`.

Expect relevant `ui_packet_lifetime` rows with nested `draw_observations`, `ui_render_local` rows when WORLD evidence is readable, and a `ui_diagnostic_capture_end` summary with fresh budget counts. Adjusted and unadjusted candidate rows are both useful; either class may be absent if that screen did not submit it during the capture.

## Capture B — Vehicle Select in a visually correct position

Without restarting or resetting the device, move to a position where the carousel appears correct, stop, and press F10 once more. Label it `B-vehicle-correct`. Confirm that the capture ID differs from A and the new end summary reports records from its own budget. This is the direct repeated-F10 regression check.

## Capture C — Race Select with visible misalignment

Navigate to Race Select, stop on a visibly misaligned highlight, and press F10 once. Label it `C-race-bug`. Do not restart between B and C. This provides a cross-carousel comparison under the same renderer session.

## Files and interpretation

Keep the matching session JSONL and the three Trace frame JSONL files, with the labels above. Optional screenshots help tie the capture to the visible state. Do not add proprietary runtime captures to the repository.

For each `ui_diagnostic_capture_end`, check:

- `capture_id`, `device_id`, start/end boundary, and `reason`;
- `capture_records_emitted` and `capture_record_budget_limit`;
- `packet_consumers_seen`, `packet_consumers_without_relevant_draw`, and `packets_with_draws`;
- adjusted and unadjusted promoted candidates;
- `candidate_capacity_rejections`, `candidate_evictions`, draw drops, record drops, and `coverage_status`.

Join packet rows to their nested draw observations within the same capture ID. Compare entity/packet/point/content-storage/mode, UI epoch, anchor provenance, packet XY, caller RVA/FVF, and native/effective WORLD XY. Compare packet addresses across captures only when the validated UI epoch and lifetime context show they represent the same object; raw address equality by itself does not establish identity. Shared content storage is investigative evidence, not proof of widget membership.

If a capture has no eligible draws, use its end summary to distinguish a missing valid consumer, consumers without a relevant draw, and bounded/log loss. A frame with no packet rows is not proof that the game did not draw a card. `current_screen_status`, `carousel_owner_status`, and selection-state evidence should remain `not_proven` until the captures or source establish the card/highlight relationship.

Capture A/B is a diagnostic lifecycle pass when B has a new ID and fresh budget with relevant evidence. Capture C adds the race-select comparison. Visual acceptance still requires both carousel families to remain aligned while moving in both directions, with the selection frame, thumbnail, preview, list, and game selection in agreement. Do not infer selection-index corruption from an empty highlighted slot alone.

Afterward, briefly check PreserveMargins HUD/menu stability, then Centered4x3 and Stock if time permits. These are regression observations, not required to infer carousel ownership. Preserve camera/FOV, foliage, borderless/windowed, AF/MSAA, and other existing renderer behavior.
